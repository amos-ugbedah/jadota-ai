"""
Reconciliation Service — keeps `positions` in sync with Bitget.

Runs every RECONCILE_INTERVAL_SECONDS. For each user with an active Bitget
connection and any OPEN positions marked `source="bitget"`, it fetches the
corresponding order from Bitget and reconciles:

    Bitget status "filled"            → position stays OPEN, entry price synced
    Bitget status "live"/"partial"    → position stays OPEN
    Bitget status "cancelled" /       → position CLOSED locally with
        "rejected" / "expired"          close_reason = "RECONCILED_CANCELLED"
    Bitget unreachable or error       → reconciliation_status = "error"

Design principles
-----------------
* Never creates new positions from Bitget data. Conservative by design —
  a missing position row is preferred to an invented one.
* Never modifies demo positions (source != "bitget").
* Never touches a position whose user has no active Bitget connection —
  those positions are effectively frozen until the user reconnects.
* Failures are per-position, not per-user. One bad order doesn't abort
  the whole pass.
"""

import asyncio
import logging
from datetime import datetime
from typing import Optional

from ..core.config import settings
from ..core.database import SessionLocal
from ..models.exchange_credentials import ExchangeCredentials
from ..models.position import Position
from .bitget_client import BitgetClient, BitgetError
from .encryption import decrypt
from .telegram_service import telegram_service

logger = logging.getLogger(__name__)

# How often the reconciliation loop runs (in seconds)
RECONCILE_INTERVAL_SECONDS = 60

# Bitget statuses that mean "the order is still active on the exchange"
_LIVE_STATUSES = {"live", "new", "partial-fill", "partially_filled"}

# Bitget statuses that mean "the order never executed, close the DB row"
_CANCELLED_STATUSES = {"cancelled", "canceled", "rejected", "expired"}

# Bitget statuses that mean "the order fully filled"
_FILLED_STATUSES = {"filled"}


