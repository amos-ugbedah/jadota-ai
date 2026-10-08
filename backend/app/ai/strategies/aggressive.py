from typing import Dict, Tuple
from .base import BaseStrategy, clamp_confidence


class AggressiveStrategy(BaseStrategy):
    NAME = "aggressive"
    LABEL = "Aggressive"
    DESCRIPTION = "More trades, wider stops, larger positions. Chases momentum and breakouts."
    RISK_LEVEL = "High"
    ICON = "🔥"
    COLOR = "#ef4444"
    TIMEFRAME = "15m"

    DEFAULT_CONFIG = {
        "confidence_threshold": 55,
        "trade_amount": 50.0,
        "stop_loss_percent": 3.0,
        "take_profit_percent": 6.0,
        "position_size_multiplier": 1.5,
        "max_positions": 8,
        "max_trades_per_day": 25,
        "risk_per_trade": 3.0,
    }

    def generate_signal(self, ind: Dict[str, float]) -> Tuple[str, int]:
        close = ind["close"]
        rsi = ind["rsi"]
        ema12 = ind["ema_12"]
        ema26 = ind["ema_26"]
        macd_hist = ind["macd_histogram"]

        fast_cross_up = ema12 > ema26 and macd_hist > 0
        fast_cross_down = ema12 < ema26 and macd_hist < 0

        momentum_up = rsi > 60 and close > ema12
        momentum_down = rsi < 40 and close < ema12

        bull_points = 0
        bear_points = 0

        if fast_cross_up: bull_points += 40
        if fast_cross_down: bear_points += 40
        if momentum_up: bull_points += 30
        if momentum_down: bear_points += 30
        if close > ind["sma_25"]: bull_points += 15
        if close < ind["sma_25"]: bear_points += 15
        if macd_hist > 0: bull_points += 15
        if macd_hist < 0: bear_points += 15

        if bull_points >= 45:
            return "BUY", clamp_confidence(50 + bull_points * 0.4)
        if bear_points >= 45:
            return "SELL", clamp_confidence(50 + bear_points * 0.4)
        return "HOLD", 0