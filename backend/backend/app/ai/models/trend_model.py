import pandas as pd
import numpy as np
from typing import Dict, Any
from ..base_model import BaseModel

class TrendModel(BaseModel):
    """
    Trend detection using multiple timeframes.
    
    Analyzes price trends using:
    - Moving averages (50, 100, 200)
    - MACD
    - ADX (Average Directional Index)
    """
    
    def __init__(self):
        super().__init__("Trend Model")
        self.weights = {
            'ema_50': 0.25,
            'ema_100': 0.20,
            'ema_200': 0.15,
            'macd': 0.25,
            'adx': 0.15
        }
    
    async def calculate(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Calculate trend score."""
        close = data['close']
        high = data['high']
        low = data['low']
        
        # Calculate EMAs
        ema_50 = self.get_ema(close, 50)
        ema_100 = self.get_ema(close, 100)
        ema_200 = self.get_ema(close, 200)
        
        # Calculate MACD
        macd_data = self.get_macd(close)
        
        # Calculate ADX (simplified)
        adx = self._calculate_adx(high, low, close, period=14)
        
        # Get latest values
        latest_close = close.iloc[-1]
        latest_ema_50 = ema_50.iloc[-1] if len(ema_50) > 0 else latest_close
        latest_ema_100 = ema_100.iloc[-1] if len(ema_100) > 0 else latest_close
        latest_ema_200 = ema_200.iloc[-1] if len(ema_200) > 0 else latest_close
        latest_macd = macd_data['macd'].iloc[-1] if len(macd_data['macd']) > 0 else 0
        latest_signal = macd_data['signal'].iloc[-1] if len(macd_data['signal']) > 0 else 0
        latest_adx = adx.iloc[-1] if len(adx) > 0 else 25
        
        # Calculate individual scores (0-100 scale)
        # 0 = Bearish, 50 = Neutral, 100 = Bullish
        
        # EMA Scores
        ema_50_score = self._score_cross(latest_close, latest_ema_50)
        ema_100_score = self._score_cross(latest_close, latest_ema_100)
        ema_200_score = self._score_cross(latest_close, latest_ema_200)
        
        # MACD Score
        macd_score = self._score_macd(latest_macd, latest_signal)
        
        # ADX Score
        adx_score = self._score_adx(latest_adx)
        
        # Weighted average
        total_score = (
            ema_50_score * self.weights['ema_50'] +
            ema_100_score * self.weights['ema_100'] +
            ema_200_score * self.weights['ema_200'] +
            macd_score * self.weights['macd'] +
            adx_score * self.weights['adx']
        )
        
        # Determine direction
        if total_score > 60:
            direction = "BULLISH"
            confidence = min(100, (total_score - 50) * 2)
        elif total_score < 40:
            direction = "BEARISH"
            confidence = min(100, (50 - total_score) * 2)
        else:
            direction = "NEUTRAL"
            confidence = 50
        
        self.last_score = total_score
        self.last_update = pd.Timestamp.now()
        
        return {
            'model': self.name,
            'score': total_score,
            'direction': direction,
            'confidence': confidence,
            'components': {
                'ema_50': ema_50_score,
                'ema_100': ema_100_score,
                'ema_200': ema_200_score,
                'macd': macd_score,
                'adx': adx_score
            },
            'timestamp': self.last_update.isoformat()
        }
    
    def _score_cross(self, price: float, moving_average: float) -> float:
        """Score based on price vs moving average."""
        if pd.isna(moving_average):
            return 50
        diff_pct = ((price - moving_average) / moving_average) * 100
        # Map diff_pct to 0-100 scale
        return max(0, min(100, 50 + (diff_pct * 2)))
    
    def _score_macd(self, macd: float, signal: float) -> float:
        """Score based on MACD vs Signal line."""
        if pd.isna(macd) or pd.isna(signal):
            return 50
        diff = macd - signal
        # Map diff to 0-100 scale (assume max diff is 5)
        normalized = (diff / 5) * 50
        return max(0, min(100, 50 + normalized))
    
    def _score_adx(self, adx: float) -> float:
        """Score based on ADX value."""
        if pd.isna(adx):
            return 50
        # ADX > 25 indicates strong trend
        if adx > 25:
            return min(100, 50 + (adx - 25) * 2)
        else:
            return max(0, 50 - (25 - adx) * 2)
    
    def _calculate_adx(self, high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        """Calculate ADX (simplified)."""
        # True Range
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        
        # Directional Movement
        plus_dm = high.diff()
        minus_dm = low.diff()
        
        plus_dm = plus_dm.where((plus_dm > minus_dm) & (plus_dm > 0), 0)
        minus_dm = minus_dm.where((minus_dm > plus_dm) & (minus_dm > 0), 0)
        
        # Average True Range
        atr = tr.rolling(window=period).mean()
        
        # Directional Indicators
        plus_di = 100 * (plus_dm.rolling(window=period).mean() / atr)
        minus_di = 100 * (minus_dm.rolling(window=period).mean() / atr)
        
        # DX and ADX
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
        adx = dx.rolling(window=period).mean()
        
        return adx
