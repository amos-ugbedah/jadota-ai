from sqlalchemy.orm import Session
from datetime import datetime
import logging
from typing import List, Dict, Any, Optional
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from ..models.notification import Notification, NotificationPreference, EmailLog
from ..models.user import User
from ..schemas.notification import CreateNotificationRequest

logger = logging.getLogger(__name__)

class NotificationService:
    """Service for managing notifications."""
    
    def __init__(self):
        self.email_enabled = True
        self.smtp_host = "smtp.gmail.com"  # Configure in settings
        self.smtp_port = 587
        self.smtp_user = "noreply@jadota.ai"
        self.smtp_password = ""  # Should come from settings
    
    # ============ Notification Creation ============
    
    def create_notification(
        self,
        db: Session,
        user_id: str,
        type: str,
        title: str,
        message: str,
        data: Optional[Dict[str, Any]] = None
    ) -> Notification:
        """Create a new notification."""
        notification = Notification(
            user_id=user_id,
            type=type,
            title=title,
            message=message,
            data=data,
            is_read=False,
            is_sent=False
        )
        
        db.add(notification)
        db.commit()
        db.refresh(notification)
        
        # Get user preferences
        prefs = self.get_preferences(db, user_id)
        
        # Send email if enabled
        if prefs and prefs.email_enabled:
            self.send_email_notification(db, user_id, notification, prefs)
        
        return notification
    
    def create_trade_notification(
        self,
        db: Session,
        user_id: str,
        trade_data: Dict[str, Any],
        action: str  # EXECUTED, CLOSED, STOP_LOSS, TAKE_PROFIT
    ) -> Notification:
        """Create a trade notification."""
        if action == "EXECUTED":
            title = f"Trade Executed: {trade_data.get('symbol')}"
            message = f"Your {trade_data.get('side')} position of {trade_data.get('quantity')} {trade_data.get('symbol')} was executed at {trade_data.get('entry_price')}"
        elif action == "CLOSED":
            title = f"Trade Closed: {trade_data.get('symbol')}"
            message = f"Your {trade_data.get('side')} position was closed at {trade_data.get('exit_price')} with PnL: ${trade_data.get('pnl', 0):.2f}"
        elif action == "STOP_LOSS":
            title = f"Stop Loss Triggered: {trade_data.get('symbol')}"
            message = f"Your {trade_data.get('side')} position was stopped out at {trade_data.get('exit_price')} with loss: ${trade_data.get('pnl', 0):.2f}"
        elif action == "TAKE_PROFIT":
            title = f"Take Profit Hit: {trade_data.get('symbol')}"
            message = f"Your {trade_data.get('side')} position hit take profit at {trade_data.get('exit_price')} with profit: ${trade_data.get('pnl', 0):.2f}"
        else:
            title = f"Trade Update: {trade_data.get('symbol')}"
            message = f"Your trade has been updated"
        
        return self.create_notification(
            db,
            user_id,
            "TRADE",
            title,
            message,
            trade_data
        )
    
    def create_subscription_notification(
        self,
        db: Session,
        user_id: str,
        subscription_data: Dict[str, Any],
        action: str  # CREATED, RENEWED, EXPIRED, CANCELLED
    ) -> Notification:
        """Create a subscription notification."""
        if action == "CREATED":
            title = "Subscription Activated"
            message = f"Your {subscription_data.get('plan_name')} subscription has been activated. Expires on {subscription_data.get('expires_at')}"
        elif action == "RENEWED":
            title = "Subscription Renewed"
            message = f"Your {subscription_data.get('plan_name')} subscription has been renewed. Now expires on {subscription_data.get('expires_at')}"
        elif action == "EXPIRED":
            title = "Subscription Expired"
            message = f"Your {subscription_data.get('plan_name')} subscription has expired. Please renew to continue trading."
        elif action == "CANCELLED":
            title = "Subscription Cancelled"
            message = f"Your {subscription_data.get('plan_name')} subscription has been cancelled."
        else:
            title = "Subscription Update"
            message = "Your subscription has been updated"
        
        return self.create_notification(
            db,
            user_id,
            "SUBSCRIPTION",
            title,
            message,
            subscription_data
        )
    
    def create_risk_notification(
        self,
        db: Session,
        user_id: str,
        risk_data: Dict[str, Any],
        severity: str  # WARNING, CRITICAL
    ) -> Notification:
        """Create a risk notification."""
        title = f"Risk Alert: {risk_data.get('event_type')}"
        message = f"{risk_data.get('description')}"
        
        return self.create_notification(
            db,
            user_id,
            "RISK",
            title,
            message,
            risk_data
        )
    
    # ============ Notification Retrieval ============
    
    def get_user_notifications(
        self,
        db: Session,
        user_id: str,
        limit: int = 50,
        unread_only: bool = False
    ) -> List[Notification]:
        """Get user's notifications."""
        query = db.query(Notification).filter(
            Notification.user_id == user_id
        )
        
        if unread_only:
            query = query.filter(Notification.is_read == False)
        
        return query.order_by(
            Notification.created_at.desc()
        ).limit(limit).all()
    
    def get_unread_count(self, db: Session, user_id: str) -> int:
        """Get unread notification count."""
        return db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.is_read == False
        ).count()
    
    def mark_as_read(
        self,
        db: Session,
        user_id: str,
        notification_ids: List[str]
    ) -> int:
        """Mark notifications as read."""
        count = db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.id.in_(notification_ids)
        ).update(
            {"is_read": True, "read_at": datetime.utcnow()},
            synchronize_session=False
        )
        db.commit()
        return count
    
    def mark_all_as_read(self, db: Session, user_id: str) -> int:
        """Mark all notifications as read."""
        count = db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.is_read == False
        ).update(
            {"is_read": True, "read_at": datetime.utcnow()},
            synchronize_session=False
        )
        db.commit()
        return count
    
    # ============ Notification Preferences ============
    
    def get_preferences(
        self,
        db: Session,
        user_id: str
    ) -> NotificationPreference:
        """Get user's notification preferences."""
        prefs = db.query(NotificationPreference).filter(
            NotificationPreference.user_id == user_id
        ).first()
        
        if not prefs:
            prefs = NotificationPreference(user_id=user_id)
            db.add(prefs)
            db.commit()
            db.refresh(prefs)
        
        return prefs
    
    def update_preferences(
        self,
        db: Session,
        user_id: str,
        updates: Dict[str, Any]
    ) -> NotificationPreference:
        """Update notification preferences."""
        prefs = self.get_preferences(db, user_id)
        
        for key, value in updates.items():
            if value is not None and hasattr(prefs, key):
                setattr(prefs, key, value)
        
        db.commit()
        db.refresh(prefs)
        return prefs
    
    # ============ Email Notifications ============
    
    def send_email_notification(
        self,
        db: Session,
        user_id: str,
        notification: Notification,
        prefs: NotificationPreference
    ):
        """Send email notification."""
        # Check if this type of notification should be sent via email
        should_send = True
        if notification.type == "TRADE":
            if notification.title.startswith("Trade Executed") and not prefs.email_trade_executed:
                should_send = False
            elif notification.title.startswith("Trade Closed") and not prefs.email_trade_closed:
                should_send = False
        elif notification.type == "SUBSCRIPTION":
            if "Expired" in notification.title and not prefs.email_subscription_expiry:
                should_send = False
        elif notification.type == "RISK" and not prefs.email_risk_alert:
            should_send = False
        
        if not should_send or not self.email_enabled:
            return
        
        # Get user email
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return
        
        # Send email (simplified - using print for now)
        print(f"""
        📧 EMAIL NOTIFICATION
        To: {user.email}
        Subject: {notification.title}
        Body: {notification.message}
        Type: {notification.type}
        """)
        
        # In production, use actual email sending
        # self._send_email(user.email, notification.title, notification.message)
        
        notification.is_sent = True
        notification.sent_at = datetime.utcnow()
        db.commit()
    
    def _send_email(self, to_email: str, subject: str, body: str):
        """Send actual email (placeholder)."""
        # Implement with SendGrid, SMTP, or other email service
        pass
    
    # ============ Telegram Notifications ============
    
    def send_telegram_notification(
        self,
        chat_id: str,
        message: str
    ):
        """Send Telegram notification."""
        # In production, use python-telegram-bot or requests
        print(f"""
        📱 TELEGRAM NOTIFICATION
        Chat ID: {chat_id}
        Message: {message}
        """)
    
    # ============ System Notifications ============
    
    def notify_subscription_expiry(self, db: Session):
        """Notify users about upcoming subscription expiry."""
        from datetime import timedelta
        
        # Find subscriptions expiring in 3 days
        expiry_threshold = datetime.utcnow() + timedelta(days=3)
        expiring = db.query(Notification).filter(
            Subscription.status == "ACTIVE",
            Subscription.expires_at <= expiry_threshold,
            Subscription.expires_at > datetime.utcnow()
        ).all()
        
        # This is a placeholder - would need to query subscriptions
        pass

notification_service = NotificationService()
