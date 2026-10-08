from typing import Dict, Tuple
from .base import BaseStrategy, clamp_confidence


class ScalpingStrategy(BaseStrategy):
    NAME = "scalping"
    LABEL = "Scalping"
    DESCRIPTION = "Quick in-and-out on short timeframes. Small profits, high frequency, tight stops."
    RISK_LEVEL = "High"
    ICON = "⚡"
    COLOR = "#f59e0b"
    TIMEFRAME = "5m"

    DEFAULT_CONFIG = {
        "confidence_threshold": 60,
        "trade_amount": 20.0,
        "stop_loss_percent": 0.5,
        "take_profit_percent": 1.0,
        "position_size_multiplier": 0.6,
        "max_positions": 4,
        "max_trades_per_day": 50,
        "risk_per_trade": 0.5,
    }

    def generate_signal(self, ind: Dict[str, float]) -> Tuple[str, int]:
        close = ind["close"]
        rsi = ind["rsi"]
        bb_lower = ind["bb_lower"]
        bb_upper = ind["bb_upper"]
        bb_mid = ind["bb_middle"]

        # Reversal setup: RSI oversold + price at lower BB + momentum just turning
        if rsi < 32 and close <= bb_lower * 1.005:
            hist = ind["macd_histogram"]
            if hist > -abs(ind["macd"] * 0.2):
                return "BUY", clamp_confidence(60 + (32 - rsi) * 1.5)

        if rsi > 68 and close >= bb_upper * 0.995:
            hist = ind["macd_histogram"]
            if hist < abs(ind["macd"] * 0.2):
                return "SELL", clamp_confidence(60 + (rsi - 68) * 1.5)

        # Momentum continuation in a tight range around BB middle
        if bb_mid and abs(close - bb_mid) / bb_mid < 0.003:
            if rsi > 55 and ind["ema_12"] > ind["ema_26"]:
                return "BUY", 62
            if rsi < 45 and ind["ema_12"] < ind["ema_26"]:
                return "SELL", 62

        return "HOLD", 0