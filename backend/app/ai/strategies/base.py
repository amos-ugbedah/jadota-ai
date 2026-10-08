"""
Base class for all trading strategies.
"""

from typing import Dict, Any, Tuple, Optional
from abc import ABC, abstractmethod


class BaseStrategy(ABC):
    # ---- Metadata ----
    NAME: str = "base"
    LABEL: str = "Base"
    DESCRIPTION: str = ""
    RISK_LEVEL: str = "Medium"
    ICON: str = "📊"
    COLOR: str = "#6366f1"
    TIMEFRAME: str = "1h"

    DEFAULT_CONFIG: Dict[str, Any] = {}

    def __init__(self):
        self.config = dict(self.DEFAULT_CONFIG)

    @abstractmethod
    def generate_signal(self, ind: Dict[str, float]) -> Tuple[str, int]:
        """
        Given a dict of indicator values, return (signal, confidence).

        NOTE: Strategies that need to manage existing positions can override
        with a wider signature that also accepts `position_context`:

            def generate_signal(self, ind, position_context=None):
                ...

        The engine calls this method defensively — it will pass
        `position_context` if the override accepts it, otherwise it calls
        with `ind` only.
        """
        raise NotImplementedError

    def to_dict(self) -> Dict[str, Any]:
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

    def call_generate_signal(
        self,
        ind: Dict[str, float],
        position_context: Optional[Dict[str, Any]] = None,
    ) -> Tuple[str, int]:
        """
        Wrapper that tries the 2-arg version first, falls back to 1-arg.
        This lets existing strategies keep working untouched while
        position-aware strategies (DCA) can use the extra context.
        """
        try:
            return self.generate_signal(ind, position_context)  # type: ignore[call-arg]
        except TypeError:
            return self.generate_signal(ind)


# ============================================
# Shared helpers (unchanged)
# ============================================
def clamp_confidence(value: float) -> int:
    return max(0, min(100, int(round(value))))


def compute_trend(ind: Dict[str, float]) -> str:
    close = ind["close"]
    sma7 = ind["sma_7"]
    sma25 = ind["sma_25"]
    if close > sma7 > sma25:
        return "up"
    if close < sma7 < sma25:
        return "down"
    return "flat"


def compute_macd_bias(ind: Dict[str, float]) -> str:
    hist = ind["macd_histogram"]
    macd = ind["macd"]
    sig = ind["macd_signal"]
    if hist > 0 and macd > sig:
        return "bull"
    if hist < 0 and macd < sig:
        return "bear"
    return "neutral"