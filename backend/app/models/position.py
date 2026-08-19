from sqlalchemy import Column, String, Boolean, DateTime, Integer, Float, DECIMAL, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
from ..core.database import Base

class Position(Base):
    __tablename__ = "positions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    account_id = Column(String(36), ForeignKey("demo_accounts.id"), nullable=False)
    
    # Asset details
    symbol = Column(String(20), nullable=False)
    side = Column(String(10), nullable=False)  # LONG, SHORT
    
    # Position details
    entry_price = Column(DECIMAL(15, 8), nullable=False)
    current_price = Column(DECIMAL(15, 8))
    quantity = Column(DECIMAL(15, 8), nullable=False)
    notional_value = Column(DECIMAL(15, 2), nullable=False)
    
    # Profit/Loss
    unrealized_pnl = Column(DECIMAL(15, 2), default=0)
    realized_pnl = Column(DECIMAL(15, 2), default=0)
    
    # Stop loss & take profit
    stop_loss_price = Column(DECIMAL(15, 8))
    take_profit_price = Column(DECIMAL(15, 8))
    
    # Risk metrics
    risk_percent = Column(DECIMAL(5, 2))
    risk_amount = Column(DECIMAL(15, 2))
    
    # AI reasoning
    ai_confidence = Column(DECIMAL(5, 2))
    ai_reasoning = Column(Text)
    
    # Status
    status = Column(String(20), default="OPEN")  # OPEN, CLOSED, PARTIAL
    
    # Timestamps
    opened_at = Column(DateTime, server_default=func.now())
    closed_at = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    
    # Relationships
    user = relationship("User")
    account = relationship("DemoAccount")
