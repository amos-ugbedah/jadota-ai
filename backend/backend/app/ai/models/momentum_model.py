import pandas as pd
import numpy as np
from typing import Dict, Any
from ..base_model import BaseModel

class MomentumModel(BaseModel):
    """
    Momentum detection using:
    - RSI (Relative Strength Index)
    - Rate of Change (ROC)
    - Stochastic Oscillator
    - Williams %R
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
        
        # Calculate indicators
        rsi = self.get_rsi(close, 14)
        roc = self._calculate_roc(close, 10)
        stochastic = self._calculate_stochastic(high, low, close, 14)
        williams = self._calculate_williams(high, low, close, 14)
        
        # Get latest values
        latest_rsi = rsi.iloc[-1] if len(rsi) > 0 else 50
        latest_roc = roc.iloc[-1] if len(roc) > 0 else 0
        latest_stochastic = stochastic.iloc[-1] if len(stochastic) > 0 else 50
        latest_williams = williams.iloc[-1] if len(williams) > 0 else -50
        
        # Calculate individual scores
        rsi_score = self._score_rsi(latest_rsi)
        roc_score = self._score_roc(latest_roc)
        stochastic_score = self._score_stochastic(latest_stochastic)
        williams_score = self._score_williams(latest_williams)
        
        # Weighted average
        total_score = (
            rsi_score * self.weights['rsi'] +
            roc_score * self.weights['roc'] +
            stochastic_score * self.weights['stochastic'] +
            williams_score * self.weights['williams']
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
                'rsi': rsi_score,
                'roc': roc_score,
                'stochastic': stochastic_score,
                'williams': williams_score
            },
            'timestamp': self.last_update.isoformat()
        }
    
    def _calculate_roc(self, data: pd.Series, period: int) -> pd.Series:
        """Calculate Rate of Change."""
        return ((data - data.shift(period)) / data.shift(period)) * 100
    
    def _calculate_stochastic(self, high: pd.Series, low: pd.Series, close: pd.Series, period: int) -> pd.Series:
        """Calculate Stochastic Oscillator."""
        lowest_low = low.rolling(window=period).min()
        highest_high = high.rolling(window=period).max()
        stochastic = 100 * ((close - lowest_low) / (highest_high - lowest_low))
        return stochastic
    
    def _calculate_williams(self, high: pd.Series, low: pd.Series, close: pd.Series, period: int) -> pd.Series:
        """Calculate Williams %R."""
        highest_high = high.rolling(window=period).max()
        lowest_low = low.rolling(window=period).min()
        williams = -100 * ((highest_high - close) / (highest_high - lowest_low))
        return williams
    
    def _score_rsi(self, rsi: float) -> float:
        """Score based on RSI value."""
        if pd.isna(rsi):
            return 50
        # RSI > 70 = Overbought, RSI < 30 = Oversold
        if rsi > 70:
            return 70  # Overbought (not necessarily bearish)
        elif rsi < 30:
            return 30  # Oversold (not necessarily bullish)
        else:
            # Map 30-70 to 0-100
            return ((rsi - 30) / 40) * 100
    
    def _score_roc(self, roc: float) -> float:
        """Score based on ROC value."""
        if pd.isna(roc):
            return 50
        # Map ROC to 0-100 (assume max ±20%)
        normalized = (roc / 20) * 50
        return max(0, min(100, 50 + normalized))
    
    def _score_stochastic(self, stochastic: float) -> float:
        """Score based on Stochastic value."""
        if pd.isna(stochastic):
            return 50
        # Stochastic > 80 = Overbought, < 20 = Oversold
        if stochastic > 80:
            return 70
        elif stochastic < 20:
            return 30
        else:
            return ((stochastic - 20) / 60) * 100
    
    def _score_williams(self, williams: float) -> float:
        """Score based on Williams %R value."""
        if pd.isna(williams):
            return 50
        # Williams > -20 = Overbought, < -80 = Oversold
        # Convert -100 to 0, 0 to 100
        return max(0, min(100, 50 + (williams / 2)))
