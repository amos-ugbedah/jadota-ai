"""Pydantic schemas for the exchange (Bitget) credential endpoints."""

from pydantic import BaseModel, Field
from typing import Optional
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