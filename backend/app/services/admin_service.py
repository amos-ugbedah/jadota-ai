from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc
from decimal import Decimal
from datetime import datetime, timedelta
import logging
from typing import Dict, Any, List, Optional

from ..models.user import User
from ..models.subscription import Subscription, Payment, SubscriptionPlan
from ..models.live_trading import LiveTrade, LivePosition
from ..models.risk import RiskEvent
from ..models.admin import SystemLog, SystemMetric, AdminAction

logger = logging.getLogger(__name__)

class AdminService:
    """Service for admin dashboard operations."""
    
    def get_dashboard_stats(self, db: Session) -> Dict[str, Any]:
        """Get dashboard statistics."""
        # User stats
        total_users = db.query(User).count()
        active_users = db.query(User).filter(User.is_active == True).count()
        
        # Subscription stats
        total_subscriptions = db.query(Subscription).count()
        active_subscriptions = db.query(Subscription).filter(
            Subscription.status == "ACTIVE"
        ).count()
        
        # Revenue stats
        total_revenue = db.query(func.sum(Payment.amount_usdt)).filter(
            Payment.status == "CONFIRMED"
        ).scalar() or 0
        
        monthly_revenue = db.query(func.sum(Payment.amount_usdt)).filter(
            Payment.status == "CONFIRMED",
            Payment.created_at >= datetime.utcnow() - timedelta(days=30)
        ).scalar() or 0
        
        # Trading stats
        total_trades = db.query(LiveTrade).count()
        total_volume = db.query(func.sum(LiveTrade.quantity * LiveTrade.executed_price)).scalar() or 0
        
        # AI status (simplified)
        ai_status = "ACTIVE"
        
        return {
            'total_users': total_users,
            'active_users': active_users,
            'total_subscriptions': total_subscriptions,
            'active_subscriptions': active_subscriptions,
            'total_revenue': Decimal(str(total_revenue)),
            'monthly_revenue': Decimal(str(monthly_revenue)),
            'total_trades': total_trades,
            'total_trading_volume': Decimal(str(total_volume)),
            'system_uptime': 99.9,
            'ai_status': ai_status
        }
    
    def get_users(
        self, 
        db: Session, 
        skip: int = 0, 
        limit: int = 50,
        search: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get list of users with their subscription status."""
        query = db.query(User)
        
        if search:
            query = query.filter(
                User.email.contains(search) | User.username.contains(search)
            )
        
        users = query.offset(skip).limit(limit).all()
        
        result = []
        for user in users:
            subscription = db.query(Subscription).filter(
                Subscription.user_id == user.id,
                Subscription.status == "ACTIVE"
            ).first()
            
            trade_count = db.query(LiveTrade).filter(
                LiveTrade.user_id == user.id
            ).count()
            
            result.append({
                'id': user.id,
                'email': user.email,
                'username': user.username,
                'full_name': user.full_name,
                'role': user.role,
                'is_active': user.is_active,
                'is_verified': user.is_verified,
                'created_at': user.created_at,
                'has_subscription': subscription is not None,
                'subscription_status': subscription.status if subscription else None,
                'total_trades': trade_count
            })
        
        return result
    
    def get_user_detail(self, db: Session, user_id: str) -> Dict[str, Any]:
        """Get detailed user information."""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("User not found")
        
        # Get subscriptions
        subscriptions = db.query(Subscription).filter(
            Subscription.user_id == user_id
        ).order_by(Subscription.created_at.desc()).all()
        
        # Get payments
        payments = db.query(Payment).filter(
            Payment.user_id == user_id
        ).order_by(Payment.created_at.desc()).all()
        
        # Get trades
        trades = db.query(LiveTrade).filter(
            LiveTrade.user_id == user_id
        ).all()
        
        # Get risk events
        risk_events = db.query(RiskEvent).filter(
            RiskEvent.user_id == user_id
        ).order_by(RiskEvent.created_at.desc()).limit(20).all()
        
        # Trade stats
        total_trades = len(trades)
        winning_trades = len([t for t in trades if t.status == "EXECUTED"])  # Simplified
        
        return {
            'id': user.id,
            'email': user.email,
            'username': user.username,
            'full_name': user.full_name,
            'role': user.role,
            'is_active': user.is_active,
            'is_verified': user.is_verified,
            'created_at': user.created_at,
            'last_login_at': user.last_login_at,
            'subscription': subscriptions[0] if subscriptions else None,
            'payments': payments[:20],
            'trade_stats': {
                'total_trades': total_trades,
                'winning_trades': winning_trades
            },
            'risk_events': risk_events
        }
    
    def update_user(self, db: Session, user_id: str, update_data: dict) -> User:
        """Update user information."""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("User not found")
        
        for key, value in update_data.items():
            if value is not None:
                setattr(user, key, value)
        
        db.commit()
        db.refresh(user)
        return user
    
    def get_system_logs(self, db: Session, limit: int = 100) -> List[SystemLog]:
        """Get recent system logs."""
        return db.query(SystemLog).order_by(
            SystemLog.created_at.desc()
        ).limit(limit).all()
    
    def get_system_metrics(self, db: Session, hours: int = 24) -> List[Dict[str, Any]]:
        """Get system metrics for the last N hours."""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        
        metrics = db.query(SystemMetric).filter(
            SystemMetric.created_at >= cutoff
        ).order_by(SystemMetric.created_at.asc()).all()
        
        # Group by metric name
        grouped = {}
        for metric in metrics:
            if metric.metric_name not in grouped:
                grouped[metric.metric_name] = []
            grouped[metric.metric_name].append({
                'value': metric.metric_value,
                'timestamp': metric.created_at.isoformat()
            })
        
        return [{'name': name, 'data': data} for name, data in grouped.items()]
    
    def log_admin_action(
        self, 
        db: Session, 
        admin_id: str, 
        action_type: str,
        target_type: Optional[str] = None,
        target_id: Optional[str] = None,
        details: Optional[dict] = None
    ):
        """Log an admin action."""
        action = AdminAction(
            admin_id=admin_id,
            action_type=action_type,
            target_type=target_type,
            target_id=target_id,
            details=details
        )
        db.add(action)
        db.commit()
        return action
    
    def get_admin_actions(
        self, 
        db: Session, 
        limit: int = 50
    ) -> List[AdminAction]:
        """Get recent admin actions."""
        return db.query(AdminAction).order_by(
            AdminAction.created_at.desc()
        ).limit(limit).all()

admin_service = AdminService()
