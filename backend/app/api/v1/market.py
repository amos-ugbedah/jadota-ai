from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from decimal import Decimal
from ...core.database import get_db
from ...schemas.market import (
    OHLCVResponse, CurrentPriceResponse, 
    PriceHistoryRequest, SymbolInfo
)
from ...services.market_service import market_service
from ...api.dependencies import get_current_user
from ...models.user import User

router = APIRouter(prefix="/market", tags=["Market Data"])

@router.get("/symbols", response_model=List[str])
async def get_supported_symbols():
    """Get list of supported trading symbols."""
    return [s.replace('/', '') for s in market_service.SUPPORTED_SYMBOLS]

@router.get("/price/{symbol}", response_model=CurrentPriceResponse)
async def get_current_price(
    symbol: str,
    db: Session = Depends(get_db),
):
    """Get current price for a symbol."""
    # Try to get from database first
    price = market_service.get_latest_price(db, symbol)
    
    if not price or (datetime.utcnow() - price.updated_at).seconds > 60:
        # Price is stale, fetch new one
        await market_service.update_current_price(db, symbol)
        price = market_service.get_latest_price(db, symbol)
    
    if not price:
        raise HTTPException(
            status_code=404,
            detail=f"Price not available for {symbol}"
        )
    
    return price

@router.get("/ohlcv/{symbol}", response_model=List[OHLCVResponse])
async def get_ohlcv(
    symbol: str,
    interval: str = Query("1h", description="1m, 5m, 15m, 1h, 4h, 1d, 1w"),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """Get historical OHLCV data."""
    request = PriceHistoryRequest(
        symbol=symbol,
        interval=interval,
        limit=limit
    )
    data = market_service.get_historical_ohlcv(db, request)
    return data

@router.post("/ohlcv/refresh")
async def refresh_ohlcv(
    symbol: str,
    interval: str = Query("1h"),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """Fetch and store fresh OHLCV data."""
    count = await market_service.fetch_and_store_ohlcv(
        db, symbol, interval, limit
    )
    return {
        "message": f"Refreshed {count} new OHLCV records for {symbol}",
        "count": count
    }

@router.post("/prices/refresh")
async def refresh_all_prices(
    db: Session = Depends(get_db),
):
    """Refresh all current prices."""
    results = await market_service.update_all_prices(db)
    return {
        "message": "Prices updated",
        "results": results
    }
