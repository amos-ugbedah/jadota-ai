"""
Payment service — creates pending payments and verifies USDT transfers
on-chain via NodeReal (recommended) or BscScan/Etherscan APIs.

API keys are OPTIONAL. If missing, verification returns None and the
payment falls back to admin manual approval.
"""

import logging
import httpx
from datetime import datetime, timedelta
from typing import Optional

from ..core.config import settings

logger = logging.getLogger(__name__)

# USDT contract addresses
USDT_BSC_CONTRACT = "0x55d398326f99059fF775485246999027B3197955"   # 18 decimals
USDT_ETH_CONTRACT = "0xdAC17F958D2ee523a2206206994597C13D831ec7"   # 6 decimals

# Plan pricing
PLAN_PRICING = {
    "basic": 0.0,
    "pro": 29.99,
    "enterprise": 99.99,
}

# Payment window
PAYMENT_WINDOW_MINUTES = 30


def get_plan_price(plan: str) -> float:
    return PLAN_PRICING.get(plan.lower(), 0.0)


def get_receiving_wallet(network: str = "BEP20") -> str:
    """Return the configured wallet address for a given network."""
    return settings.jadota_wallet_address or "0x0000000000000000000000000000000000000000"


async def _query_nodereal(
    wallet_address: str,
    expected_amount: float,
    created_at: datetime,
    contract: str,
    decimals: int,
    api_key: str,
) -> Optional[str]:
    """
    Query NodeReal's BscScan-compatible API for USDT token transfers.
    Returns matching tx_hash or None.
    """
    url = f"https://api.nodereal.io/v1/{api_key}/api"
    params = {
        "module": "account",
        "action": "tokentx",
        "address": wallet_address,
        "contractaddress": contract,
        "startblock": 0,
        "endblock": 99999999,
        "sort": "desc",
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            r = await client.get(url, params=params)
            data = r.json()
    except Exception as e:
        logger.error(f"NodeReal API error: {e}")
        return None

    if data.get("status") != "1" or not isinstance(data.get("result"), list):
        logger.warning(f"NodeReal returned no usable data: {data.get('message')}")
        return None

    return _match_transaction(
        transactions=data["result"],
        wallet_address=wallet_address,
        expected_amount=expected_amount,
        created_at=created_at,
        decimals=decimals,
    )


async def _query_bscscan_family(
    wallet_address: str,
    expected_amount: float,
    created_at: datetime,
    contract: str,
    decimals: int,
    base_url: str,
    api_key: str,
) -> Optional[str]:
    """
    Query BscScan/Etherscan-style API. Used as a fallback.
    """
    params = {
        "module": "account",
        "action": "tokentx",
        "address": wallet_address,
        "contractaddress": contract,
        "startblock": 0,
        "endblock": 99999999,
        "sort": "desc",
        "apikey": api_key,
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            r = await client.get(base_url, params=params)
            data = r.json()
    except Exception as e:
        logger.error(f"Blockchain API error ({base_url}): {e}")
        return None

    if data.get("status") != "1" or not isinstance(data.get("result"), list):
        logger.warning(f"Blockchain API returned no results: {data.get('message')}")
        return None

    return _match_transaction(
        transactions=data["result"],
        wallet_address=wallet_address,
        expected_amount=expected_amount,
        created_at=created_at,
        decimals=decimals,
    )


def _match_transaction(
    transactions: list,
    wallet_address: str,
    expected_amount: float,
    created_at: datetime,
    decimals: int,
) -> Optional[str]:
    """
    Find a tx in the list that matches: sent to our address, correct
    amount (±1%), within the time window (payment_created ±5 min).
    """
    lower_wallet = wallet_address.lower()
    window_start = created_at - timedelta(minutes=5)
    window_end = datetime.utcnow() + timedelta(minutes=5)

    for tx in transactions:
        try:
            to_addr = (tx.get("to") or "").lower()
            if to_addr != lower_wallet:
                continue

            raw_value = int(tx.get("value", 0))
            amount = raw_value / (10 ** decimals)

            tolerance = max(0.01, expected_amount * 0.01)
            if abs(amount - expected_amount) > tolerance:
                continue

            tx_time = datetime.utcfromtimestamp(int(tx.get("timeStamp", 0)))
            if not (window_start <= tx_time <= window_end):
                continue

            logger.info(f"✅ Matching payment found: {tx['hash']} = {amount} USDT")
            return tx["hash"]

        except Exception as e:
            logger.debug(f"Skipping tx {tx.get('hash')}: {e}")
            continue

    logger.info(f"No matching payment found for ${expected_amount}")
    return None


async def verify_usdt_payment(
    wallet_address: str,
    expected_amount: float,
    created_at: datetime,
    network: str = "BEP20",
) -> Optional[str]:
    """
    Verify a USDT payment on-chain.

    Priority:
      1. NodeReal API (for BEP20) — recommended
      2. BscScan API (for BEP20) — deprecated but still works in some regions
      3. Etherscan API (for ERC20)

    Returns tx_hash if match found, else None. If no API key is set,
    returns None immediately — caller should fall back to admin approval.
    """
    is_bep20 = network.upper() == "BEP20"
    contract = USDT_BSC_CONTRACT if is_bep20 else USDT_ETH_CONTRACT
    decimals = 18 if is_bep20 else 6

    # ============================================
    # BEP20 — try NodeReal, then BscScan
    # ============================================
    if is_bep20:
        nodereal_key = getattr(settings, "nodereal_api_key", None)
        if nodereal_key:
            logger.info("Verifying via NodeReal…")
            tx = await _query_nodereal(
                wallet_address=wallet_address,
                expected_amount=expected_amount,
                created_at=created_at,
                contract=contract,
                decimals=decimals,
                api_key=nodereal_key,
            )
            if tx:
                return tx

        bscscan_key = getattr(settings, "bscscan_api_key", None)
        if bscscan_key:
            logger.info("Verifying via BscScan (fallback)…")
            tx = await _query_bscscan_family(
                wallet_address=wallet_address,
                expected_amount=expected_amount,
                created_at=created_at,
                contract=contract,
                decimals=decimals,
                base_url="https://api.bscscan.com/api",
                api_key=bscscan_key,
            )
            if tx:
                return tx

        logger.info("No BEP20 API key configured — skipping auto-verification")
        return None

    # ============================================
    # ERC20 — use Etherscan
    # ============================================
    etherscan_key = getattr(settings, "etherscan_api_key", None)
    if etherscan_key:
        logger.info("Verifying via Etherscan…")
        return await _query_bscscan_family(
            wallet_address=wallet_address,
            expected_amount=expected_amount,
            created_at=created_at,
            contract=contract,
            decimals=decimals,
            base_url="https://api.etherscan.io/api",
            api_key=etherscan_key,
        )

    logger.info("No ERC20 API key configured — skipping auto-verification")
    return None


def activate_subscription(user, plan: str, months: float) -> None:
    """
    Extend or set the user's subscription.
    If the user already has an active subscription, extends from current expiry.
    """
    now = datetime.utcnow()

    start = now
    if user.subscription_expires_at and user.subscription_expires_at > now:
        start = user.subscription_expires_at

    user.subscription_plan = plan.upper()
    user.subscription_expires_at = start + timedelta(days=int(30 * months))
    user.is_subscription_active = True