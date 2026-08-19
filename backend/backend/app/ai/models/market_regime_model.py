import pandas as pd
import numpy as np
from typing import Dict, Any
from ..base_model import BaseModel

class MarketRegimeModel(BaseModel):
    """
    Market regime detection using:
    - Trend strength
    - Volatility regime
    - Volume analysis
    - Market state classification
    """
    
    def __init__(self):
        super().__init__("Market Regime Model")
        self.regimes = ['RANGING', 'TRENDING_UP', 'TRENDING_DOWN', 'HIGH_VOLATILITY']
    
    async def calculate(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Calculate market regime."""
        close = data['close']
        high = data['high']
        low = data['low']
        volume = data['volume'] if 'volume' in data else None
        
        # Calculate indicators
        trend_strength = self._calculate_trend_strength(close)
        volatility_regime = self._calculate_volatility_regime(close)
        volume_profile = self._calculate_volume_profile(volume, close) if volume is not None else 50
        
        # Determine regime
        regime, confidence = self._determine_regime(trend_strength, volatility_regime, volume_profile)
        
        self.last_score = confidence
        self.last_update = pd.Timestamp.now()
        
        return {
            'model': self.name,
            'regime': regime,
            'confidence': confidence,
            'components': {
                'trend_strength': trend_strength,
                'volatility_regime': volatility_regime,
                'volume_profile': volume_profile
            },
            'timestamp': self.last_update.isoformat()
        }
    
    def _calculate_trend_strength(self, data: pd.Series) -> float:
        """Calculate trend strength."""
        # Use ADX as trend strength indicator
        # Simplified: compare price to moving averages
        sma_50 = data.rolling(window=50).mean()
        sma_200 = data.rolling(window=200).mean()
        
        latest_close = data.iloc[-1]
        latest_sma_50 = sma_50.iloc[-1] if len(sma_50) > 0 else latest_close
        latest_sma_200 = sma_200.iloc[-1] if len(sma_200) > 0 else latest_close
        
        # Score based on price position
        if latest_close > latest_sma_50 > latest_sma_200:
            return 80  # Strong uptrend
        elif latest_close < latest_sma_50 < latest_sma_200:
            return 80  # Strong downtrend
        elif abs(latest_close - latest_sma_50) / latest_sma_50 < 0.02:
            return 20  # Ranging
        else:
            return 50  # Moderate trend
    
    def _calculate_volatility_regime(self, data: pd.Series) -> float:
        """Calculate volatility regime."""
        returns = data.pct_change()
        recent_vol = returns.tail(20).std()
        vol_ratio = recent_vol / returns.std()
        
        if vol_ratio > 1.5:
            return 80  # High volatility
        elif vol_ratio > 1.0:
            return 60  # Above average
        elif vol_ratio > 0.5:
            return 40  # Below average
        else:
            return 20  # Low volatility
    
    def _calculate_volume_profile(self, volume: pd.Series, price: pd.Series) -> float:
        """Calculate volume profile."""
        avg_volume = volume.rolling(window=20).mean()
        current_volume = volume.iloc[-1]
        avg_price = price.rolling(window=20).mean()
        current_price = price.iloc[-1]
        
        # Volume relative to average
        vol_ratio = current_volume / avg_volume.iloc[-1] if len(avg_volume) > 0 else 1
        
        # Price vs volume
        if vol_ratio > 1.5 and current_price > avg_price.iloc[-1]:
            return 80  # High volume, price up
        elif vol_ratio > 1.5 and current_price < avg_price.iloc[-1]:
            return 80  # High volume, price down
        elif vol_ratio < 0.5:
            return 30  # Low volume
        else:
            return 50  # Normal
    
    def _determine_regime(self, trend_strength: float, volatility_regime: float, volume_profile: float) -> tuple:
        """Determine market regime."""
        # Weighted score
        regime_score = (trend_strength * 0.4 + volatility_regime * 0.3 + volume_profile * 0.3)
        
        if regime_score > 70:
            if trend_strength > 60:
                return "TRENDING_UP", regime_score
            else:
                return "HIGH_VOLATILITY", regime_score
        elif regime_score < 30:
            return "RANGING", regime_score
        else:
            if trend_strength > 60:
                return "TRENDING_UP", regime_score
            elif trend_strength < 40:
                return "TRENDING_DOWN", regime_score
            else:
                return "RANGING", regime_score
