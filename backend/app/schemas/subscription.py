from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from decimal import Decimal

class PlanResponse(BaseModel):
    id: str
    name: str
    code: str
    description: Optional[str]
    price_usdt: Decimal
    duration_days: int
    features: List[str]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class SubscriptionCreate(BaseModel):
    plan_code: str

class SubscriptionResponse(BaseModel):
    id: str
    plan: PlanResponse
    status: str
    start_at: datetime
    expires_at: datetime
    auto_renew: bool
    created_at: datetime

    class Config:
        from_attributes = True

class PaymentCreate(BaseModel):
    transaction_hash: str
    amount_usdt: Decimal
    network: str = "BEP20"
    from_address: str
    to_address: str

class PaymentResponse(BaseModel):
    id: str
    amount_usdt: Decimal
    currency: str
    network: str
    transaction_hash: str
    from_address: str
    to_address: str
    status: str
    confirmations: int
    verified_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True

class SubscriptionAccessResponse(BaseModel):
    has_demo_access: bool
    has_live_access: bool
    has_ai_access: bool
    max_live_trades: int
    max_live_capital: Decimal

    class Config:
        from_attributes = True

class PaymentVerificationRequest(BaseModel):
    transaction_hash: str
    amount_usdt: Decimal
    network: str = "BEP20"
