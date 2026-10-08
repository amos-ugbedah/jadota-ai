from typing import Dict, Tuple
from .base import BaseStrategy, clamp_confidence, compute_trend, compute_macd_bias


class SwingStrategy(BaseStrategy):
    NAME = "swing"
    LABEL = "Swing"
    DESCRIPTION = "Ride trends for days. Ignores short-term noise, holds through pullbacks for big moves."
    RISK_LEVEL = "Medium"
    ICON = "📈"
    COLOR = "#a855f7"
    TIMEFRAME = "4h"

    DEFAULT_CONFIG = {
        "confidence_threshold": 70,
        "trade_amount": 40.0,
        "stop_loss_percent": 4.0,
        "take_profit_percent": 10.0,
        "position_size_multiplier": 1.2,
        "max_positions": 5,
        "max_trades_per_day": 5,
        "risk_per_trade": 2.0,
    }

    def generate_signal(self, ind: Dict[str, float]) -> Tuple[str, int]:
        close = ind["close"]
        sma7 = ind["sma_7"]
        sma25 = ind["sma_25"]
        sma99 = ind["sma_99"]
        rsi = ind["rsi"]

        macd = compute_macd_bias(ind)

        # Strong uptrend: price above all SMAs + MACD agrees + RSI in a healthy band
        if (close > sma7 > sma25 > sma99
                and macd == "bull"
                and 40 < rsi < 75):
            score = 75
            distance = (close - sma99) / sma99 if sma99 else 0
            if distance > 0.03:
                score += 8
            if distance > 0.08:
                score += 5
            if ind["macd_histogram"] > 0 and ind["macd_histogram"] > abs(ind["macd"] * 0.15):
                score += 7
            return "BUY", clamp_confidence(score)

        # Strong downtrend
        if (close < sma7 < sma25 < sma99
                and macd == "bear"
                and 25 < rsi < 60):
            score = 75
            distance = (sma99 - close) / sma99 if sma99 else 0
            if distance > 0.03:
                score += 8
            if distance > 0.08:
                score += 5
            if ind["macd_histogram"] < 0 and abs(ind["macd_histogram"]) > abs(ind["macd"] * 0.15):
                score += 7
            return "SELL", clamp_confidence(score)

        return "HOLD", 0