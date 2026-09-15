import pandas as pd
import numpy as np
from typing import Dict, Any
from ..base_model import BaseModel

class TrendModel(BaseModel):
    """
    Trend detection using EMAs, MACD, ADX, and moving averages.
    """
    
    def __init__(self):
        super().__init__("Trend Model")
        self.weights = {
            'ema_cross': 0.30,
            'macd': 0.30,
            'adx': 0.20,
            'sma_alignment': 0.20
        }
    
    async def calculate(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Calculate trend score."""
        close = data['close']
        high = data['high']
        low = data['low']
        
        # Calculate indicators
        ema_9 = self.get_ema(close, 9)
        ema_21 = self.get_ema(close, 21)
        ema_50 = self.get_ema(close, 50)
        
        macd_data = self.get_macd(close)
        
        adx = self._calculate_adx(high, low, close, 14)
        
        sma_alignment = self._calculate_sma_alignment(close)
        
        # Score each component
        ema_score = self._score_ema_cross(ema_9, ema_21, ema_50, close)
        macd_score = self._score_macd(macd_data)
        adx_score = self._score_adx(adx)
        sma_score = self._score_sma_alignment(sma_alignment)
        
        total_score = (
            ema_score * self.weights['ema_cross'] +
            macd_score * self.weights['macd'] +
            adx_score * self.weights['adx'] +
            sma_score * self.weights['sma_alignment']
        )
        
        # Determine direction
        if total_score > 65:
            direction = "BULLISH"
            confidence = min(100, (total_score - 50) * 2)
        elif total_score < 35:
            direction = "BEARISH"
            confidence = min(100, (50 - total_score) * 2)
        else:
            direction = "NEUTRAL"
            confidence = 50
        
        self.last_score = total_score
        self.last_update = pd.Timestamp.now()
        self.last_result = {
            'score': total_score,
            'direction': direction,
            'confidence': confidence,
            'components': {
                'ema_cross': ema_score,
                'macd': macd_score,
                'adx': adx_score,
                'sma_alignment': sma_score
            }
        }
        
        return self.last_result
    
    def _calculate_adx(self, high: pd.Series, low: pd.Series, close: pd.Series, period: int) -> pd.Series:
        """Calculate Average Directional Index."""
        tr = self.get_atr(high, low, close, period)
        
        up_move = high - high.shift()
        down_move = low.shift() - low
        
        plus_dm = up_move.where((up_move > down_move) & (up_move > 0), 0)
        minus_dm = down_move.where((down_move > up_move) & (down_move > 0), 0)
        
        plus_di = 100 * (plus_dm.rolling(period).mean() / tr)
        minus_di = 100 * (minus_dm.rolling(period).mean() / tr)
        
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
        adx = dx.rolling(period).mean()
        
        return adx
    
    def _calculate_sma_alignment(self, close: pd.Series) -> float:
        """Calculate SMA alignment score."""
        sma_20 = self.get_sma(close, 20)
        sma_50 = self.get_sma(close, 50)
        sma_200 = self.get_sma(close, 200)
        
        if len(sma_20) == 0 or len(sma_50) == 0 or len(sma_200) == 0:
            return 50
        
        last_close = close.iloc[-1]
        last_sma_20 = sma_20.iloc[-1]
        last_sma_50 = sma_50.iloc[-1]
        last_sma_200 = sma_200.iloc[-1]
        
        if pd.isna(last_sma_20) or pd.isna(last_sma_50) or pd.isna(last_sma_200):
            return 50
        
        if last_close > last_sma_20 > last_sma_50 > last_sma_200:
            return 80
        elif last_close < last_sma_20 < last_sma_50 < last_sma_200:
            return 20
        return 50
    
    def _score_ema_cross(self, ema_9: pd.Series, ema_21: pd.Series, ema_50: pd.Series, close: pd.Series) -> float:
        """Score EMA cross signals."""
        if len(ema_9) < 2 or len(ema_21) < 2:
            return 50
        
        last_ema_9 = ema_9.iloc[-1]
        last_ema_21 = ema_21.iloc[-1]
        last_ema_50 = ema_50.iloc[-1]
        last_close = close.iloc[-1]
        
        if pd.isna(last_ema_9) or pd.isna(last_ema_21) or pd.isna(last_ema_50):
            return 50
        
        # EMA 9/21 cross
        cross_9_21 = last_ema_9 - last_ema_21
        prev_cross_9_21 = ema_9.iloc[-2] - ema_21.iloc[-2]
        
        score = 50
        if cross_9_21 > 0 and prev_cross_9_21 <= 0:
            score += 20
        elif cross_9_21 < 0 and prev_cross_9_21 >= 0:
            score -= 20
        
        # EMA 21/50 alignment
        if last_ema_9 > last_ema_21 > last_ema_50:
            score += 15
        elif last_ema_9 < last_ema_21 < last_ema_50:
            score -= 15
        
        # Price vs EMAs
        if last_close > last_ema_9 > last_ema_21:
            score += 15
        elif last_close < last_ema_9 < last_ema_21:
            score -= 15
        
        return max(0, min(100, score))
    
    def _score_macd(self, macd_data: Dict[str, pd.Series]) -> float:
        """Score MACD signal."""
        macd = macd_data['macd']
        signal = macd_data['signal']
        
        if len(macd) < 2 or len(signal) < 2:
            return 50
        
        last_macd = macd.iloc[-1]
        last_signal = signal.iloc[-1]
        prev_macd = macd.iloc[-2]
        prev_signal = signal.iloc[-2]
        
        if pd.isna(last_macd) or pd.isna(last_signal):
            return 50
        
        score = 50
        if last_macd > last_signal and prev_macd <= prev_signal:
            score += 25
        elif last_macd < last_signal and prev_macd >= prev_signal:
            score -= 25
        
        if last_macd > 0:
            score += 10
        elif last_macd < 0:
            score -= 10
        
        return max(0, min(100, score))
    
    def _score_adx(self, adx: pd.Series) -> float:
        """Score ADX trend strength."""
        if len(adx) == 0 or pd.isna(adx.iloc[-1]):
            return 50
        
        last_adx = adx.iloc[-1]
        
        if last_adx > 40:
            return 80
        elif last_adx > 25:
            return 65
        elif last_adx > 20:
            return 50
        else:
            return 30
    
    def _score_sma_alignment(self, alignment: float) -> float:
        """Score SMA alignment."""
        return alignment