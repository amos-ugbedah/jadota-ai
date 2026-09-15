from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime
import pandas as pd
import numpy as np

class BaseModel(ABC):
    """Base class for all AI models with common utilities."""
    
    def __init__(self, name: str):
        self.name = name
        self.last_score: Optional[float] = None
        self.last_update: Optional[datetime] = None
        self.last_result: Optional[Dict[str, Any]] = None
    
    @abstractmethod
    async def calculate(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Calculate model output.
        
        Args:
            data: OHLCV DataFrame with 'open', 'high', 'low', 'close', 'volume'
            
        Returns:
            Dict with model results
        """
        pass
    
    def normalize_score(self, score: float, min_val: float = 0, max_val: float = 100) -> float:
        """Normalize a score to a 0-100 range."""
        return max(min_val, min(max_val, float(score)))
    
    def get_ema(self, data: pd.Series, period: int) -> pd.Series:
        """Calculate Exponential Moving Average."""
        return data.ewm(span=period, adjust=False).mean()
    
    def get_sma(self, data: pd.Series, period: int) -> pd.Series:
        """Calculate Simple Moving Average."""
        return data.rolling(window=period).mean()
    
    def get_rsi(self, data: pd.Series, period: int = 14) -> pd.Series:
        """Calculate Relative Strength Index."""
        delta = data.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi.fillna(50)
    
    def get_macd(self, data: pd.Series) -> Dict[str, pd.Series]:
        """Calculate MACD (Moving Average Convergence Divergence)."""
        exp1 = data.ewm(span=12, adjust=False).mean()
        exp2 = data.ewm(span=26, adjust=False).mean()
        macd = exp1 - exp2
        signal = macd.ewm(span=9, adjust=False).mean()
        histogram = macd - signal
        return {'macd': macd, 'signal': signal, 'histogram': histogram}
    
    def get_bollinger_bands(self, data: pd.Series, period: int = 20, std_dev: int = 2) -> Dict[str, pd.Series]:
        """Calculate Bollinger Bands."""
        sma = data.rolling(window=period).mean()
        std = data.rolling(window=period).std()
        upper = sma + (std * std_dev)
        lower = sma - (std * std_dev)
        return {'upper': upper, 'middle': sma, 'lower': lower}
    
    def get_atr(self, high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        """Calculate Average True Range."""
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        return tr.rolling(window=period).mean()
    
    def get_stochastic(self, high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        """Calculate Stochastic Oscillator."""
        lowest_low = low.rolling(window=period).min()
        highest_high = high.rolling(window=period).max()
        return 100 * ((close - lowest_low) / (highest_high - lowest_low))
    
    def get_historical_volatility(self, data: pd.Series, period: int = 20) -> pd.Series:
        """Calculate Historical Volatility (annualized)."""
        returns = data.pct_change()
        return returns.rolling(window=period).std() * np.sqrt(252)
    
    def get_volume_profile(self, volume: pd.Series, price: pd.Series, period: int = 20) -> float:
        """Calculate volume-weighted price profile."""
        avg_volume = volume.rolling(window=period).mean()
        if len(avg_volume) == 0 or pd.isna(avg_volume.iloc[-1]):
            return 50
        vol_ratio = volume.iloc[-1] / avg_volume.iloc[-1]
        price_change = (price.iloc[-1] - price.iloc[-period]) / price.iloc[-period] if period < len(price) else 0
        
        if vol_ratio > 1.5 and price_change > 0.02:
            return 80
        elif vol_ratio > 1.5 and price_change < -0.02:
            return 80
        elif vol_ratio < 0.5:
            return 30
        return 50

    def get_model_status(self) -> Dict[str, Any]:
        """Get current model status."""
        return {
            'name': self.name,
            'last_score': self.last_score,
            'last_update': self.last_update.isoformat() if self.last_update else None,
            'has_result': self.last_result is not None
        }