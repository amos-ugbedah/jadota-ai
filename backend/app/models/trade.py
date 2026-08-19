from sqlalchemy import Column, String, Boolean, DateTime, Integer, Float, DECIMAL, ForeignKey, Text, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
from ..core.database import Base

class Trade(Base):
    __tablename__ = "trades"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    account_id = Column(String(36), ForeignKey("demo_accounts.id"), nullable=False)
    position_id = Column(String(36), ForeignKey("positions.id"))
    
    # Order details
    symbol = Column(String(20), nullable=False)
    side = Column(String(10), nullable=False)  # BUY, SELL
    order_type = Column(String(20), nullable=False)  # MARKET, LIMIT, STOP_LOSS, TAKE_PROFIT
    
    quantity = Column(DECIMAL(15, 8), nullable=False)
    price = Column(DECIMAL(15, 8))
    executed_price = Column(DECIMAL(15, 8))
    executed_quantity = Column(DECIMAL(15, 8))
    
    # Status
    status = Column(String(20), default="PENDING")  # PENDING, EXECUTED, CANCELLED, FAILED, PARTIAL
    
    # Fees
    fee = Column(DECIMAL(15, 8), default=0)
    fee_currency = Column(String(10), default="USDT")
    
    # AI reasoning
    ai_decision_id = Column(String(36))
    
    # Timestamps
    placed_at = Column(DateTime, server_default=func.now())
    executed_at = Column(DateTime)
    cancelled_at = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    
    # Relationships
    user = relationship("User")
    account = relationship("DemoAccount")
    position = relationship("Position")
