from sqlalchemy import Column, String, Boolean, DateTime, Integer, DECIMAL, ForeignKey, Text, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
from ..core.database import Base

class SubscriptionPlan(Base):
    __tablename__ = "subscription_plans"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False)
    code = Column(String(50), unique=True, nullable=False)
    description = Column(Text)
    
    price_usdt = Column(DECIMAL(10, 2), nullable=False)
    duration_days = Column(Integer, nullable=False)
    
    features = Column(JSON, default=list)
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    plan_id = Column(String(36), ForeignKey("subscription_plans.id"), nullable=False)
    
    status = Column(String(50), default="PENDING")
    
    start_at = Column(DateTime, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    
    auto_renew = Column(Boolean, default=False)
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    
    user = relationship("User")
    plan = relationship("SubscriptionPlan")
    payments = relationship("Payment", back_populates="subscription")

class Payment(Base):
    __tablename__ = "payments"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    subscription_id = Column(String(36), ForeignKey("subscriptions.id"))
    
    amount_usdt = Column(DECIMAL(10, 2), nullable=False)
    currency = Column(String(10), default="USDT")
    network = Column(String(20), default="BEP20")
    
    transaction_hash = Column(String(255), unique=True, nullable=False)
    from_address = Column(String(255))
    to_address = Column(String(255), nullable=False)
    
    status = Column(String(50), default="PENDING")
    confirmations = Column(Integer, default=0)
    required_confirmations = Column(Integer, default=6)
    
    verified_at = Column(DateTime)
    payment_metadata = Column(JSON)  # Renamed from 'metadata' to avoid conflict
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    
    user = relationship("User")
    subscription = relationship("Subscription", back_populates="payments")

class SubscriptionAccess(Base):
    __tablename__ = "subscription_access"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, unique=True, index=True)
    
    has_demo_access = Column(Boolean, default=True)
    has_live_access = Column(Boolean, default=False)
    has_ai_access = Column(Boolean, default=False)
    
    max_live_trades = Column(Integer, default=0)
    max_live_capital = Column(DECIMAL(15, 2), default=0)
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    
    user = relationship("User")
