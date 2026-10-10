"""
Exchange integration API — Bitget account connection management.

This module is the *only* place in the codebase that ever sees a user's
plaintext Bitget credentials. It hands them to Bitget for verification
and immediately stores them encrypted (Fernet, see services/encryption.py)
before returning. The raw values never leave the server.

Endpoints
---------
    GET     /exchange/bitget/status       Connection status + metadata
    POST    /exchange/bitget/connect      Verify and store credentials
    POST    /exchange/bitget/test         Re-verify stored credentials
    DELETE  /exchange/bitget/disconnect   Forget credentials
    GET     /exchange/bitget/balance      Live spot wallet balances

Security model
--------------
* Raw API keys, secrets, and passphrases are never returned to the client.
* The plaintext secret is never written to logs.
* On disconnect, credentials are hard-deleted from the database.
"""

import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ...api.dependencies import get_current_user
from ...core.config import settings
from ...core.database import get_db
from ...models.exchange_credentials import ExchangeCredentials
from ...models.user import User
from ...schemas.exchange import (
    BitgetConnectRequest,
    ExchangeBalanceItem,
    ExchangeBalanceResponse,
    ExchangeConnectResponse,
    ExchangeDisconnectResponse,
    ExchangeStatusResponse,
)
from ...services.bitget_client import BitgetClient, BitgetError
from ...services.encryption import decrypt, encrypt, mask

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/exchange", tags=["Exchange"])

_MASK_VISIBLE_CHARS = 6
_MAX_ERROR_CHARS = 500
_EXCHANGE_ID = "bitget"


# ============================================
# Internal helpers
# ============================================
def _load_credential(db: Session, user_id: str) -> Optional[ExchangeCredentials]:
    return (
        db.query(ExchangeCredentials)
        .filter(
            ExchangeCredentials.user_id == user_id,
            ExchangeCredentials.exchange == _EXCHANGE_ID,
        )
        .first()
    )


def _to_status(cred: Optional[ExchangeCredentials]) -> ExchangeStatusResponse:
    if cred is None:
        return ExchangeStatusResponse(
            connected=False,
            exchange=_EXCHANGE_ID,
            testnet=settings.bitget_testnet,
        )
    return ExchangeStatusResponse(
        connected=True,
        exchange=cred.exchange,
        api_key_masked=cred.api_key_masked,
        permissions=cred.permissions,
        ip_whitelist=cred.ip_whitelist,
        is_active=bool(cred.is_active),
        testnet=settings.bitget_testnet,
        last_used_at=cred.last_used_at,
        last_error=cred.last_error,
        connected_at=cred.created_at,
    )


def _decrypt_credential(cred: ExchangeCredentials):
    """Returns (api_key, api_secret, passphrase) or raises HTTPException 500."""
    api_key = decrypt(cred.api_key_encrypted)
    api_secret = decrypt(cred.api_secret_encrypted)
    passphrase = decrypt(cred.passphrase_encrypted)
    if not (api_key and api_secret and passphrase):
        logger.error(f"bitget.decrypt.failed user={cred.user_id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "Stored credentials cannot be decrypted. Please disconnect "
                "and reconnect your Bitget account."
            ),
        )
    return api_key, api_secret, passphrase


async def _verify_with_bitget(api_key: str, api_secret: str, passphrase: str) -> None:
    """Ping Bitget with the given credentials. Raises HTTPException on failure."""
    try:
        async with BitgetClient(
            api_key=api_key,
            api_secret=api_secret,
            passphrase=passphrase,
            testnet=settings.bitget_testnet,
        ) as client:
            await client.get_account_info()
    except BitgetError as exc:
        logger.info(
            f"bitget.verify.rejected code={exc.code} http={exc.http_status} "
            f"msg={exc.msg}"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Bitget rejected these credentials: {exc.msg}",
        )
    except Exception as exc:  # noqa: BLE001 — network, timeout, DNS
        logger.exception(f"bitget.verify.unreachable error={type(exc).__name__}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Could not reach Bitget. Please try again in a moment.",
        )


# ============================================
# GET /exchange/bitget/status
# ============================================
@router.get(
    "/bitget/status",
    response_model=ExchangeStatusResponse,
    summary="Bitget connection status",
    description=(
        "Return whether the current user has a Bitget account connected, "
        "along with non-sensitive metadata. Never returns raw credentials."
    ),
)
async def get_bitget_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ExchangeStatusResponse:
    cred = _load_credential(db, current_user.id)
    return _to_status(cred)


