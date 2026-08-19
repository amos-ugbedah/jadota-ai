from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from decimal import Decimal

class OHLCVResponse(BaseModel):
    id: str
    symbol: str
    exchange: str
    interval: str
    timestamp: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal
    vwap: Optional[Decimal]
    number_of_trades: Optional[int]

    class Config:
        from_attributes = True

class CurrentPriceResponse(BaseModel):
    symbol: str
    price: Decimal
    bid: Optional[Decimal]
    ask: Optional[Decimal]
    volume_24h: Optional[Decimal]
    high_24h: Optional[Decimal]
    low_24h: Optional[Decimal]
    updated_at: datetime

    class Config:
        from_attributes = True

class PriceHistoryRequest(BaseModel):
    symbol: str
    interval: str = "1h"  # 1m, 5m, 15m, 1h, 4h, 1d, 1w
    limit: int = 100
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

class SymbolInfo(BaseModel):
    symbol: str
    base_asset: str
    quote_asset: str
    min_quantity: Decimal
    max_quantity: Decimal
    tick_size: Decimal
    min_notional: Optional[Decimal]
