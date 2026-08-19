from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
import pandas as pd

from ...core.database import get_db
from ...models.market_data import OHLCV
from ...ai.consensus_engine import consensus_engine
from ...api.dependencies import get_current_user
from ...models.user import User

router = APIRouter(prefix="/ai", tags=["AI Trading Engine"])

@router.post("/analyze/{symbol}")
async def analyze_symbol(
    symbol: str,
    interval: str = Query("1h", description="Timeframe: 1m, 5m, 15m, 1h, 4h, 1d"),
    limit: int = Query(100, description="Number of candles to analyze"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Analyze a symbol and generate trading signal.
    """
    # Get OHLCV data
    ohlcv_data = db.query(OHLCV).filter(
        OHLCV.symbol == symbol,
        OHLCV.interval == interval
    ).order_by(OHLCV.timestamp.asc()).limit(limit).all()
    
    if len(ohlcv_data) < 50:
        raise HTTPException(
            status_code=404,
            detail=f"Not enough data for {symbol}. Need at least 50 candles."
        )
    
    # Convert to DataFrame
    data = pd.DataFrame([{
        'timestamp': d.timestamp,
        'open': float(d.open),
        'high': float(d.high),
        'low': float(d.low),
        'close': float(d.close),
        'volume': float(d.volume)
    } for d in ohlcv_data])
    
    if data.empty:
        raise HTTPException(
            status_code=404,
            detail=f"No OHLCV data found for {symbol}"
        )
    
    # Run analysis
    result = await consensus_engine.analyze(data, symbol)
    
    return result

@router.get("/status")
async def get_ai_status(
    current_user: User = Depends(get_current_user),
):
    """
    Get AI engine status.
    """
    return {
        'engine': 'JADOTA AI Trading Engine',
        'version': '1.0.0',
        'models': consensus_engine.get_model_status(),
        'min_opportunity_score': consensus_engine.min_opportunity_score,
        'min_confidence': consensus_engine.min_confidence
    }

@router.get("/supported-symbols")
async def get_supported_symbols():
    """
    Get list of supported symbols.
    """
    return {
        'symbols': ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'BNBUSDT', 'XRPUSDT', 'DOGEUSDT', 'ADAUSDT'],
        'description': 'Supported trading pairs'
    }

@router.post("/test-signal")
async def test_signal(
    symbol: str = Query("BTCUSDT"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Generate a test signal with simulated data.
    """
    # Generate simulated data
    import numpy as np
    np.random.seed(42)
    
    base_price = 50000 if symbol == "BTCUSDT" else 3000
    prices = base_price * (1 + np.random.randn(100) * 0.02)
    prices = np.maximum(prices, prices[0] * 0.7)
    prices = np.minimum(prices, prices[0] * 1.3)
    
    data = pd.DataFrame({
        'timestamp': [datetime.utcnow() - timedelta(hours=i) for i in range(99, -1, -1)],
        'open': prices[:-1],
        'high': prices[:-1] * (1 + np.random.rand(99) * 0.01),
        'low': prices[:-1] * (1 - np.random.rand(99) * 0.01),
        'close': prices[1:],
        'volume': np.random.rand(99) * 1000
    })
    
    result = await consensus_engine.analyze(data, symbol)
    
    return {
        'message': 'Test signal generated with simulated data',
        'signal': result
    }
