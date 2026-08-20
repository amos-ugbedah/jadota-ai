from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from decimal import Decimal

class RiskSettingsBase(BaseModel):
    max_risk_per_trade: Decimal = Field(2.0, description="2% of capital per trade")
    max_risk_per_day: Decimal = Field(5.0, description="5% daily loss limit")
    max_risk_per_week: Decimal = Field(10.0, description="10% weekly loss limit")
    max_drawdown: Decimal = Field(15.0, description="15% max drawdown")
    max_simultaneous_trades: int = Field(5, description="Max simultaneous trades")
    max_position_size_pct: Decimal = Field(20.0, description="20% of capital per position")
    default_stop_loss_pct: Decimal = Field(2.0, description="2% default stop loss")
    trailing_stop_enabled: bool = True
    trailing_stop_pct: Decimal = Field(1.0, description="1% trailing stop")
    correlation_limit: Decimal = Field(0.7, description="Don't trade if correlation > 0.7")
    protected_capital_pct: Decimal = Field(50.0, description="50% protected capital")
    emergency_shutdown_enabled: bool = True
    auto_shutdown_after_events: int = Field(3, description="Shutdown after 3 risk events")

class RiskSettingsUpdate(BaseModel):
    max_risk_per_trade: Optional[Decimal] = None
    max_risk_per_day: Optional[Decimal] = None
    max_risk_per_week: Optional[Decimal] = None
    max_drawdown: Optional[Decimal] = None
    max_simultaneous_trades: Optional[int] = None
    max_position_size_pct: Optional[Decimal] = None
    default_stop_loss_pct: Optional[Decimal] = None
    trailing_stop_enabled: Optional[bool] = None
    trailing_stop_pct: Optional[Decimal] = None
    correlation_limit: Optional[Decimal] = None
    protected_capital_pct: Optional[Decimal] = None
    emergency_shutdown_enabled: Optional[bool] = None
    auto_shutdown_after_events: Optional[int] = None

class RiskSettingsResponse(BaseModel):
    id: str
    user_id: str
    max_risk_per_trade: Decimal
    max_risk_per_day: Decimal
    max_risk_per_week: Decimal
    max_drawdown: Decimal
    max_simultaneous_trades: int
    max_position_size_pct: Decimal
    default_stop_loss_pct: Decimal
    trailing_stop_enabled: bool
    trailing_stop_pct: Decimal
    correlation_limit: Decimal
    protected_capital_pct: Decimal
    emergency_shutdown_enabled: bool
    auto_shutdown_after_events: int
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

class CapitalTrackerResponse(BaseModel):
    id: str
    user_id: str
    initial_capital: Decimal
    protected_capital: Decimal
    trading_capital: Decimal
    reserve_capital: Decimal
    realized_profit: Decimal
    unrealized_profit: Decimal
    total_pnl: Decimal
    daily_pnl: Decimal
    daily_start_capital: Decimal
    daily_loss_count: int
    weekly_pnl: Decimal
    weekly_start_capital: Decimal
    weekly_loss_count: int
    is_paused: bool
    paused_reason: Optional[str]
    paused_at: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

class RiskEventResponse(BaseModel):
    id: str
    user_id: str
    event_type: str
    severity: str
    description: Optional[str]
    metric_value: Optional[Decimal]
    threshold: Optional[Decimal]
    action_taken: Optional[str]
    resolved_at: Optional[datetime]
    resolution_notes: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

class PositionSizeRequest(BaseModel):
    capital: Decimal = Field(..., description="Available capital")
    risk_percent: Decimal = Field(2.0, description="Risk per trade as % of capital")
    stop_loss_pct: Decimal = Field(2.0, description="Stop loss as % of entry price")
    entry_price: Decimal = Field(..., description="Entry price")
    
class PositionSizeResponse(BaseModel):
    position_size: Decimal
    risk_amount: Decimal
    stop_loss_price: Decimal
    take_profit_1: Decimal
    take_profit_2: Decimal
    take_profit_3: Decimal
    max_loss: Decimal

class RiskCheckRequest(BaseModel):
    symbol: str
    side: str  # LONG, SHORT
    entry_price: Decimal
    stop_loss_price: Decimal
    position_size: Decimal
    
class RiskCheckResponse(BaseModel):
    is_allowed: bool
    reason: Optional[str]
    risk_score: Decimal
    warnings: List[str]
