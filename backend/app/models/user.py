from sqlalchemy import Column, String, Boolean, DateTime, Integer, Text, Float, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
import enum
from datetime import datetime
from ..core.database import Base


# ============================================
# User Role Enum
# ============================================
class UserRole(str, enum.Enum):
    USER = "USER"
    ADMIN = "ADMIN"
    SUPER_ADMIN = "SUPER_ADMIN"


# ============================================
# Subscription plan constants
# ============================================
FREE_PLANS = {"BASIC", "FREE", ""}


# ============================================
# User Model
# ============================================
class User(Base):
    __tablename__ = "users"

    # ============================================
    # Primary Key
    # ============================================
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # ============================================
    # Authentication
    # ============================================
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)

    # ============================================
    # Role & Status
    # ============================================
    role = Column(String(50), default="USER")  # USER, ADMIN, SUPER_ADMIN
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)

    # ============================================
    # 2FA (Two-Factor Authentication)
    # ============================================
    two_factor_enabled = Column(Boolean, default=False)
    two_factor_secret = Column(String(255), nullable=True)

    # ============================================
    # Verification & Login Tracking
    # ============================================
    email_verified_at = Column(DateTime, nullable=True)
    last_login_at = Column(DateTime, nullable=True)
    last_login_ip = Column(String(45), nullable=True)  # IPv6 support

    # ============================================
    # Financial
    # ============================================
    demo_balance = Column(Float, default=10000.0)
    real_balance = Column(Float, default=0.0)
    total_deposits = Column(Float, default=0.0)
    total_withdrawals = Column(Float, default=0.0)
    total_pnl = Column(Float, default=0.0)

    # ============================================
    # Subscription
    # ============================================
    subscription_plan = Column(String(50), nullable=True)  # BASIC, PRO, ENTERPRISE
    subscription_expires_at = Column(DateTime, nullable=True)
    is_subscription_active = Column(Boolean, default=False)

    # ============================================
    # Preferences
    # ============================================
    preferences = Column(Text, nullable=True)  # JSON string for user preferences

    # ============================================
    # Timestamps
    # ============================================
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    deleted_at = Column(DateTime, nullable=True)  # Soft delete

    # ============================================
    # Properties
    # ============================================
    @property
    def is_admin(self) -> bool:
        """Check if user is admin or super admin"""
        return self.role in ["ADMIN", "SUPER_ADMIN"]

    @property
    def is_super_admin(self) -> bool:
        """Check if user is super admin"""
        return self.role == "SUPER_ADMIN"

    @property
    def has_active_subscription(self) -> bool:
        """
        Check if user has an active paid subscription.

        🔥 FIX: Sources of truth are `subscription_plan` + `subscription_expires_at`.
        The `is_subscription_active` boolean is unreliable (was not always set
        during bootstrap/registration), so it's NOT used here.
        """
        # No plan set = no subscription
        if not self.subscription_plan:
            return False

        # Normalize and check if it's a free plan
        plan = (self.subscription_plan or "").strip().upper()
        if plan in FREE_PLANS or plan == "BASIC":
            return False

        # Must have an expiry date
        if not self.subscription_expires_at:
            return False

        # Must not be expired
        return datetime.utcnow() < self.subscription_expires_at

    @property
    def days_until_subscription_expires(self) -> int:
        """Get days until subscription expires"""
        if not self.subscription_expires_at:
            return 0
        delta = self.subscription_expires_at - datetime.utcnow()
        return max(0, delta.days)

    @property
    def total_balance(self) -> float:
        """Get total balance (demo + real)"""
        return self.demo_balance + self.real_balance

    # ============================================
    # Methods
    # ============================================
    def update_last_login(self, ip: str = None):
        """Update last login timestamp and IP"""
        self.last_login_at = datetime.utcnow()
        if ip:
            self.last_login_ip = ip

    def add_to_balance(self, amount: float, is_real: bool = False):
        """Add to user balance"""
        if is_real:
            self.real_balance += amount
        else:
            self.demo_balance += amount

    def subtract_from_balance(self, amount: float, is_real: bool = False):
        """Subtract from user balance"""
        if is_real:
            if self.real_balance < amount:
                raise ValueError("Insufficient real balance")
            self.real_balance -= amount
        else:
            if self.demo_balance < amount:
                raise ValueError("Insufficient demo balance")
            self.demo_balance -= amount

    def update_pnl(self, pnl: float):
        """Update total P&L"""
        self.total_pnl += pnl

    # ============================================
    # String Representation
    # ============================================
    def __repr__(self):
        return f"<User {self.email} ({self.role})>"

    def __str__(self):
        return f"{self.full_name or self.username} ({self.email})"