"""Pydantic schemas for the exchange (Bitget) credential endpoints."""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class BitgetConnectRequest(BaseModel):
    api_key: str = Field(..., min_length=10, max_length=200)
    api_secret: str = Field(..., min_length=10, max_length=200)
    passphrase: str = Field(..., min_length=4, max_length=100)


class ExchangeStatusResponse(BaseModel):
    connected: bool
    exchange: str = "bitget"
    api_key_masked: Optional[str] = None
    permissions: Optional[str] = None
    ip_whitelist: Optional[str] = None
    is_active: bool = False
    testnet: bool = False
    last_used_at: Optional[datetime] = None
    last_error: Optional[str] = None
    connected_at: Optional[datetime] = None


class ExchangeConnectResponse(BaseModel):
    success: bool
    message: str
    status: ExchangeStatusResponse


class ExchangeDisconnectResponse(BaseModel):
    success: bool
    message: str


# 🔥 Task #4c: balance endpoint shapes
class ExchangeBalanceItem(BaseModel):
    asset: str
    free: float
    used: float
    total: float


class ExchangeBalanceResponse(BaseModel):
    success: bool
    exchange: str = "bitget"
    testnet: bool = False
    balances: List[ExchangeBalanceItem]
    total_usdt_value: Optional[float] = None