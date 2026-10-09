"""
Position Monitor Service - Monitors open positions for Stop-Loss / Take-Profit.

Reads OPEN positions from the `positions` table on every tick, updates the
current price and unrealized P&L, and closes any position whose stop-loss
or take-profit has been hit.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any

from .telegram_service import telegram_service
from .position_store import list_positions, update_position, close_position
from ..core.database import SessionLocal
from ..models.user import User

logger = logging.getLogger(__name__)

TICK_SECONDS = 2


class PositionMonitor:
    """Monitors open positions and triggers Stop-Loss / Take-Profit."""

    def __init__(self):
        self.is_running = False
        self._task = None
        self.market_service = None
        # In-memory record of closed trades since process start.
        # Persisted positions live in the DB; this is only for fast /performance reads.
        self.trade_history = []

    async def start(self, market_service):
        """Start the position monitor. Positions now live in the DB."""
        self.market_service = market_service
        self.is_running = True
        self._task = asyncio.create_task(self._monitor_loop())
        logger.info("✅ Position Monitor started")

    async def stop(self):
        """Stop the position monitor."""
        self.is_running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        logger.info("Position Monitor stopped")

    async def _monitor_loop(self):
        """Main monitoring loop."""
        while self.is_running:
            try:
                await self._check_positions()
            except Exception as e:
                logger.error(f"Position monitor error: {e}")
            await asyncio.sleep(TICK_SECONDS)

    async def _check_positions(self):
        """Check all OPEN positions for SL / TP triggers."""
        db = SessionLocal()
        try:
            open_positions = list_positions(db, status="OPEN")
        finally:
            db.close()

        if not open_positions:
            return

        for pos in open_positions:
            symbol = pos.get("symbol")
            current_price = self.market_service.get_price(symbol)
            if current_price == 0:
                continue

            # Compute unrealized P&L and persist current price
            if pos["side"] == "BUY":
                unrealized = (current_price - pos["entryPrice"]) * pos["size"]
            else:
                unrealized = (pos["entryPrice"] - current_price) * pos["size"]

            db = SessionLocal()
            try:
                update_position(db, pos["id"], {
                    "currentPrice": current_price,
                    "unrealizedPnl": round(unrealized, 8),
                })
            finally:
                db.close()

            # SL / TP checks
            stop_loss = pos.get("stopLoss")
            take_profit = pos.get("takeProfit")

            if stop_loss and current_price <= stop_loss:
                await self._close_position(pos["id"], "STOP_LOSS", current_price)
                continue

            if take_profit and current_price >= take_profit:
                await self._close_position(pos["id"], "TAKE_PROFIT", current_price)
                continue

    async def _close_position(self, position_id: str, reason: str, exit_price: float):
        """Close a position via the store, record history, send alerts."""
        db = SessionLocal()
        try:
            closed = close_position(db, position_id, reason, exit_price=exit_price)
        finally:
            db.close()

        if not closed:
            logger.warning(f"Close requested for missing position {position_id}")
            return

        # Record for fast /performance reads
        trade_record = {
            "id": closed["id"],
            "symbol": closed["symbol"],
            "side": closed["side"],
            "entryPrice": closed["entryPrice"],
            "exitPrice": exit_price,
            "size": closed["size"],
            "pnl": closed["realizedPnl"],
            "reason": reason,
            "aiConfidence": closed.get("aiConfidence", 0),
            "aiReasoning": closed.get("aiReasoning", ""),
            "openedAt": closed.get("openedAt"),
            "closedAt": closed.get("closedAt"),
            "user_id": closed.get("user_id"),
        }
        self.trade_history.append(trade_record)

        logger.info(
            f"📊 Position CLOSED: {closed['symbol']} {closed['side']} | "
            f"{reason} | P&L: ${closed['realizedPnl']:.2f}"
        )

        # Telegram alerts
        await telegram_service.send_trade_alert(closed, reason)

        user_info = None
        if closed.get("user_id"):
            try:
                db = SessionLocal()
                user = db.query(User).filter(User.id == closed["user_id"]).first()
                if user:
                    user_info = {
                        "full_name": user.full_name or user.username,
                        "username": user.username,
                        "email": user.email,
                    }
                db.close()
            except Exception as e:
                logger.error(f"Error fetching user info: {e}")

        await telegram_service.send_public_trade_alert(closed, reason, user_info)

    def get_trade_history(self, limit: int = 50):
        return self.trade_history[-limit:] if self.trade_history else []

    def get_performance_stats(self) -> Dict:
        if not self.trade_history:
            return {
                "total_trades": 0, "winning_trades": 0, "losing_trades": 0,
                "win_rate": 0, "total_pnl": 0, "avg_win": 0, "avg_loss": 0,
                "profit_factor": 0, "best_trade": 0, "worst_trade": 0,
            }

        wins = [t for t in self.trade_history if t["pnl"] > 0]
        losses = [t for t in self.trade_history if t["pnl"] < 0]

        total_trades = len(self.trade_history)
        winning_trades = len(wins)
        losing_trades = len(losses)
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        total_pnl = sum(t["pnl"] for t in self.trade_history)
        avg_win = sum(t["pnl"] for t in wins) / winning_trades if winning_trades > 0 else 0
        avg_loss = sum(t["pnl"] for t in losses) / losing_trades if losing_trades > 0 else 0
        gross_loss = sum(t["pnl"] for t in losses)
        gross_profit = sum(t["pnl"] for t in wins)
        profit_factor = abs(gross_profit / gross_loss) if gross_loss != 0 else 0
        best_trade = max([t["pnl"] for t in self.trade_history]) if self.trade_history else 0
        worst_trade = min([t["pnl"] for t in self.trade_history]) if self.trade_history else 0

        return {
            "total_trades": total_trades,
            "winning_trades": winning_trades,
            "losing_trades": losing_trades,
            "win_rate": round(win_rate, 2),
            "total_pnl": round(total_pnl, 2),
            "avg_win": round(avg_win, 2),
            "avg_loss": round(avg_loss, 2),
            "profit_factor": round(profit_factor, 2),
            "best_trade": round(best_trade, 2),
            "worst_trade": round(worst_trade, 2),
        }


# Singleton
position_monitor = PositionMonitor()