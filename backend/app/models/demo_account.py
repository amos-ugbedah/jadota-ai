from sqlalchemy import Column, String, Boolean, DateTime, Integer, Float, DECIMAL, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
from ..core.database import Base

class DemoAccount(Base):
    __tablename__ = "demo_accounts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    
    # Balance
    initial_balance = Column(DECIMAL(15, 2), default=10000.00)
    current_balance = Column(DECIMAL(15, 2), default=10000.00)
    
    # Performance metrics
    total_pnl = Column(DECIMAL(15, 2), default=0)
    total_return = Column(DECIMAL(10, 2), default=0)
    win_rate = Column(DECIMAL(5, 2), default=0)
    profit_factor = Column(DECIMAL(10, 2), default=0)
    max_drawdown = Column(DECIMAL(10, 2), default=0)
    sharpe_ratio = Column(DECIMAL(10, 2), default=0)
    
    # Trade counts
    total_trades = Column(Integer, default=0)
    winning_trades = Column(Integer, default=0)
    losing_trades = Column(Integer, default=0)
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    
    # Relationships
    user = relationship("User")
