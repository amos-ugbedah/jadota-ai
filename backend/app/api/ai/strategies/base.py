"""
Base class for all trading strategies.
"""

from typing import Dict, Any, Tuple
from abc import ABC, abstractmethod


class BaseStrategy(ABC):
    # ---- Metadata ----
    NAME: str = "base"
    LABEL: str = "Base"
    DESCRIPTION: str = ""
    RISK_LEVEL: str = "Medium"   # Low | Medium | High
    ICON: str = "📊"
    COLOR: str = "#6366f1"
    TIMEFRAME: str = "1h"

    # ---- Defaults applied when this strategy is activated ----
    DEFAULT_CONFIG: Dict[str, Any] = {}

    def __init__(self):
        self.config = dict(self.DEFAULT_CONFIG)

    @abstractmethod
    def generate_signal(self, ind: Dict[str, float]) -> Tuple[str, int]:
        """
        Given a dict of indicator values, return (signal, confidence).
        signal: "BUY" | "SELL" | "HOLD"
        confidence: 0-100
        """
        raise NotImplementedError

    def to_dict(self) -> Dict[str, Any]:
        """Serializable metadata for API responses."""
        return {
            "name": self.NAME,
            "label": self.LABEL,
            "description": self.DESCRIPTION,
            "risk_level": self.RISK_LEVEL,
            "icon": self.ICON,
            "color": self.COLOR,
            "timeframe": self.TIMEFRAME,
            "defaults": dict(self.config),
        }


# ============================================
# Shared helpers
# ============================================
def clamp_confidence(value: float) -> int:
    """Clamp any confidence to 0-100."""
    return max(0, min(100, int(round(value))))


def compute_trend(ind: Dict[str, float]) -> str:
    """Return 'up' | 'down' | 'flat'."""
    close = ind["close"]
    sma7 = ind["sma_7"]
    sma25 = ind["sma_25"]
    if close > sma7 > sma25:
        return "up"
    if close < sma7 < sma25:
        return "down"
    return "flat"


def compute_macd_bias(ind: Dict[str, float]) -> str:
    """Return 'bull' | 'bear' | 'neutral'."""
    hist = ind["macd_histogram"]
    macd = ind["macd"]
    sig = ind["macd_signal"]
    if hist > 0 and macd > sig:
        return "bull"
    if hist < 0 and macd < sig:
        return "bear"
    return "neutral"