class ReconciliationService:
    """Background service that reconciles positions against Bitget."""

    def __init__(self, interval_seconds: int = RECONCILE_INTERVAL_SECONDS):
        self.interval_seconds = interval_seconds
        self.is_running = False
        self._task: Optional[asyncio.Task] = None

    async def start(self) -> None:
        if self.is_running:
            return
        self.is_running = True
        self._task = asyncio.create_task(self._loop())
        logger.info(
            f"✅ Reconciliation service started "
            f"(interval={self.interval_seconds}s)"
        )

    async def stop(self) -> None:
        self.is_running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        logger.info("Reconciliation service stopped")

    async def _loop(self) -> None:
        # Small initial delay so startup isn't flooded with API calls
        await asyncio.sleep(5)
        while self.is_running:
            try:
                summary = await self.run_once()
                if summary["checked"]:
                    logger.info(
                        f"reconcile.pass users={summary['users']} "
                        f"checked={summary['checked']} "
                        f"synced={summary['synced']} "
                        f"orphaned={summary['orphaned']} "
                        f"errors={summary['errors']}"
                    )
            except Exception as e:
                logger.exception(f"reconcile.loop.error: {e}")
            await asyncio.sleep(self.interval_seconds)

    async def run_once(self) -> dict:
        """
        Run one reconciliation pass. Also used by the admin endpoint
        `POST /api/v1/admin/reconcile` for manual triggers.

        Returns a small summary dict.
        """
        summary = {"users": 0, "checked": 0, "synced": 0, "orphaned": 0, "errors": 0}

        db = SessionLocal()
        try:
            creds = (
                db.query(ExchangeCredentials)
                .filter(
                    ExchangeCredentials.exchange == "bitget",
                    ExchangeCredentials.is_active == True,  # noqa: E712
                )
                .all()
            )
            summary["users"] = len(creds)

            for cred in creds:
                try:
                    counts = await self._reconcile_user(db, cred)
                    summary["checked"] += counts["checked"]
                    summary["synced"] += counts["synced"]
                    summary["orphaned"] += counts["orphaned"]
                    summary["errors"] += counts["errors"]
                except Exception as e:
                    logger.exception(
                        f"reconcile.user.error user={cred.user_id[:8]}: {e}"
                    )
                    summary["errors"] += 1
        finally:
            db.close()

        return summary

    async def _reconcile_user(self, db, cred: ExchangeCredentials) -> dict:
        """Reconcile one user's open bitget-sourced positions."""
        counts = {"checked": 0, "synced": 0, "orphaned": 0, "errors": 0}

        positions = (
            db.query(Position)
            .filter(
                Position.user_id == cred.user_id,
                Position.source == "bitget",
                Position.status == "OPEN",
                Position.bitget_order_id.isnot(None),
            )
            .all()
        )

        if not positions:
            return counts

        api_key = decrypt(cred.api_key_encrypted)
        api_secret = decrypt(cred.api_secret_encrypted)
        passphrase = decrypt(cred.passphrase_encrypted)
        if not (api_key and api_secret and passphrase):
            logger.error(
                f"reconcile.decrypt.failed user={cred.user_id[:8]} — skipping"
            )
            return counts

        async with BitgetClient(
            api_key=api_key,
            api_secret=api_secret,
            passphrase=passphrase,
            testnet=settings.bitget_testnet,
        ) as client:
            for pos in positions:
                counts["checked"] += 1
                symbol_norm = pos.symbol.replace("/", "")

                try:
                    detail = await client.get_order_detail(
                        order_id=pos.bitget_order_id,
                        symbol=symbol_norm,
                    )
                except BitgetError as e:
                    pos.reconciliation_status = "error"
                    pos.last_reconciled_at = datetime.utcnow()
                    counts["errors"] += 1
                    logger.warning(
                        f"reconcile.api.error user={cred.user_id[:8]} "
                        f"pos={pos.id[:8]} code={e.code} msg={e.msg}"
                    )
                    continue

                status = (detail.get("status") or "").lower()
                pos.last_reconciled_at = datetime.utcnow()

                if status in _FILLED_STATUSES:
                    # Order completed on Bitget. Position is valid. Sync entry
                    # price from Bitget's actual average fill price if present.
                    pos.reconciliation_status = "synced"
                    counts["synced"] += 1
                    fill_price = (
                        detail.get("priceAvg")
                        or detail.get("fillPrice")
                        or detail.get("price")
                    )
                    if fill_price:
                        try:
                            pos.entry_price = float(fill_price)
                        except (TypeError, ValueError):
                            pass

                elif status in _LIVE_STATUSES:
                    pos.reconciliation_status = "synced"
                    counts["synced"] += 1

                elif status in _CANCELLED_STATUSES:
                    # Order did not execute. Close the DB position.
                    pos.status = "CLOSED"
                    pos.close_reason = "RECONCILED_CANCELLED"
                    pos.closed_at = datetime.utcnow()
                    pos.realized_pnl = 0.0
                    pos.reconciliation_status = "orphaned"
                    counts["orphaned"] += 1

                    logger.warning(
                        f"reconcile.orphaned user={cred.user_id[:8]} "
                        f"pos={pos.id[:8]} order={pos.bitget_order_id} "
                        f"bitget_status={status!r}"
                    )

                    # Notify the user via Telegram (best-effort)
                    try:
                        await telegram_service.send_trade_alert(
                            {
                                "id": pos.id,
                                "symbol": pos.symbol,
                                "side": pos.side,
                                "entryPrice": pos.entry_price,
                                "currentPrice": pos.current_price or pos.entry_price,
                                "size": pos.size,
                                "realizedPnl": 0.0,
                                "user_id": pos.user_id,
                            },
                            "RECONCILED_CANCELLED",
                        )
                    except Exception as e:
                        logger.warning(f"reconcile.telegram.error: {e}")

                else:
                    pos.reconciliation_status = "error"
                    counts["errors"] += 1
                    logger.warning(
                        f"reconcile.unknown.status user={cred.user_id[:8]} "
                        f"pos={pos.id[:8]} status={status!r}"
                    )

        db.commit()
        return counts


# Singleton
reconciliation_service = ReconciliationService()