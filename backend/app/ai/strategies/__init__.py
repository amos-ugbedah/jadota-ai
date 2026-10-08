"""
Strategy registry.
"""

from typing import Dict, List
from .base import BaseStrategy
from .conservative import ConservativeStrategy
from .balanced import BalancedStrategy
from .aggressive import AggressiveStrategy
from .scalping import ScalpingStrategy
from .swing import SwingStrategy
from .dca_recovery import DCARecoveryStrategy


_STRATEGIES: Dict[str, BaseStrategy] = {
    s.NAME: s
    for s in [
        ConservativeStrategy(),
        BalancedStrategy(),
        AggressiveStrategy(),
        ScalpingStrategy(),
        SwingStrategy(),
        DCARecoveryStrategy(),
    ]
}

DEFAULT_STRATEGY_NAME = "balanced"


def get_strategy(name: str | None) -> BaseStrategy:
    if not name:
        return _STRATEGIES[DEFAULT_STRATEGY_NAME]
    return _STRATEGIES.get(name.lower(), _STRATEGIES[DEFAULT_STRATEGY_NAME])


def list_strategies() -> List[Dict]:
    return [s.to_dict() for s in _STRATEGIES.values()]


def strategy_names() -> List[str]:
    return list(_STRATEGIES.keys())