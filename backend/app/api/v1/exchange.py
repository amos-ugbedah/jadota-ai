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

Security model
--------------
* Raw API keys, secrets, and passphrases are never returned to the client.
  Only the first N characters of the API key are exposed, masked.
* The plaintext secret is never written to logs. Bitget's own error
  messages are logged as-is — they do not contain the credential.
* On disconnect, credentials are hard-deleted from the database, so a
  user who revokes access does not leave encrypted secrets lying around.
* The `/test` endpoint re-decrypts stored credentials and re-pings Bitget.
  It is safe to expose: Bitget rejects the call if the user has rotated
  or deleted the key on their side.
"""

import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ...api.dependencies import get_current_user
from ...core.config import settings
from ...core.database import get_db
from ...models.exchange_credentials import ExchangeCredentials
from ...models.user import User
from ...schemas.exchange import (
    BitgetConnectRequest,
    ExchangeConnectResponse,
    ExchangeDisconnectResponse,
    ExchangeStatusResponse,
)
from ...services.bitget_client import BitgetClient, BitgetError
from ...services.encryption import decrypt, encrypt, mask

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/exchange", tags=["Exchange"])

# How many leading characters of the API key to leave visible when masking
_MASK_VISIBLE_CHARS = 6

# Truncation limit for error strings persisted to the DB
_MAX_ERROR_CHARS = 500

# Canonical exchange identifier — used in the DB row and route prefixes
_EXCHANGE_ID = "bitget"


# ============================================
# Internal helpers
# ============================================
def _load_credential(db: Session, user_id: str) -> Optional[ExchangeCredentials]:
    """Fetch the user's Bitget credential row, or None if not connected."""
    return (
        db.query(ExchangeCredentials)
        .filter(
            ExchangeCredentials.user_id == user_id,
            ExchangeCredentials.exchange == _EXCHANGE_ID,
        )
        .first()
    )


def _to_status(cred: Optional[ExchangeCredentials]) -> ExchangeStatusResponse:
    """Convert a credential row (or None) into the public status shape."""
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


async def _verify_with_bitget(
    api_key: str,
    api_secret: str,
    passphrase: str,
) -> None:
    """
    Ping Bitget with the given credentials.

    Raises:
        HTTPException(400): Bitget explicitly rejected the credentials.
        HTTPException(502): Bitget was unreachable (network, timeout, DNS).

    The Bitget error code and message are logged but the raw API key is not.
    """
    try:
        async with BitgetClient(
            api_key=api_key,
            api_secret=api_secret,
            passphrase=passphrase,
            testnet=settings.bitget_testnet,
        ) as client:
            await client.get_account_info()
    except BitgetError as exc:
        # Bitget's `msg` is a user-safe, upstream-provided string.
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
        "along with non-sensitive metadata (masked key, permissions, "
        "last-used timestamp, last error). Never returns the raw "
        "credentials, even to the account owner."
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
    status_code=status.HTTP_200_OK,
    summary="Connect a Bitget account",
    description=(
        "Verify the supplied API key, secret, and passphrase against "
        "Bitget, then persist them encrypted. Calling this when a "
        "connection already exists will replace the stored credentials "
        "(upsert). The verification happens *before* any DB write, so a "
        "failed attempt leaves existing credentials untouched."
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
    # 1. Verify live with Bitget *first* — never persist unverified keys
    await _verify_with_bitget(body.api_key, body.api_secret, body.passphrase)

    # 2. Upsert the credential row
    cred = _load_credential(db, current_user.id)
    if cred is None:
        cred = ExchangeCredentials(
            user_id=current_user.id,
            exchange=_EXCHANGE_ID,
        )
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
        "still work. Useful when a user suspects their API key was "
        "rotated, revoked, or their IP whitelist changed. On failure the "
        "reason is saved and visible via `/status`."
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

    api_key = decrypt(cred.api_key_encrypted)
    api_secret = decrypt(cred.api_secret_encrypted)
    passphrase = decrypt(cred.passphrase_encrypted)

    if not (api_key and api_secret and passphrase):
        # Reaches here only if ENCRYPTION_KEY changed on the server.
        logger.error(f"bitget.decrypt.failed user={current_user.id}")
        cred.last_error = "Decryption failed — server encryption key changed."
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "Stored credentials cannot be decrypted. Please disconnect "
                "and reconnect your Bitget account."
            ),
        )

    try:
        await _verify_with_bitget(api_key, api_secret, passphrase)
    except HTTPException as exc:
        # Persist the failure reason for the next /status read, then re-raise
        # so the caller receives the correct HTTP status.
        cred.last_error = str(exc.detail)[:_MAX_ERROR_CHARS]
        db.commit()
        raise

    # Success path — update metadata and return
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
        "This action is idempotent: calling it when no connection exists "
        "still returns success, so retries are safe."
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