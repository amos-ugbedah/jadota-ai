from sqlalchemy import Column, String, Boolean, DateTime, Integer, Float, DECIMAL, ForeignKey, Text, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
from ..core.database import Base

class RiskEvent(Base):
    __tablename__ = "risk_events"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    
    event_type = Column(String(50), nullable=False)  # DAILY_LOSS_LIMIT, WEEKLY_LOSS_LIMIT, MAX_DRAWDOWN, etc.
    severity = Column(String(20), nullable=False)  # INFO, WARNING, CRITICAL
    
    description = Column(Text)
    metric_value = Column(DECIMAL(15, 2))
    threshold = Column(DECIMAL(15, 2))
    
    action_taken = Column(String(50))  # PAUSE_TRADING, NOTIFY_ADMIN, REDUCE_SIZE, etc.
    
    resolved_at = Column(DateTime)
    resolved_by = Column(String(36), ForeignKey("users.id"))
    resolution_notes = Column(Text)
    
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    resolver = relationship("User", foreign_keys=[resolved_by])

class RiskSettings(Base):
    __tablename__ = "risk_settings"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, unique=True, index=True)
    
    # Position sizing
    max_risk_per_trade = Column(DECIMAL(5, 2), default=2.0)  # 2% of capital
    max_risk_per_day = Column(DECIMAL(5, 2), default=5.0)    # 5% daily loss limit
    max_risk_per_week = Column(DECIMAL(5, 2), default=10.0)  # 10% weekly loss limit
    max_drawdown = Column(DECIMAL(5, 2), default=15.0)       # 15% max drawdown
    
    # Position limits
    max_simultaneous_trades = Column(Integer, default=5)
    max_position_size_pct = Column(DECIMAL(5, 2), default=20.0)  # 20% of capital per position
    
    # Stop loss
    default_stop_loss_pct = Column(DECIMAL(5, 2), default=2.0)   # 2% default stop loss
    trailing_stop_enabled = Column(Boolean, default=True)
    trailing_stop_pct = Column(DECIMAL(5, 2), default=1.0)       # 1% trailing stop
    
    # Correlation
    correlation_limit = Column(DECIMAL(5, 2), default=0.7)       # Don't trade if correlation > 0.7
    
    # Capital protection
    protected_capital_pct = Column(DECIMAL(5, 2), default=50.0)  # 50% protected
    
    # Emergency shutdown
    emergency_shutdown_enabled = Column(Boolean, default=True)
    auto_shutdown_after_events = Column(Integer, default=3)      # Shutdown after 3 risk events
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    
    # Relationships
    user = relationship("User")

class CapitalTracker(Base):
    __tablename__ = "capital_tracker"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, unique=True, index=True)
    
    # Capital tiers
    initial_capital = Column(DECIMAL(15, 2), default=0)
    protected_capital = Column(DECIMAL(15, 2), default=0)
    trading_capital = Column(DECIMAL(15, 2), default=0)
    reserve_capital = Column(DECIMAL(15, 2), default=0)
    
    # Realized PnL
    realized_profit = Column(DECIMAL(15, 2), default=0)
    unrealized_profit = Column(DECIMAL(15, 2), default=0)
    total_pnl = Column(DECIMAL(15, 2), default=0)
    
    # Daily tracking
    daily_pnl = Column(DECIMAL(15, 2), default=0)
    daily_start_capital = Column(DECIMAL(15, 2), default=0)
    daily_loss_count = Column(Integer, default=0)
    
    # Weekly tracking
    weekly_pnl = Column(DECIMAL(15, 2), default=0)
    weekly_start_capital = Column(DECIMAL(15, 2), default=0)
    weekly_loss_count = Column(Integer, default=0)
    
    # Status
    is_paused = Column(Boolean, default=False)
    paused_reason = Column(Text)
    paused_at = Column(DateTime)
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    
    # Relationships
    user = relationship("User")
