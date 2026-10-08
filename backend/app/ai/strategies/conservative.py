from typing import Dict, Tuple
from .base import BaseStrategy, clamp_confidence, compute_trend, compute_macd_bias


class ConservativeStrategy(BaseStrategy):
    NAME = "conservative"
    LABEL = "Conservative"
    DESCRIPTION = "Capital preservation first. Only the highest-quality setups, tight stops, small positions."
    RISK_LEVEL = "Low"
    ICON = "🛡️"
    COLOR = "#10b981"
    TIMEFRAME = "4h"

    DEFAULT_CONFIG = {
        "confidence_threshold": 75,
        "trade_amount": 25.0,
        "stop_loss_percent": 1.5,
        "take_profit_percent": 3.0,
        "position_size_multiplier": 0.5,
        "max_positions": 3,
        "max_trades_per_day": 3,
        "risk_per_trade": 1.0,
    }

    def generate_signal(self, ind: Dict[str, float]) -> Tuple[str, int]:
        close = ind["close"]
        rsi = ind["rsi"]
        bb_lower = ind["bb_lower"]
        bb_upper = ind["bb_upper"]

        trend = compute_trend(ind)
        macd = compute_macd_bias(ind)

        # Strict bullish: uptrend + MACD bullish + not overbought + not at bottom of a dump
        if (trend == "up" and macd == "bull"
                and rsi < 65
                and close > bb_lower * 1.02):
            score = 70
            if rsi < 55:
                score += 5
            if close > ind["sma_99"]:
                score += 10
            if ind["macd_histogram"] > abs(ind["macd"] * 0.1):
                score += 5
            return "BUY", clamp_confidence(score)

        # Strict bearish: downtrend + MACD bearish + not oversold
        if (trend == "down" and macd == "bear"
                and rsi > 35
                and close < bb_upper * 0.98):
            score = 70
            if rsi > 45:
                score += 5
            if close < ind["sma_99"]:
                score += 10
            if abs(ind["macd_histogram"]) > abs(ind["macd"] * 0.1):
                score += 5
            return "SELL", clamp_confidence(score)

        return "HOLD", 0