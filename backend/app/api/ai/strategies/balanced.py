from typing import Dict, Tuple
from .base import BaseStrategy, clamp_confidence, compute_trend, compute_macd_bias


class BalancedStrategy(BaseStrategy):
    NAME = "balanced"
    LABEL = "Balanced"
    DESCRIPTION = "The default. Combines trend, momentum, and mean-reversion signals into a balanced score."
    RISK_LEVEL = "Medium"
    ICON = "⚖️"
    COLOR = "#6366f1"
    TIMEFRAME = "1h"

    DEFAULT_CONFIG = {
        "confidence_threshold": 65,
        "trade_amount": 25.0,
        "stop_loss_percent": 2.0,
        "take_profit_percent": 4.0,
        "position_size_multiplier": 1.0,
        "max_positions": 5,
        "max_trades_per_day": 10,
        "risk_per_trade": 2.0,
    }

    def generate_signal(self, ind: Dict[str, float]) -> Tuple[str, int]:
        close = ind["close"]
        rsi = ind["rsi"]
        bb_lower = ind["bb_lower"]
        bb_upper = ind["bb_upper"]

        trend = compute_trend(ind)
        macd = compute_macd_bias(ind)

        rsi_bull = rsi < 30
        rsi_bear = rsi > 70
        bb_bull = close <= bb_lower * 1.01
        bb_bear = close >= bb_upper * 0.99

        bullish_score = 0
        bearish_score = 0

        if trend == "up":
            bullish_score += 20
        elif trend == "down":
            bearish_score += 20

        if rsi_bull:
            bullish_score += 15
        elif rsi_bear:
            bearish_score += 15

        if macd == "bull":
            bullish_score += 25
        elif macd == "bear":
            bearish_score += 25

        if bb_bull:
            bullish_score += 10
        elif bb_bear:
            bearish_score += 10

        total = bullish_score + bearish_score
        if total == 0:
            return "HOLD", 0

        if bullish_score > bearish_score:
            return "BUY", clamp_confidence((bullish_score / total) * 80 + 20)
        if bearish_score > bullish_score:
            return "SELL", clamp_confidence((bearish_score / total) * 80 + 20)
        return "HOLD", 50