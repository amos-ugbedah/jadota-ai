from sqlalchemy import Column, String, Boolean, DateTime, Integer, Text
from sqlalchemy.sql import func
import uuid
from ..core.database import Base

class User(Base):
    __tablename__ = "users"

    # Use String for SQLite compatibility instead of UUID
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    role = Column(String(50), default="USER")
    
    # 2FA
    two_factor_enabled = Column(Boolean, default=False)
    two_factor_secret = Column(String(255), nullable=True)
    
    # Verification
    email_verified_at = Column(DateTime, nullable=True)
    last_login_at = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    deleted_at = Column(DateTime, nullable=True)
