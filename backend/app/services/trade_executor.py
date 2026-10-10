"""
Trade executor — places Bitget orders and creates local position rows.

Used by:
    - main.py::auto_trade endpoint (manual trigger)
    - main.py::place_manual_order endpoint (Trading panel)
    - services/auto_trader.py (background loop)
"""

import logging
import uuid
from datetime import datetime

from fastapi import HTTPException, status

from ..core.config import settings
from ..core.database import SessionLocal
from ..models.exchange_credentials import ExchangeCredentials
from .bitget_client import BitgetClient, BitgetError
from .encryption import decrypt
from .market_data_service import market_data_service
from .ai_trading_service import ai_trading_service
from .position_store import (
    list_positions,
    create_position,
    update_position,
)
from .telegram_service import telegram_service

logger = logging.getLogger(__name__)

_MAX_ERROR_CHARS = 500


async def place_bitget_order(
    cred: ExchangeCredentials,
    db,
    symbol: str,
    side: str,
    trade_amount: float,
    base_size: float,
) -> str:
    """
    Place a spot market order on Bitget for a connected user.

    Side semantics (Bitget v2 spot):
      - BUY / ADD → order side "buy",  size is the QUOTE amount (USDT to spend)
      - SELL      → order side "sell", size is the BASE amount (coins to sell)

    🔥 IMPORTANT: Bitget does not always return an `orderId` even for
    successful orders. When that happens, we log a warning and fall back
    to using the `client_oid` (our own idempotency token) as the tracking
    identifier. This prevents us from raising a fake 502 for an order
    that actually went through.

    Raises HTTPException(502) ONLY if Bitget actually rejected the order
    or is unreachable. If Bitget said "success", this returns normally.
    """
    api_key = decrypt(cred.api_key_encrypted)
    api_secret = decrypt(cred.api_secret_encrypted)
    passphrase = decrypt(cred.passphrase_encrypted)

    if not (api_key and api_secret and passphrase):
        logger.error(f"bitget.decrypt.failed user={cred.user_id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "Stored Bitget credentials cannot be decrypted. "
                "Please disconnect and reconnect your Bitget account."
            ),
        )

    bitget_symbol = symbol.replace("/", "")
    order_side = "buy" if side in ("BUY", "ADD") else "sell"

    if order_side == "buy":
        order_size = f"{trade_amount:.8f}"
    else:
        order_size = f"{base_size:.8f}"

    client_oid = str(uuid.uuid4()).replace("-", "")[:30]

    # --- Call Bitget ---
    result: dict = {}
    try:
        async with BitgetClient(
            api_key=api_key,
            api_secret=api_secret,
            passphrase=passphrase,
            testnet=settings.bitget_testnet,
        ) as client:
            result = await client.place_spot_market_order(
                symbol=bitget_symbol,
                side=order_side,
                size=order_size,
                client_oid=client_oid,
            )
    except BitgetError as exc:
        # Bitget EXPLICITLY rejected the order. This is a genuine failure.
        logger.warning(
            f"bitget.order.rejected user={cred.user_id} "
            f"symbol={bitget_symbol} side={order_side} "
            f"code={exc.code} msg={exc.msg}"
        )
        cred.last_error = f"{exc.code}: {exc.msg}"[:_MAX_ERROR_CHARS]
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Bitget rejected the order: {exc.msg}",
        )
    except Exception as exc:
        logger.exception(
            f"bitget.order.unreachable user={cred.user_id} "
            f"symbol={bitget_symbol} side={order_side}"
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Could not reach Bitget: {type(exc).__name__}",
        )

    # --- Extract order id (defensive) ---
    # 🔥 Fix: never raise on missing orderId. Bitget accepts market orders
    # without always echoing an id back. Fall back to client_oid so we still
    # have a stable identifier for this order.
    order_id = (
        (result or {}).get("orderId")
        or (result or {}).get("order_id")
        or (result or {}).get("order_id_str")
    )

    if not order_id:
        logger.warning(
            f"bitget.order.no_id_returned user={cred.user_id} "
            f"symbol={bitget_symbol} side={order_side} "
            f"client_oid={client_oid} raw_result={result}"
        )
        # Use client_oid as the tracking id. Reconciliation can resolve the
        # actual Bitget order id later if needed.
        order_id = f"client:{client_oid}"

    # --- Record successful use ---
    cred.last_used_at = datetime.utcnow()
    cred.last_error = None
    db.commit()

    logger.info(
        f"bitget.order.placed user={cred.user_id} "
        f"symbol={bitget_symbol} side={order_side} size={order_size} "
        f"order_id={order_id} raw_result={result}"
    )
    return order_id


