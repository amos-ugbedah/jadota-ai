from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from decimal import Decimal

class DemoAccountResponse(BaseModel):
    id: str
    initial_balance: Decimal
    current_balance: Decimal
    total_pnl: Decimal
    total_return: Decimal
    win_rate: Decimal
    profit_factor: Decimal
    max_drawdown: Decimal
    sharpe_ratio: Decimal
    total_trades: int
    winning_trades: int
    losing_trades: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class CreatePosition(BaseModel):
    symbol: str
    side: str  # LONG, SHORT
    quantity: Decimal
    entry_price: Decimal
    stop_loss_price: Optional[Decimal] = None
    take_profit_price: Optional[Decimal] = None
    ai_confidence: Optional[Decimal] = None
    ai_reasoning: Optional[str] = None

class PositionResponse(BaseModel):
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

class CreateTrade(BaseModel):
    symbol: str
    side: str  # BUY, SELL
    order_type: str  # MARKET, LIMIT
    quantity: Decimal
    price: Optional[Decimal] = None

class TradeResponse(BaseModel):
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
    placed_at: datetime
    executed_at: Optional[datetime]

    class Config:
        from_attributes = True

class PerformanceMetrics(BaseModel):
    total_pnl: Decimal
    total_return: Decimal
    win_rate: Decimal
    profit_factor: Decimal
    max_drawdown: Decimal
    sharpe_ratio: Decimal
    total_trades: int
    winning_trades: int
    losing_trades: int
