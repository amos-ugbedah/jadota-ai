"""
Strategy registry.

Usage:
    from app.ai.strategies import get_strategy, list_strategies

    strat = get_strategy("conservative")
    signal, confidence = strat.generate_signal(indicators)
"""

from typing import Dict, List
from .base import BaseStrategy
from .conservative import ConservativeStrategy
from .balanced import BalancedStrategy
from .aggressive import AggressiveStrategy
from .scalping import ScalpingStrategy
from .swing import SwingStrategy


# Singleton instances (strategies are stateless after init)
_STRATEGIES: Dict[str, BaseStrategy] = {
    s.NAME: s
    for s in [
        ConservativeStrategy(),
        BalancedStrategy(),
        AggressiveStrategy(),
        ScalpingStrategy(),
        SwingStrategy(),
    ]
}

DEFAULT_STRATEGY_NAME = "balanced"


def get_strategy(name: str | None) -> BaseStrategy:
    """Get a strategy by name, falling back to balanced."""
    if not name:
        return _STRATEGIES[DEFAULT_STRATEGY_NAME]
    return _STRATEGIES.get(name.lower(), _STRATEGIES[DEFAULT_STRATEGY_NAME])


def list_strategies() -> List[Dict]:
    """Return list of strategy metadata dicts (for API)."""
    return [s.to_dict() for s in _STRATEGIES.values()]


def strategy_names() -> List[str]:
    return list(_STRATEGIES.keys())