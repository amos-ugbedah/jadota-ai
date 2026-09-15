"""
AI Settings Pydantic Schemas - Professional Trading Configuration
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

# ============================================
# STRATEGY INFO SCHEMA
# ============================================
class StrategyInfo(BaseModel):
    type: str
    label: str
    description: str
    icon: str
    risk_level: str
    settings: dict

# ============================================
# STRATEGY PRESET SCHEMA
# ============================================
class StrategyPreset(BaseModel):
    type: str
    label: str
    description: str
    icon: str
    risk_level: str
    settings: dict

# ============================================
# AI SETTINGS BASE SCHEMA
# ============================================
class AISettingsBase(BaseModel):
    confidence_threshold: float = Field(70.0, ge=50, le=90)
    strategy_type: str = Field('balanced')
    
    # 🔥 PER-TRADE AMOUNT
    trade_amount: float = Field(25.0, ge=1, le=10000)
    
    stop_loss_percent: float = Field(2.0, ge=0.5, le=10)
    take_profit_percent: float = Field(4.0, ge=1, le=20)
    max_daily_loss: float = Field(5.0, ge=0.5, le=30)
    max_drawdown: float = Field(15.0, ge=5, le=50)
    max_positions: int = Field(5, ge=1, le=20)
    risk_per_trade: float = Field(2.0, ge=0.5, le=5)
    position_size_multiplier: float = Field(1.0, ge=0.1, le=3.0)
    symbols: List[str] = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'BNB/USDT']
    auto_trade_enabled: bool = False
    max_trades_per_day: int = Field(10, ge=1, le=50)

class AISettingsCreate(AISettingsBase):
    pass

class AISettingsUpdate(BaseModel):
    confidence_threshold: Optional[float] = Field(None, ge=50, le=90)
    strategy_type: Optional[str] = None
    trade_amount: Optional[float] = Field(None, ge=1, le=10000)
    stop_loss_percent: Optional[float] = Field(None, ge=0.5, le=10)
    take_profit_percent: Optional[float] = Field(None, ge=1, le=20)
    max_daily_loss: Optional[float] = Field(None, ge=0.5, le=30)
    max_drawdown: Optional[float] = Field(None, ge=5, le=50)
    max_positions: Optional[int] = Field(None, ge=1, le=20)
    risk_per_trade: Optional[float] = Field(None, ge=0.5, le=5)
    position_size_multiplier: Optional[float] = Field(None, ge=0.1, le=3.0)
    symbols: Optional[List[str]] = None
    auto_trade_enabled: Optional[bool] = None
    max_trades_per_day: Optional[int] = Field(None, ge=1, le=50)

class AISettingsResponse(AISettingsBase):
    id: str
    user_id: str
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    total_pnl: float = 0.0
    best_trade: float = 0.0
    worst_trade: float = 0.0
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True