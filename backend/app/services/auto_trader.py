"""
Auto-Trader — background service that runs AI auto-trade for every user
who has auto_trade_enabled = True AND an active Bitget connection.

Runs every AUTO_TRADE_INTERVAL_SECONDS (default 300 = 5 minutes).

Safety rules enforced on every pass:
    - Only consider users with auto_trade_enabled = True
    - Only consider users with an active Bitget credential
    - Respect max_trades_per_day (count today's bitget-source positions)
    - Respect max_positions (skip user if they're at the cap)
    - Skip symbols the user already has an OPEN position on
    - Only fire on signal == BUY and confidence >= threshold
"""

import asyncio
import logging
from datetime import datetime

from ..core.database import SessionLocal
from ..models.ai_settings import AISettings
from ..models.exchange_credentials import ExchangeCredentials
from ..models.position import Position
from .ai_trading_service import ai_trading_service
from .position_store import list_positions
from .trade_executor import execute_ai_trade

logger = logging.getLogger(__name__)

AUTO_TRADE_INTERVAL_SECONDS = 300  # 5 minutes


class AutoTrader:
    def __init__(self, interval_seconds: int = AUTO_TRADE_INTERVAL_SECONDS):
        self.interval_seconds = interval_seconds
        self.is_running = False
        self._task = None

    async def start(self) -> None:
        if self.is_running:
            return
        self.is_running = True
        self._task = asyncio.create_task(self._loop())
        logger.info(
            f"✅ Auto-Trader service started (interval={self.interval_seconds}s)"
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
        logger.info("Auto-Trader service stopped")

    async def _loop(self) -> None:
        # Small initial delay so we don't hammer Bitget right at boot
        await asyncio.sleep(30)
        while self.is_running:
            try:
                summary = await self.run_once()
                if summary["users_processed"]:
                    logger.info(
                        f"auto_trader.pass users={summary['users_processed']} "
                        f"fired={summary['trades_fired']} "
                        f"skipped={summary['skipped']} "
                        f"errors={summary['errors']}"
                    )
            except Exception as e:
                logger.exception(f"auto_trader.loop.error: {e}")
            await asyncio.sleep(self.interval_seconds)

    async def run_once(self) -> dict:
        """One pass across all eligible users. Admin-triggerable via API."""
        summary = {
            "users_processed": 0,
            "trades_fired": 0,
            "skipped": 0,
            "errors": 0,
        }

        db = SessionLocal()
        try:
            enabled_settings = (
                db.query(AISettings)
                .filter(AISettings.auto_trade_enabled == True)  # noqa: E712
                .all()
            )
            if not enabled_settings:
                return summary

            user_ids = [s.user_id for s in enabled_settings]
            active_creds = (
                db.query(ExchangeCredentials.user_id)
                .filter(
                    ExchangeCredentials.user_id.in_(user_ids),
                    ExchangeCredentials.exchange == "bitget",
                    ExchangeCredentials.is_active == True,  # noqa: E712
                )
                .all()
            )
            active_user_ids = {row.user_id for row in active_creds}

            for settings in enabled_settings:
                if settings.user_id not in active_user_ids:
                    continue
                summary["users_processed"] += 1
                try:
                    counts = await self._process_user(db, settings)
                    summary["trades_fired"] += counts["trades_fired"]
                    summary["skipped"] += counts["skipped"]
                    summary["errors"] += counts["errors"]
                except Exception as e:
                    logger.exception(
                        f"auto_trader.user.error user={settings.user_id[:8]}: {e}"
                    )
                    summary["errors"] += 1
        finally:
            db.close()

        return summary

    async def _process_user(self, db, settings: AISettings) -> dict:
        counts = {"trades_fired": 0, "skipped": 0, "errors": 0}

        user_id = settings.user_id
        user_symbols = settings.get_symbols_list() or []
        if not user_symbols:
            return counts

        confidence_threshold = settings.confidence_threshold or 70.0
        strategy_name = getattr(settings, "strategy_type", None) or "balanced"
        max_trades_per_day = settings.max_trades_per_day or 10
        max_positions = settings.max_positions or 5

        # --- rate limit: trades already fired today ---
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        trades_today = (
            db.query(Position)
            .filter(
                Position.user_id == user_id,
                Position.opened_at >= today_start,
                Position.source == "bitget",
            )
            .count()
        )
        if trades_today >= max_trades_per_day:
            counts["skipped"] += 1
            return counts

        # --- position cap ---
        open_positions = list_positions(db, user_id=user_id, status="OPEN")
        if len(open_positions) >= max_positions:
            counts["skipped"] += 1
            return counts

        # --- skip symbols already held ---
        held_symbols = {p["symbol"] for p in open_positions}
        candidates = [s for s in user_symbols if s not in held_symbols]
        if not candidates:
            counts["skipped"] += 1
            return counts

        # --- analyze each candidate ---
        signals = {}
        for sym in candidates:
            try:
                signals[sym] = await ai_trading_service.analyze_symbol(
                    sym,
                    timeframe="1h",
                    strategy=strategy_name,
                    positions=open_positions,
                )
            except Exception as e:
                logger.warning(
                    f"auto_trader.analyze.error user={user_id[:8]} sym={sym}: {e}"
                )
                counts["errors"] += 1

        # --- fire on BUY signals above threshold ---
        for symbol, signal in signals.items():
            if signal.get("signal") != "BUY":
                continue
            if signal.get("confidence", 0) < confidence_threshold:
                continue

            try:
                await execute_ai_trade(symbol, "BUY", signal, user_id)
                counts["trades_fired"] += 1
                logger.info(
                    f"auto_trader.fired user={user_id[:8]} symbol={symbol} "
                    f"confidence={signal.get('confidence')}"
                )
            except Exception as e:
                logger.warning(
                    f"auto_trader.execute.error user={user_id[:8]} "
                    f"symbol={symbol}: {e}"
                )
                counts["errors"] += 1

        return counts


# Singleton
auto_trader = AutoTrader()