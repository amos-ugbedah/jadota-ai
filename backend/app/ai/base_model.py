from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime
import pandas as pd
import numpy as np

class BaseModel(ABC):
    """Base class for all AI models."""
    
    def __init__(self, name: str):
        self.name = name
        self.last_score = None
        self.last_update = None
    
    @abstractmethod
    async def calculate(self, data: pd.DataFrame) -> Dict[str, Any]:
        pass
    
    def normalize_score(self, score: float, min_val: float = 0, max_val: float = 100) -> float:
        return max(min_val, min(max_val, score))
    
    def get_ema(self, data: pd.Series, period: int) -> pd.Series:
        return data.ewm(span=period, adjust=False).mean()
    
    def get_sma(self, data: pd.Series, period: int) -> pd.Series:
        return data.rolling(window=period).mean()
    
    def get_rsi(self, data: pd.Series, period: int = 14) -> pd.Series:
        delta = data.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def get_macd(self, data: pd.Series) -> Dict[str, pd.Series]:
        exp1 = data.ewm(span=12, adjust=False).mean()
        exp2 = data.ewm(span=26, adjust=False).mean()
        macd = exp1 - exp2
        signal = macd.ewm(span=9, adjust=False).mean()
        histogram = macd - signal
        return {'macd': macd, 'signal': signal, 'histogram': histogram}
    
    def get_bollinger_bands(self, data: pd.Series, period: int = 20, std_dev: int = 2) -> Dict[str, pd.Series]:
        sma = data.rolling(window=period).mean()
        std = data.rolling(window=period).std()
        upper = sma + (std * std_dev)
        lower = sma - (std * std_dev)
        return {'upper': upper, 'middle': sma, 'lower': lower}
