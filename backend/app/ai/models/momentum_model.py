import pandas as pd
import numpy as np
from typing import Dict, Any
from ..base_model import BaseModel

class MomentumModel(BaseModel):
    """
    Momentum detection using RSI, ROC, Stochastic, Williams %R.
    """
    
    def __init__(self):
        super().__init__("Momentum Model")
        self.weights = {
            'rsi': 0.35,
            'roc': 0.25,
            'stochastic': 0.25,
            'williams': 0.15
        }
    
    async def calculate(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Calculate momentum score."""
        close = data['close']
        high = data['high']
        low = data['low']
        
        rsi = self.get_rsi(close, 14)
        roc = self._calculate_roc(close, 10)
        stochastic = self._calculate_stochastic(high, low, close, 14)
        williams = self._calculate_williams(high, low, close, 14)
        
        latest_rsi = float(rsi.iloc[-1]) if len(rsi) > 0 else 50
        latest_roc = float(roc.iloc[-1]) if len(roc) > 0 else 0
        latest_stochastic = float(stochastic.iloc[-1]) if len(stochastic) > 0 else 50
        latest_williams = float(williams.iloc[-1]) if len(williams) > 0 else -50
        
        rsi_score = self._score_rsi(latest_rsi)
        roc_score = self._score_roc(latest_roc)
        stochastic_score = self._score_stochastic(latest_stochastic)
        williams_score = self._score_williams(latest_williams)
        
        total_score = (
            rsi_score * self.weights['rsi'] +
            roc_score * self.weights['roc'] +
            stochastic_score * self.weights['stochastic'] +
            williams_score * self.weights['williams']
        )
        
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
                'rsi': rsi_score,
                'roc': roc_score,
                'stochastic': stochastic_score,
                'williams': williams_score
            },
            'timestamp': self.last_update.isoformat()
        }
    
    def _calculate_roc(self, data: pd.Series, period: int) -> pd.Series:
        return ((data - data.shift(period)) / data.shift(period)) * 100
    
    def _calculate_stochastic(self, high: pd.Series, low: pd.Series, close: pd.Series, period: int) -> pd.Series:
        lowest_low = low.rolling(window=period).min()
        highest_high = high.rolling(window=period).max()
        return 100 * ((close - lowest_low) / (highest_high - lowest_low))
    
    def _calculate_williams(self, high: pd.Series, low: pd.Series, close: pd.Series, period: int) -> pd.Series:
        highest_high = high.rolling(window=period).max()
        lowest_low = low.rolling(window=period).min()
        return -100 * ((highest_high - close) / (highest_high - lowest_low))
    
    def _score_rsi(self, rsi: float) -> float:
        if pd.isna(rsi):
            return 50
        if rsi > 70:
            return 70
        elif rsi < 30:
            return 30
        else:
            return ((rsi - 30) / 40) * 100
    
    def _score_roc(self, roc: float) -> float:
        if pd.isna(roc):
            return 50
        normalized = (roc / 20) * 50
        return max(0, min(100, 50 + normalized))
    
    def _score_stochastic(self, stochastic: float) -> float:
        if pd.isna(stochastic):
            return 50
        if stochastic > 80:
            return 70
        elif stochastic < 20:
            return 30
        else:
            return ((stochastic - 20) / 60) * 100
    
    def _score_williams(self, williams: float) -> float:
        if pd.isna(williams):
            return 50
        return max(0, min(100, 50 + (williams / 2)))
