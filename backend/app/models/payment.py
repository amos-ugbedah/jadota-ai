"""
Payment model — tracks crypto payment attempts for subscription upgrades.
"""

from sqlalchemy import Column, String, DateTime, Float, Text
from sqlalchemy.sql import func
import uuid

from ..core.database import Base


class PaymentStatus:
    PENDING = "pending"         # awaiting user payment
    VERIFYING = "verifying"     # checking blockchain
    COMPLETED = "completed"     # confirmed, subscription activated
    FAILED = "failed"           # verification failed
    EXPIRED = "expired"         # timeout, no payment received
    CANCELLED = "cancelled"     # user cancelled


class Payment(Base):
    __tablename__ = "payments"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), nullable=False, index=True)

    # What they're buying
    plan = Column(String(50), nullable=False)              # PRO, ENTERPRISE
    months = Column(Float, default=1.0)                    # subscription length
    amount_usdt = Column(Float, nullable=False)            # expected USDT amount

    # Where they send it
    network = Column(String(20), default="BEP20")          # BEP20 | ERC20
    wallet_address = Column(String(100), nullable=False)   # receiving wallet

    # Lifecycle
    status = Column(String(20), default=PaymentStatus.PENDING, index=True)
    tx_hash = Column(String(100), nullable=True)           # blockchain tx hash
    admin_notes = Column(Text, nullable=True)              # for manual approvals

    created_at = Column(DateTime, server_default=func.now())
    expires_at = Column(DateTime, nullable=False)
    verified_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<Payment {self.id[:8]} {self.plan} ${self.amount_usdt} {self.status}>"