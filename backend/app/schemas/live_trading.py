from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from decimal import Decimal

class LiveAccountCreate(BaseModel):
    exchange_account_id: str
    initial_capital: Decimal = Field(..., description="Starting capital")
    protected_capital: Decimal = Field(..., description="Protected capital (cannot be traded)")

class LiveAccountResponse(BaseModel):
    id: str
    initial_capital: Decimal
    protected_capital: Decimal
    trading_capital: Decimal
    reserved_capital: Decimal
    realized_profit: Decimal
    unrealized_profit: Decimal
    total_pnl: Decimal
    is_active: bool
    is_paused: bool
    paused_reason: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

class LivePositionResponse(BaseModel):
    id: str
    symbol: str
    side: str
    entry_price: Decimal
    current_price: Optional[Decimal]
    quantity: Decimal
    notional_value: Decimal
    unrealized_pnl: Decimal
    realized_pnl: Decimal
    stop_loss_price: Optional[Decimal]
    take_profit_price: Optional[Decimal]
    risk_percent: Optional[Decimal]
    ai_confidence: Optional[Decimal]
    ai_reasoning: Optional[str]
    status: str
    opened_at: datetime
    closed_at: Optional[datetime]

    class Config:
        from_attributes = True

class LiveTradeResponse(BaseModel):
    id: str
    symbol: str
    side: str
    order_type: str
    quantity: Decimal
    price: Optional[Decimal]
    executed_price: Optional[Decimal]
    executed_quantity: Optional[Decimal]
    status: str
    fee: Decimal
    fee_currency: str
    placed_at: datetime
    executed_at: Optional[datetime]

    class Config:
        from_attributes = True

class ExecuteTradeRequest(BaseModel):
    symbol: str
    side: str  # LONG, SHORT
    entry_price: Optional[Decimal]
    quantity: Decimal
    stop_loss_price: Optional[Decimal]
    take_profit_price: Optional[Decimal]
    ai_confidence: Optional[Decimal]
    ai_reasoning: Optional[str]

class ClosePositionRequest(BaseModel):
    position_id: str
    close_price: Optional[Decimal]
