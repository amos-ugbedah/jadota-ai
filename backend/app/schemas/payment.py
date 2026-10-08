"""
Payment schemas.
"""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class PaymentCreateRequest(BaseModel):
    plan: str                 # "pro" | "enterprise"
    months: float = 1.0


class PaymentResponse(BaseModel):
    id: str
    user_id: str
    plan: str
    months: float
    amount_usdt: float
    network: str
    wallet_address: str
    status: str
    tx_hash: Optional[str] = None
    created_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    verified_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PaymentVerifyResponse(BaseModel):
    success: bool
    status: str
    message: str
    tx_hash: Optional[str] = None


class AdminApproveRequest(BaseModel):
    tx_hash: Optional[str] = None
    admin_notes: Optional[str] = None