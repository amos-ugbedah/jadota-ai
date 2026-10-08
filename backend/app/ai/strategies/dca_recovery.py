from typing import Dict, Tuple, Optional, Any
from .base import BaseStrategy, clamp_confidence


class DCARecoveryStrategy(BaseStrategy):
    """
    Dollar-Cost-Averaging Recovery Strategy.

    Waits for oversold conditions to enter, then averages down on deeper
    drops. Exits on small recovery above the average cost. Uses a very
    wide panic stop-loss (20%) as a last-resort safety net.

    Unlike other strategies, this one is position-aware: it receives
    the current open position (if any) and can return "ADD" to signal
    that the engine should buy more and merge with the existing position.
    """

    NAME = "dca_recovery"
    LABEL = "DCA Recovery"
    DESCRIPTION = (
        "Buys oversold dips and averages down on further drops. "
        "Exits on small recovery above average cost. Holds through "
        "drawdowns (up to 20% panic stop)."
    )
    RISK_LEVEL = "High"
    ICON = "💰"
    COLOR = "#14b8a6"
    TIMEFRAME = "1h"

    DEFAULT_CONFIG = {
        "confidence_threshold": 55,
        "trade_amount": 30.0,
        "stop_loss_percent": 20.0,   # panic stop only
        "take_profit_percent": 2.0,  # small recovery target
        "position_size_multiplier": 0.5,
        "max_positions": 3,
        "max_trades_per_day": 10,
        "risk_per_trade": 5.0,
        # DCA behaviour (informational — used by the engine)
        "dip_levels": [3.0, 6.0, 10.0],
        "recovery_target_percent": 2.0,
    }

    def generate_signal(
        self,
        ind: Dict[str, float],
        position_context: Optional[Dict[str, Any]] = None,
    ) -> Tuple[str, int]:
        """
        If position_context is None:
            → This is an ENTRY decision. Buy oversold dips.
        If position_context has an OPEN position:
            → This is a MANAGE decision. ADD on dips, SELL on recovery.
        """
        close = ind["close"]
        rsi = ind["rsi"]
        bb_lower = ind["bb_lower"]
        bb_mid = ind["bb_middle"]

        # ============================================
        # Case A — Managing an existing position
        # ============================================
        if position_context:
            entry_price = float(position_context.get("entryPrice") or 0)
            side = position_context.get("side", "BUY")
            if entry_price > 0:
                pnl_pct = ((close - entry_price) / entry_price) * 100.0
                if side == "SELL":
                    pnl_pct = -pnl_pct  # invert for shorts

                dip_levels = self.config.get("dip_levels", [3.0, 6.0, 10.0])
                recovery_target = self.config.get("recovery_target_percent", 2.0)

                # Recovery — take the small win and exit
                if pnl_pct >= recovery_target:
                    return "SELL" if side == "BUY" else "BUY", 70

                # Deepest dip triggers the strongest add
                for level in reversed(dip_levels):
                    if pnl_pct <= -level:
                        # Deeper dips → higher confidence in ADD
                        if level >= dip_levels[-1]:
                            return "ADD", 80
                        elif level >= dip_levels[len(dip_levels) // 2]:
                            return "ADD", 70
                        else:
                            return "ADD", 60

                # Between entry and next dip level — hold
                return "HOLD", 0

        # ============================================
        # Case B — No position: look for entry
        # ============================================
        oversold = rsi < 40
        at_lower_bb = close <= bb_lower * 1.02
        below_mid = bb_mid and close < bb_mid

        if oversold and at_lower_bb and below_mid:
            # Deeper oversold = higher confidence
            score = 55 + (40 - rsi) * 1.2
            return "BUY", clamp_confidence(score)

        # Extreme oversold alone also triggers (rare event)
        if rsi < 25:
            return "BUY", clamp_confidence(70 + (25 - rsi) * 2.0)

        return "HOLD", 0