async def execute_ai_trade(
    symbol: str,
    side: str,
    signal: dict,
    user_id: str = None,
):
    """
    Execute a trade based on an AI signal. Writes to the `positions` table.

    If the user has an active Bitget connection, the order is placed on
    Bitget BEFORE any DB write. If Bitget rejects, no position is created.
    Otherwise, a demo-only position is written (source="demo").
    """
    from ..models.ai_settings import AISettings

    base_amount = 25.0
    stop_loss_pct = 0.02
    take_profit_pct = 0.04

    db = SessionLocal()
    try:
        if user_id:
            user_settings = (
                db.query(AISettings).filter(AISettings.user_id == user_id).first()
            )
            if user_settings:
                base_amount = user_settings.trade_amount or 25.0
                stop_loss_pct = (user_settings.stop_loss_percent or 2.0) / 100
                take_profit_pct = (user_settings.take_profit_percent or 4.0) / 100

        current_price = market_data_service.get_price(symbol)
        if current_price == 0:
            current_price = 45000.00

        confidence = signal.get("confidence", 50)
        trade_amount = ai_trading_service.calculate_trade_amount(base_amount, confidence)
        size = trade_amount / current_price

        cred = None
        if user_id:
            cred = (
                db.query(ExchangeCredentials)
                .filter(
                    ExchangeCredentials.user_id == user_id,
                    ExchangeCredentials.exchange == "bitget",
                    ExchangeCredentials.is_active == True,  # noqa: E712
                )
                .first()
            )
        is_live = cred is not None

        bitget_order_id = None
        if is_live:
            bitget_order_id = await place_bitget_order(
                cred=cred,
                db=db,
                symbol=symbol,
                side=side,
                trade_amount=trade_amount,
                base_size=size,
            )

        source = "bitget" if is_live else "demo"

        # ADD — merge into existing OPEN position
        if side == "ADD":
            open_positions = list_positions(db, user_id=user_id, status="OPEN")
            existing = next((p for p in open_positions if p["symbol"] == symbol), None)

            if existing:
                old_size = float(existing.get("size") or 0)
                old_price = float(existing.get("entryPrice") or 0)
                new_size = old_size + size
                if new_size > 0:
                    avg_price = (old_size * old_price + size * current_price) / new_size
                else:
                    avg_price = current_price

                updated = update_position(db, existing["id"], {
                    "size": round(new_size, 6),
                    "entryPrice": round(avg_price, 2),
                    "currentPrice": current_price,
                    "tradeAmount": (existing.get("tradeAmount") or 0) + trade_amount,
                    "stopLoss": round(avg_price * (1 - stop_loss_pct), 2),
                    "takeProfit": round(avg_price * (1 + take_profit_pct), 2),
                    "bitgetOrderId": bitget_order_id,
                    "source": source,
                })

                logger.info(
                    f"💰 DCA ADD: {symbol} | source={source} | "
                    f"Old {old_size:.6f}@{old_price:.2f} + "
                    f"New {size:.6f}@{current_price:.2f} = "
                    f"Avg {new_size:.6f}@{avg_price:.2f}"
                    + (f" | bitget_order={bitget_order_id}" if bitget_order_id else "")
                )
                await telegram_service.send_trade_alert(updated, "ADD")
                return updated

            side = "BUY"

        position = create_position(db, {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "symbol": symbol,
            "side": side,
            "size": round(size, 6),
            "entryPrice": current_price,
            "currentPrice": current_price,
            "unrealizedPnl": 0.00,
            "realizedPnl": 0.00,
            "tradeAmount": trade_amount,
            "baseAmount": base_amount,
            "stopLoss": round(current_price * (1 - stop_loss_pct), 2),
            "takeProfit": round(current_price * (1 + take_profit_pct), 2),
            "stopLossPct": stop_loss_pct,
            "takeProfitPct": take_profit_pct,
            "openedAt": datetime.utcnow().isoformat(),
            "status": "OPEN",
            "aiConfidence": confidence,
            "aiReasoning": signal.get("reasoning", "AI signal"),
            "bitgetOrderId": bitget_order_id,
            "source": source,
        })

        logger.info(
            f"🤖 AI Trade: {side} {symbol} | source={source} | "
            f"Base ${base_amount} × {confidence}% = ${trade_amount} | "
            f"Size {size:.6f}"
            + (f" | bitget_order={bitget_order_id}" if bitget_order_id else "")
        )

        await telegram_service.send_trade_alert(position, "OPEN")
        return position
    finally:
        db.close()