"""
Exchange API credentials — one row per user per exchange.

Secrets are encrypted at rest with Fernet (see services/encryption.py).
Never returned to the client in plaintext.
"""

from sqlalchemy import Column, String, Boolean, DateTime, Text
from sqlalchemy.sql import func
import uuid

from ..core.database import Base


class ExchangeCredentials(Base):
    __tablename__ = "exchange_credentials"
    __table_args__ = {"extend_existing": True}

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), nullable=False, index=True)
    exchange = Column(String(20), nullable=False, default="bitget", index=True)

    api_key_encrypted = Column(Text, nullable=False)
    api_secret_encrypted = Column(Text, nullable=False)
    passphrase_encrypted = Column(Text, nullable=False)

    api_key_masked = Column(String(50), nullable=True)
    permissions = Column(String(100), nullable=True)
    ip_whitelist = Column(String(200), nullable=True)

    is_active = Column(Boolean, default=True)
    last_used_at = Column(DateTime, nullable=True)
    last_error = Column(Text, nullable=True)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    def __repr__(self):
        return f"<ExchangeCredentials {self.exchange} user={self.user_id[:8]}>"