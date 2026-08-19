from typing import Dict, Any, List, Optional
from datetime import datetime
import pandas as pd
import numpy as np
from decimal import Decimal
import logging

from .models.trend_model import TrendModel
from .models.momentum_model import MomentumModel
from .models.volatility_model import VolatilityModel
from .models.market_regime_model import MarketRegimeModel

logger = logging.getLogger(__name__)

class ConsensusEngine:
    """
    Combines multiple models to generate trading signals.
    """
    
    def __init__(self):
        self.models = {
            'trend': TrendModel(),
            'momentum': MomentumModel(),
            'volatility': VolatilityModel(),
            'regime': MarketRegimeModel()
        }
        self.weights = {
            'trend': 0.35,
            'momentum': 0.30,
            'volatility': 0.15,
            'regime': 0.20
        }
        self.min_confidence = 60
        self.min_opportunity_score = 70
    
    async def analyze(self, data: pd.DataFrame, symbol: str) -> Dict[str, Any]:
        """
        Analyze market data and generate trading signal.
        
        Args:
            data: DataFrame with OHLCV data
            symbol: Trading symbol
            
        Returns:
            Dict with analysis results
        """
        try:
            # Run all models
            results = {}
            for name, model in self.models.items():
                try:
                    result = await model.calculate(data)
                    results[name] = result
                except Exception as e:
                    logger.error(f"Error in {name} model: {e}")
                    results[name] = {
                        'score': 50,
                        'direction': 'NEUTRAL',
                        'confidence': 0
                    }
            
            # Calculate consensus score
            consensus_score = self._calculate_consensus(results)
            
            # Determine direction
            direction, confidence = self._determine_direction(results, consensus_score)
            
            # Calculate risk/reward
            risk_reward = self._calculate_risk_reward(data, direction)
            
            # Generate recommendation
            opportunity_score = self._calculate_opportunity_score(
                consensus_score, confidence, risk_reward
            )
            
            should_trade = (
                opportunity_score >= self.min_opportunity_score and
                confidence >= self.min_confidence
            )
            
            return {
                'symbol': symbol,
                'timestamp': datetime.utcnow().isoformat(),
                'consensus_score': consensus_score,
                'direction': direction,
                'confidence': confidence,
                'opportunity_score': opportunity_score,
                'risk_reward_ratio': risk_reward,
                'should_trade': should_trade,
                'models': results,
                'recommendation': self._generate_recommendation(
                    opportunity_score, direction, confidence
                )
            }
            
        except Exception as e:
            logger.error(f"Error in consensus engine: {e}")
            return {
                'symbol': symbol,
                'timestamp': datetime.utcnow().isoformat(),
                'error': str(e),
                'should_trade': False
            }
    
    def _calculate_consensus(self, results: Dict[str, Any]) -> float:
        """Calculate weighted consensus score."""
        total_score = 0
        total_weight = 0
        
        for name, result in results.items():
            if name in self.weights and 'score' in result:
                weight = self.weights[name]
                score = result['score']
                total_score += score * weight
                total_weight += weight
        
        if total_weight > 0:
            return total_score / total_weight
        return 50
    
    def _determine_direction(self, results: Dict[str, Any], consensus_score: float) -> tuple:
        """Determine trading direction."""
        directions = []
        for name, result in results.items():
            if 'direction' in result and result['direction'] != 'NEUTRAL':
                directions.append(result['direction'])
        
        # Count bullish vs bearish
        bullish = directions.count('BULLISH')
        bearish = directions.count('BEARISH')
        
        if bullish > bearish:
            direction = 'LONG'
            confidence = min(100, 50 + (bullish / len(directions)) * 50)
        elif bearish > bullish:
            direction = 'SHORT'
            confidence = min(100, 50 + (bearish / len(directions)) * 50)
        else:
            direction = 'NEUTRAL'
            confidence = 50
        
        return direction, confidence
    
    def _calculate_risk_reward(self, data: pd.DataFrame, direction: str) -> float:
        """Calculate risk/reward ratio."""
        close = data['close']
        latest_price = close.iloc[-1]
        
        # Calculate volatility based on ATR
        high = data['high']
        low = data['low']
        atr = self._calculate_atr(high, low, close, 14)
        
        if len(atr) == 0 or pd.isna(atr.iloc[-1]):
            return 1.5
        
        atr_value = atr.iloc[-1]
        
        # Calculate potential profit and loss
        if direction == 'LONG':
            # 2:1 risk/reward ratio target
            reward_target = latest_price + (atr_value * 2)
            stop_loss = latest_price - atr_value
        elif direction == 'SHORT':
            reward_target = latest_price - (atr_value * 2)
            stop_loss = latest_price + atr_value
        else:
            return 1.5
        
        # Calculate ratio
        risk = abs(latest_price - stop_loss)
        reward = abs(reward_target - latest_price)
        
        if risk > 0:
            return round(reward / risk, 2)
        return 1.5
    
    def _calculate_atr(self, high: pd.Series, low: pd.Series, close: pd.Series, period: int) -> pd.Series:
        """Calculate Average True Range."""
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        return tr.rolling(window=period).mean()
    
    def _calculate_opportunity_score(self, consensus: float, confidence: float, risk_reward: float) -> float:
        """Calculate overall opportunity score."""
        # Consensus (0-100) * 0.4
        # Confidence (0-100) * 0.3
        # Risk/Reward (scaled to 0-100) * 0.3
        rr_score = min(100, risk_reward / 3 * 100)
        
        score = (consensus * 0.4) + (confidence * 0.3) + (rr_score * 0.3)
        return round(score, 2)
    
    def _generate_recommendation(self, score: float, direction: str, confidence: float) -> str:
        """Generate human-readable recommendation."""
        if score < 50:
            return f"❌ No trade - Opportunity score {score}% (needs 70%)"
        elif score < 70:
            return f"⚠️ Weak signal - Opportunity score {score}% (needs 70%)"
        elif direction == 'NEUTRAL':
            return f"⚠️ Mixed signals - Wait for clearer direction"
        else:
            return f"✅ {direction} signal - Confidence {confidence}%, Opportunity {score}%"
    
    def get_model_status(self) -> Dict[str, Any]:
        """Get status of all models."""
        return {
            name: {
                'name': model.name,
                'last_score': model.last_score,
                'last_update': model.last_update.isoformat() if model.last_update else None
            }
            for name, model in self.models.items()
        }

# Create singleton
consensus_engine = ConsensusEngine()
