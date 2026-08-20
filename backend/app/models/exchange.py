from sqlalchemy import Column, String, Boolean, DateTime, Integer, Float, DECIMAL, ForeignKey, Text, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
from ..core.database import Base

class ExchangeAccount(Base):
    __tablename__ = "exchange_accounts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    
    exchange = Column(String(50), nullable=False, default="BITGET")
    
    # API Credentials (encrypted at rest)
    api_key = Column(String(255), nullable=False)
    api_secret_encrypted = Column(Text, nullable=False)
    passphrase_encrypted = Column(Text, nullable=True)
    
    # Permissions
    permissions_read = Column(Boolean, default=True)
    permissions_trade = Column(Boolean, default=True)
    permissions_withdraw = Column(Boolean, default=False)
    
    # Status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    last_verified_at = Column(DateTime)
    
    # IP Whitelist
    ip_whitelist = Column(JSON, default=list)
    
    # Rate limit tracking
    rate_limit_remaining = Column(Integer, default=1000)
    rate_limit_reset = Column(DateTime)
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    
    # Relationships
    user = relationship("User")

class ExchangeOrder(Base):
    __tablename__ = "exchange_orders"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    exchange_account_id = Column(String(36), ForeignKey("exchange_accounts.id"), nullable=False)
    
    # Order details
    symbol = Column(String(20), nullable=False)
    side = Column(String(10), nullable=False)  # BUY, SELL
    order_type = Column(String(20), nullable=False)  # MARKET, LIMIT, STOP, STOP_LIMIT
    
    quantity = Column(DECIMAL(15, 8), nullable=False)
    price = Column(DECIMAL(15, 8))
    stop_price = Column(DECIMAL(15, 8))
    
    # Execution
    executed_quantity = Column(DECIMAL(15, 8), default=0)
    executed_price = Column(DECIMAL(15, 8))
    avg_price = Column(DECIMAL(15, 8))
    
    # Status
    status = Column(String(20), default="PENDING")  # PENDING, OPEN, FILLED, CANCELLED, FAILED, PARTIAL
    
    # Exchange references
    exchange_order_id = Column(String(255))
    exchange_response = Column(JSON)
    
    # Fees
    fee = Column(DECIMAL(15, 8))
    fee_currency = Column(String(10))
    
    # Timestamps
    placed_at = Column(DateTime, server_default=func.now())
    executed_at = Column(DateTime)
    cancelled_at = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    
    # Relationships
    user = relationship("User")
    exchange_account = relationship("ExchangeAccount")

class ExchangeBalance(Base):
    __tablename__ = "exchange_balances"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    exchange_account_id = Column(String(36), ForeignKey("exchange_accounts.id"), nullable=False)
    
    asset = Column(String(20), nullable=False)
    total = Column(DECIMAL(25, 8), default=0)
    free = Column(DECIMAL(25, 8), default=0)
    used = Column(DECIMAL(25, 8), default=0)
    
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    user = relationship("User")
    exchange_account = relationship("ExchangeAccount")
