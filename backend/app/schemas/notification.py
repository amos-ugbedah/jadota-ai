from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class NotificationResponse(BaseModel):
    id: str
    type: str
    title: str
    message: str
    data: Optional[Dict[str, Any]]
    is_read: bool
    is_sent: bool
    read_at: Optional[datetime]
    sent_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True

class NotificationPreferenceResponse(BaseModel):
    email_enabled: bool
    email_trade_executed: bool
    email_trade_closed: bool
    email_subscription_expiry: bool
    email_payment_confirmed: bool
    email_risk_alert: bool
    telegram_enabled: bool
    telegram_chat_id: Optional[str]
    telegram_trade_executed: bool
    telegram_trade_closed: bool
    telegram_subscription_expiry: bool
    telegram_payment_confirmed: bool
    telegram_risk_alert: bool
    in_app_enabled: bool

    class Config:
        from_attributes = True

class UpdateNotificationPreference(BaseModel):
    email_enabled: Optional[bool] = None
    email_trade_executed: Optional[bool] = None
    email_trade_closed: Optional[bool] = None
    email_subscription_expiry: Optional[bool] = None
    email_payment_confirmed: Optional[bool] = None
    email_risk_alert: Optional[bool] = None
    telegram_enabled: Optional[bool] = None
    telegram_chat_id: Optional[str] = None
    telegram_trade_executed: Optional[bool] = None
    telegram_trade_closed: Optional[bool] = None
    telegram_subscription_expiry: Optional[bool] = None
    telegram_payment_confirmed: Optional[bool] = None
    telegram_risk_alert: Optional[bool] = None
    in_app_enabled: Optional[bool] = None

class MarkNotificationsRead(BaseModel):
    notification_ids: List[str]

class CreateNotificationRequest(BaseModel):
    user_id: str
    type: str
    title: str
    message: str
    data: Optional[Dict[str, Any]] = None
