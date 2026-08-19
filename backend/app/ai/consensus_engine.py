from typing import Dict, Any
from datetime import datetime
import pandas as pd
import numpy as np
import logging

# Use relative imports within the package
from .models.trend_model import TrendModel
from .models.momentum_model import MomentumModel
from .models.volatility_model import VolatilityModel
from .models.market_regime_model import MarketRegimeModel

logger = logging.getLogger(__name__)

class ConsensusEngine:
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
        try:
            results = {}
            for name, model in self.models.items():
                try:
                    result = await model.calculate(data)
                    results[name] = result
                except Exception as e:
                    logger.error(f"Error in {name} model: {e}")
                    results[name] = {'score': 50, 'direction': 'NEUTRAL', 'confidence': 0}
            
            consensus_score = self._calculate_consensus(results)
            direction, confidence = self._determine_direction(results, consensus_score)
            risk_reward = self._calculate_risk_reward(data, direction)
            opportunity_score = self._calculate_opportunity_score(consensus_score, confidence, risk_reward)
            
            should_trade = opportunity_score >= self.min_opportunity_score and confidence >= self.min_confidence
            
            return {
                'symbol': symbol,
                'timestamp': datetime.utcnow().isoformat(),
                'consensus_score': float(consensus_score),
                'direction': direction,
                'confidence': float(confidence),
                'opportunity_score': float(opportunity_score),
                'risk_reward_ratio': float(risk_reward),
                'should_trade': should_trade,
                'models': results,
                'recommendation': self._generate_recommendation(opportunity_score, direction, confidence)
            }
        except Exception as e:
            logger.error(f"Error in consensus engine: {e}")
            return {'symbol': symbol, 'timestamp': datetime.utcnow().isoformat(), 'error': str(e), 'should_trade': False}
    
    def _calculate_consensus(self, results: Dict[str, Any]) -> float:
        total_score = 0
        total_weight = 0
        for name, result in results.items():
            if name in self.weights and 'score' in result:
                total_score += result['score'] * self.weights[name]
                total_weight += self.weights[name]
        return total_score / total_weight if total_weight > 0 else 50
    
    def _determine_direction(self, results: Dict[str, Any], consensus_score: float) -> tuple:
        directions = []
        for name, result in results.items():
            if 'direction' in result and result['direction'] != 'NEUTRAL':
                directions.append(result['direction'])
        
        bullish = directions.count('BULLISH')
        bearish = directions.count('BEARISH')
        
        if bullish > bearish:
            return 'LONG', min(100, 50 + (bullish / max(1, len(directions))) * 50)
        elif bearish > bullish:
            return 'SHORT', min(100, 50 + (bearish / max(1, len(directions))) * 50)
        else:
            return 'NEUTRAL', 50
    
    def _calculate_risk_reward(self, data: pd.DataFrame, direction: str) -> float:
        close = data['close']
        latest_price = float(close.iloc[-1])
        high = data['high']
        low = data['low']
        
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=14).mean()
        
        if len(atr) == 0 or pd.isna(atr.iloc[-1]):
            return 1.5
        
        atr_value = float(atr.iloc[-1])
        
        if direction == 'LONG':
            stop_loss = latest_price - atr_value
            reward_target = latest_price + (atr_value * 2)
        elif direction == 'SHORT':
            stop_loss = latest_price + atr_value
            reward_target = latest_price - (atr_value * 2)
        else:
            return 1.5
        
        risk = abs(latest_price - stop_loss)
        reward = abs(reward_target - latest_price)
        return round(reward / risk, 2) if risk > 0 else 1.5
    
    def _calculate_opportunity_score(self, consensus: float, confidence: float, risk_reward: float) -> float:
        rr_score = min(100, (risk_reward / 3) * 100)
        return round((consensus * 0.4) + (confidence * 0.3) + (rr_score * 0.3), 2)
    
    def _generate_recommendation(self, score: float, direction: str, confidence: float) -> str:
        if score < 50:
            return f"❌ No trade - Opportunity score {score}% (needs 70%)"
        elif score < 70:
            return f"⚠️ Weak signal - Opportunity score {score}% (needs 70%)"
        elif direction == 'NEUTRAL':
            return "⚠️ Mixed signals - Wait for clearer direction"
        else:
            return f"✅ {direction} signal - Confidence {confidence}%, Opportunity {score}%"
    
    def get_model_status(self) -> Dict[str, Any]:
        status = {}
        for name, model in self.models.items():
            status[name] = {
                'name': model.name,
                'last_score': model.last_score,
                'last_update': model.last_update.isoformat() if model.last_update else None
            }
        return status

consensus_engine = ConsensusEngine()