# ============================================
# POST /exchange/bitget/connect
# ============================================
@router.post(
    "/bitget/connect",
    response_model=ExchangeConnectResponse,
    summary="Connect a Bitget account",
    description=(
        "Verify the supplied API key, secret, and passphrase against Bitget, "
        "then persist them encrypted. Verification happens *before* any DB "
        "write, so a failed attempt leaves existing credentials untouched."
    ),
    responses={
        400: {"description": "Bitget rejected the credentials"},
        502: {"description": "Bitget was unreachable"},
    },
)
async def connect_bitget(
    body: BitgetConnectRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ExchangeConnectResponse:
    await _verify_with_bitget(body.api_key, body.api_secret, body.passphrase)

    cred = _load_credential(db, current_user.id)
    if cred is None:
        cred = ExchangeCredentials(user_id=current_user.id, exchange=_EXCHANGE_ID)
        db.add(cred)

    cred.api_key_encrypted = encrypt(body.api_key)
    cred.api_secret_encrypted = encrypt(body.api_secret)
    cred.passphrase_encrypted = encrypt(body.passphrase)
    cred.api_key_masked = mask(body.api_key, visible=_MASK_VISIBLE_CHARS)
    cred.is_active = True
    cred.last_error = None
    cred.last_used_at = datetime.utcnow()
    db.commit()
    db.refresh(cred)

    logger.info(
        f"bitget.connected user={current_user.id} "
        f"key={cred.api_key_masked} testnet={settings.bitget_testnet}"
    )

    return ExchangeConnectResponse(
        success=True,
        message="Bitget account connected and verified.",
        status=_to_status(cred),
    )


# ============================================
# POST /exchange/bitget/test
# ============================================
@router.post(
    "/bitget/test",
    response_model=ExchangeConnectResponse,
    summary="Re-verify Bitget credentials",
    description=(
        "Decrypt the stored credentials and ping Bitget to confirm they "
        "still work. On failure the reason is saved and visible via /status."
    ),
    responses={
        404: {"description": "No Bitget account connected"},
        400: {"description": "Bitget rejected the stored credentials"},
        502: {"description": "Bitget was unreachable"},
    },
)
async def test_bitget(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ExchangeConnectResponse:
    cred = _load_credential(db, current_user.id)
    if cred is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No Bitget account connected.",
        )

    api_key, api_secret, passphrase = _decrypt_credential(cred)

    try:
        await _verify_with_bitget(api_key, api_secret, passphrase)
    except HTTPException as exc:
        cred.last_error = str(exc.detail)[:_MAX_ERROR_CHARS]
        db.commit()
        raise

    cred.last_used_at = datetime.utcnow()
    cred.last_error = None
    db.commit()

    logger.info(f"bitget.verified user={current_user.id}")

    return ExchangeConnectResponse(
        success=True,
        message="Bitget credentials verified.",
        status=_to_status(cred),
    )


# ============================================
# DELETE /exchange/bitget/disconnect
# ============================================
@router.delete(
    "/bitget/disconnect",
    response_model=ExchangeDisconnectResponse,
    summary="Disconnect Bitget",
    description=(
        "Hard-delete the stored Bitget credentials for the current user. "
        "Idempotent: calling it when no connection exists returns success."
    ),
)
async def disconnect_bitget(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ExchangeDisconnectResponse:
    deleted = (
        db.query(ExchangeCredentials)
        .filter(
            ExchangeCredentials.user_id == current_user.id,
            ExchangeCredentials.exchange == _EXCHANGE_ID,
        )
        .delete(synchronize_session=False)
    )
    db.commit()

    if deleted:
        logger.info(f"bitget.disconnected user={current_user.id}")
        return ExchangeDisconnectResponse(
            success=True,
            message="Bitget account disconnected.",
        )

    return ExchangeDisconnectResponse(
        success=True,
        message="No Bitget account was connected.",
    )


# ============================================
# GET /exchange/bitget/balance  🔥 Task #4c
# ============================================
@router.get(
    "/bitget/balance",
    response_model=ExchangeBalanceResponse,
    summary="Live spot wallet balance",
    description=(
        "Fetch the user's live Bitget spot wallet balances. Requires a "
        "connected account. Optional `asset` query param filters to a "
        "single coin (e.g. `?asset=USDT`)."
    ),
    responses={
        404: {"description": "No Bitget account connected"},
        502: {"description": "Bitget was unreachable or rejected the request"},
    },
)
async def get_bitget_balance(
    asset: Optional[str] = Query(None, description="Filter to one asset, e.g. USDT"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ExchangeBalanceResponse:
    cred = _load_credential(db, current_user.id)
    if cred is None or not cred.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active Bitget account connected.",
        )

    api_key, api_secret, passphrase = _decrypt_credential(cred)

    try:
        async with BitgetClient(
            api_key=api_key,
            api_secret=api_secret,
            passphrase=passphrase,
            testnet=settings.bitget_testnet,
        ) as client:
            rows = await client.get_spot_balances(coin=asset)
    except BitgetError as exc:
        logger.info(
            f"bitget.balance.rejected user={current_user.id} "
            f"code={exc.code} msg={exc.msg}"
        )
        cred.last_error = f"{exc.code}: {exc.msg}"[:_MAX_ERROR_CHARS]
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Bitget rejected the request: {exc.msg}",
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception(f"bitget.balance.unreachable user={current_user.id}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Could not reach Bitget: {type(exc).__name__}",
        )

    # Record successful use
    cred.last_used_at = datetime.utcnow()
    cred.last_error = None
    db.commit()

    # Only return non-zero balances (Bitget returns all coins, most are 0)
    non_zero = [r for r in rows if r["total"] > 0]
    balances = [ExchangeBalanceItem(**r) for r in non_zero]

    # Sum USDT value if USDT is present — cheap sanity number for the UI
    total_usdt = None
    for b in balances:
        if b.asset.upper() == "USDT":
            total_usdt = b.total
            break

    return ExchangeBalanceResponse(
        success=True,
        exchange=_EXCHANGE_ID,
        testnet=settings.bitget_testnet,
        balances=balances,
        total_usdt_value=total_usdt,
    )