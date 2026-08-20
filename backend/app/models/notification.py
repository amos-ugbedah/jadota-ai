from sqlalchemy import Column, String, Boolean, DateTime, Integer, ForeignKey, Text, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
from ..core.database import Base

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    
    type = Column(String(50), nullable=False)  # TRADE, SUBSCRIPTION, RISK, SYSTEM, INFO
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    
    data = Column(JSON)  # Additional data like trade_id, subscription_id
    
    is_read = Column(Boolean, default=False)
    is_sent = Column(Boolean, default=False)  # For email/telegram
    
    read_at = Column(DateTime)
    sent_at = Column(DateTime)
    
    created_at = Column(DateTime, server_default=func.now())
    
    user = relationship("User")

class NotificationPreference(Base):
    __tablename__ = "notification_preferences"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, unique=True, index=True)
    
    # Email preferences
    email_enabled = Column(Boolean, default=True)
    email_trade_executed = Column(Boolean, default=True)
    email_trade_closed = Column(Boolean, default=True)
    email_subscription_expiry = Column(Boolean, default=True)
    email_payment_confirmed = Column(Boolean, default=True)
    email_risk_alert = Column(Boolean, default=True)
    
    # Telegram preferences
    telegram_enabled = Column(Boolean, default=False)
    telegram_chat_id = Column(String(255))
    telegram_trade_executed = Column(Boolean, default=True)
    telegram_trade_closed = Column(Boolean, default=True)
    telegram_subscription_expiry = Column(Boolean, default=True)
    telegram_payment_confirmed = Column(Boolean, default=True)
    telegram_risk_alert = Column(Boolean, default=True)
    
    # In-app preferences
    in_app_enabled = Column(Boolean, default=True)
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    
    user = relationship("User")

class EmailLog(Base):
    __tablename__ = "email_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), index=True)
    
    to_email = Column(String(255), nullable=False)
    subject = Column(String(255), nullable=False)
    template = Column(String(100))
    data = Column(JSON)
    
    status = Column(String(20), default="PENDING")  # PENDING, SENT, FAILED
    error_message = Column(Text)
    
    sent_at = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())
    
    user = relationship("User")
