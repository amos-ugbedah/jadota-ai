import pandas as pd
import numpy as np
from typing import Dict, Any
from ..base_model import BaseModel

class VolatilityModel(BaseModel):
    """
    Volatility assessment using ATR, Bollinger Bands, historical volatility.
    """
    
    def __init__(self):
        super().__init__("Volatility Model")
    
    async def calculate(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Calculate volatility score."""
        close = data['close']
        high = data['high']
        low = data['low']
        
        atr = self._calculate_atr(high, low, close, 14)
        bb_width = self._calculate_bb_width(close, 20, 2)
        hist_vol = self._calculate_historical_volatility(close, 20)
        
        latest_atr = float(atr.iloc[-1]) if len(atr) > 0 else float(close.iloc[-1] * 0.02)
        latest_bb_width = float(bb_width.iloc[-1]) if len(bb_width) > 0 else 5
        latest_hist_vol = float(hist_vol.iloc[-1]) if len(hist_vol) > 0 else 0.3
        
        atr_score = self._score_atr(latest_atr, float(close.iloc[-1]))
        bb_width_score = self._score_bb_width(latest_bb_width)
        hist_vol_score = self._score_historical_volatility(latest_hist_vol)
        
        total_score = (atr_score + bb_width_score + hist_vol_score) / 3
        
        if total_score > 70:
            level = "HIGH"
        elif total_score > 40:
            level = "MODERATE"
        else:
            level = "LOW"
        
        self.last_score = total_score
        self.last_update = pd.Timestamp.now()
        
        return {
            'model': self.name,
            'score': total_score,
            'volatility_level': level,
            'components': {
                'atr': atr_score,
                'bb_width': bb_width_score,
                'historical_volatility': hist_vol_score
            },
            'timestamp': self.last_update.isoformat()
        }
    
    def _calculate_atr(self, high: pd.Series, low: pd.Series, close: pd.Series, period: int) -> pd.Series:
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        return tr.rolling(window=period).mean()
    
    def _calculate_bb_width(self, data: pd.Series, period: int, std_dev: int) -> pd.Series:
        bb = self.get_bollinger_bands(data, period, std_dev)
        width = (bb['upper'] - bb['lower']) / bb['middle']
        return width * 100
    
    def _calculate_historical_volatility(self, data: pd.Series, period: int) -> pd.Series:
        returns = data.pct_change()
        return returns.rolling(window=period).std() * np.sqrt(252)
    
    def _score_atr(self, atr: float, price: float) -> float:
        if pd.isna(atr) or price == 0:
            return 50
        atr_pct = (atr / price) * 100
        return min(100, (atr_pct / 5) * 100)
    
    def _score_bb_width(self, width: float) -> float:
        if pd.isna(width):
            return 50
        return min(100, (width / 20) * 100)
    
    def _score_historical_volatility(self, vol: float) -> float:
        if pd.isna(vol):
            return 50
        return min(100, vol * 100)
