from pydantic import BaseModel, Field, SecretStr
from typing import Optional, List
from datetime import datetime
from decimal import Decimal

class ExchangeAccountCreate(BaseModel):
    api_key: str = Field(..., description="API Key from Bitget")
    api_secret: SecretStr = Field(..., description="API Secret from Bitget")
    passphrase: Optional[str] = Field(None, description="Passphrase (if set)")
    ip_whitelist: Optional[List[str]] = Field(default=[], description="Whitelisted IPs")

class ExchangeAccountResponse(BaseModel):
    id: str
    exchange: str
    api_key: str
    permissions_read: bool
    permissions_trade: bool
    permissions_withdraw: bool
    is_active: bool
    is_verified: bool
    last_verified_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True

class ExchangeBalanceResponse(BaseModel):
    asset: str
    total: Decimal
    free: Decimal
    used: Decimal
    updated_at: datetime

    class Config:
        from_attributes = True

class ExchangeOrderCreate(BaseModel):
    symbol: str = Field(..., description="Trading pair (e.g., BTCUSDT)")
    side: str = Field(..., description="BUY or SELL")
    order_type: str = Field(..., description="MARKET or LIMIT")
    quantity: Decimal = Field(..., description="Order quantity")
    price: Optional[Decimal] = Field(None, description="Price for limit orders")
    stop_price: Optional[Decimal] = Field(None, description="Stop price for stop orders")

class ExchangeOrderResponse(BaseModel):
    id: str
    symbol: str
    side: str
    order_type: str
    quantity: Decimal
    price: Optional[Decimal]
    executed_quantity: Decimal
    executed_price: Optional[Decimal]
    avg_price: Optional[Decimal]
    status: str
    fee: Optional[Decimal]
    fee_currency: Optional[str]
    placed_at: datetime
    executed_at: Optional[datetime]

    class Config:
        from_attributes = True

class ExchangeOrderCancelResponse(BaseModel):
    order_id: str
    status: str
    message: str
