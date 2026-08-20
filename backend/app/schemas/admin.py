from pydantic import BaseModel, Field
from typing import Optional, List, Any
from datetime import datetime
from decimal import Decimal

class DashboardStats(BaseModel):
    total_users: int
    active_users: int
    total_subscriptions: int
    active_subscriptions: int
    total_revenue: Decimal
    monthly_revenue: Decimal
    total_trades: int
    total_trading_volume: Decimal
    system_uptime: float
    ai_status: str

class UserListItem(BaseModel):
    id: str
    email: str
    username: str
    full_name: Optional[str]
    role: str
    is_active: bool
    is_verified: bool
    created_at: datetime
    has_subscription: bool
    subscription_status: Optional[str]
    total_trades: int

class UserDetailResponse(BaseModel):
    id: str
    email: str
    username: str
    full_name: Optional[str]
    role: str
    is_active: bool
    is_verified: bool
    created_at: datetime
    last_login_at: Optional[datetime]
    subscription: Optional[dict]
    payments: List[dict]
    trade_stats: dict
    risk_events: List[dict]

class AdminActionCreate(BaseModel):
    action_type: str
    target_type: Optional[str] = None
    target_id: Optional[str] = None
    details: Optional[dict] = None

class AdminActionResponse(BaseModel):
    id: str
    admin_id: str
    action_type: str
    target_type: Optional[str]
    target_id: Optional[str]
    details: Optional[dict]
    created_at: datetime
    admin_email: Optional[str]

    class Config:
        from_attributes = True

class SystemMetricResponse(BaseModel):
    id: str
    metric_name: str
    metric_value: float
    unit: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

class SystemLogResponse(BaseModel):
    id: str
    level: str
    component: str
    message: str
    details: Optional[dict]
    created_at: datetime

    class Config:
        from_attributes = True

class UserUpdateRequest(BaseModel):
    is_active: Optional[bool] = None
    role: Optional[str] = None
    is_verified: Optional[bool] = None
