from sqlalchemy import Column, String, Boolean, DateTime, Integer, Float, DECIMAL, ForeignKey, Text, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
from ..core.database import Base

class LiveAccount(Base):
    __tablename__ = "live_accounts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    exchange_account_id = Column(String(36), ForeignKey("exchange_accounts.id"), nullable=False)
    
    initial_capital = Column(DECIMAL(15, 2), nullable=False)
    protected_capital = Column(DECIMAL(15, 2), nullable=False)
    trading_capital = Column(DECIMAL(15, 2), nullable=False)
    reserved_capital = Column(DECIMAL(15, 2), default=0)
    
    realized_profit = Column(DECIMAL(15, 2), default=0)
    unrealized_profit = Column(DECIMAL(15, 2), default=0)
    total_pnl = Column(DECIMAL(15, 2), default=0)
    
    is_active = Column(Boolean, default=True)
    is_paused = Column(Boolean, default=False)
    paused_reason = Column(Text)
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    
    user = relationship("User")
    exchange_account = relationship("ExchangeAccount")

class LivePosition(Base):
    __tablename__ = "live_positions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    live_account_id = Column(String(36), ForeignKey("live_accounts.id"), nullable=False)
    
    symbol = Column(String(20), nullable=False)
    side = Column(String(10), nullable=False)
    
    entry_price = Column(DECIMAL(15, 8), nullable=False)
    current_price = Column(DECIMAL(15, 8))
    quantity = Column(DECIMAL(15, 8), nullable=False)
    notional_value = Column(DECIMAL(15, 2), nullable=False)
    
    unrealized_pnl = Column(DECIMAL(15, 2), default=0)
    realized_pnl = Column(DECIMAL(15, 2), default=0)
    
    stop_loss_price = Column(DECIMAL(15, 8))
    take_profit_price = Column(DECIMAL(15, 8))
    
    risk_percent = Column(DECIMAL(5, 2))
    risk_amount = Column(DECIMAL(15, 2))
    
    ai_decision_id = Column(String(36))
    ai_confidence = Column(DECIMAL(5, 2))
    ai_reasoning = Column(Text)
    
    entry_order_id = Column(String(255))
    exit_order_id = Column(String(255))
    
    status = Column(String(20), default="OPEN")
    
    opened_at = Column(DateTime, server_default=func.now())
    closed_at = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    
    user = relationship("User")
    live_account = relationship("LiveAccount")

class LiveTrade(Base):
    __tablename__ = "live_trades"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    live_account_id = Column(String(36), ForeignKey("live_accounts.id"), nullable=False)
    position_id = Column(String(36), ForeignKey("live_positions.id"))
    
    symbol = Column(String(20), nullable=False)
    side = Column(String(10), nullable=False)
    order_type = Column(String(20), nullable=False)
    
    quantity = Column(DECIMAL(15, 8), nullable=False)
    price = Column(DECIMAL(15, 8))
    executed_price = Column(DECIMAL(15, 8))
    executed_quantity = Column(DECIMAL(15, 8))
    
    status = Column(String(20), default="PENDING")
    
    fee = Column(DECIMAL(15, 8), default=0)
    fee_currency = Column(String(10), default="USDT")
    
    exchange_order_id = Column(String(255))
    ai_decision_id = Column(String(36))
    
    placed_at = Column(DateTime, server_default=func.now())
    executed_at = Column(DateTime)
    cancelled_at = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    
    user = relationship("User")
    live_account = relationship("LiveAccount")
    position = relationship("LivePosition")
