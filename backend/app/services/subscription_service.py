from sqlalchemy.orm import Session
from decimal import Decimal
from datetime import datetime, timedelta
import logging
from typing import Dict, Any, Optional, List

from ..models.subscription import SubscriptionPlan, Subscription, Payment, SubscriptionAccess
from ..schemas.subscription import PaymentCreate

logger = logging.getLogger(__name__)

class SubscriptionService:
    DEFAULT_PLANS = [
        {
            'name': 'Monthly',
            'code': 'monthly',
            'description': '1 month of JADOTA AI access',
            'price_usdt': 29.99,
            'duration_days': 30,
            'features': ['Live Trading', 'AI Signals', 'Demo Trading', 'Email Support']
        },
        {
            'name': 'Quarterly',
            'code': 'quarterly',
            'description': '3 months of JADOTA AI access',
            'price_usdt': 79.99,
            'duration_days': 90,
            'features': ['Live Trading', 'AI Signals', 'Demo Trading', 'Priority Support']
        },
        {
            'name': 'Yearly',
            'code': 'yearly',
            'description': '12 months of JADOTA AI access',
            'price_usdt': 299.99,
            'duration_days': 365,
            'features': ['Live Trading', 'AI Signals', 'Demo Trading', 'Priority Support', 'Advanced Analytics', 'API Access']
        }
    ]
    
    def __init__(self):
        self.payment_wallet = "0xJADOTAWalletAddress"
    
    def initialize_plans(self, db: Session):
        for plan_data in self.DEFAULT_PLANS:
            existing = db.query(SubscriptionPlan).filter(
                SubscriptionPlan.code == plan_data['code']
            ).first()
            if not existing:
                plan = SubscriptionPlan(**plan_data)
                db.add(plan)
        db.commit()
    
    def get_plans(self, db: Session) -> List[SubscriptionPlan]:
        return db.query(SubscriptionPlan).filter(
            SubscriptionPlan.is_active == True
        ).all()
    
    def get_plan_by_code(self, db: Session, code: str) -> Optional[SubscriptionPlan]:
        return db.query(SubscriptionPlan).filter(
            SubscriptionPlan.code == code,
            SubscriptionPlan.is_active == True
        ).first()
    
    def get_or_create_access(self, db: Session, user_id: str) -> SubscriptionAccess:
        access = db.query(SubscriptionAccess).filter(
            SubscriptionAccess.user_id == user_id
        ).first()
        
        if not access:
            access = SubscriptionAccess(
                user_id=user_id,
                has_demo_access=True,
                has_live_access=False,
                has_ai_access=False,
                max_live_trades=0,
                max_live_capital=0
            )
            db.add(access)
            db.commit()
            db.refresh(access)
        
        return access
    
    def create_subscription(
        self,
        db: Session,
        user_id: str,
        plan_code: str,
        payment_id: Optional[str] = None
    ) -> Subscription:
        plan = self.get_plan_by_code(db, plan_code)
        if not plan:
            raise ValueError(f"Plan {plan_code} not found")
        
        active_sub = db.query(Subscription).filter(
            Subscription.user_id == user_id,
            Subscription.status == "ACTIVE"
        ).first()
        
        if active_sub:
            start_at = active_sub.expires_at
            expires_at = start_at + timedelta(days=plan.duration_days)
            
            subscription = Subscription(
                user_id=user_id,
                plan_id=plan.id,
                status="ACTIVE",
                start_at=start_at,
                expires_at=expires_at,
                auto_renew=False
            )
            db.add(subscription)
            
            access = self.get_or_create_access(db, user_id)
            access.has_live_access = True
            access.has_ai_access = True
            access.max_live_trades += 100
            access.max_live_capital += 10000
        else:
            start_at = datetime.utcnow()
            expires_at = start_at + timedelta(days=plan.duration_days)
            
            subscription = Subscription(
                user_id=user_id,
                plan_id=plan.id,
                status="ACTIVE",
                start_at=start_at,
                expires_at=expires_at,
                auto_renew=False
            )
            db.add(subscription)
            
            access = self.get_or_create_access(db, user_id)
            access.has_live_access = True
            access.has_ai_access = True
            access.max_live_trades = 100
            access.max_live_capital = 10000
        
        if payment_id:
            payment = db.query(Payment).filter(Payment.id == payment_id).first()
            if payment:
                payment.subscription_id = subscription.id
        
        db.commit()
        db.refresh(subscription)
        
        logger.info(f"Subscription created for user {user_id}: {plan_code}")
        return subscription
    
    def record_payment(
        self,
        db: Session,
        user_id: str,
        payment_data: PaymentCreate
    ) -> Payment:
        existing = db.query(Payment).filter(
            Payment.transaction_hash == payment_data.transaction_hash
        ).first()
        
        if existing:
            raise ValueError("Payment already recorded")
        
        payment = Payment(
            user_id=user_id,
            amount_usdt=payment_data.amount_usdt,
            currency="USDT",
            network=payment_data.network,
            transaction_hash=payment_data.transaction_hash,
            from_address=payment_data.from_address,
            to_address=payment_data.to_address,
            status="PENDING",
            confirmations=0,
            required_confirmations=6
        )
        
        db.add(payment)
        db.commit()
        db.refresh(payment)
        
        logger.info(f"Payment recorded: {payment_data.transaction_hash}")
        return payment
    
    def verify_payment(
        self,
        db: Session,
        transaction_hash: str,
        expected_amount: Decimal,
        expected_network: str = "BEP20"
    ) -> Dict[str, Any]:
        payment = db.query(Payment).filter(
            Payment.transaction_hash == transaction_hash
        ).first()
        
        if not payment:
            return {'verified': False, 'message': 'Payment not found'}
        
        if payment.status == "COMPLETED":
            return {'verified': True, 'message': 'Payment already verified'}
        
        # Simulate verification
        if payment.amount_usdt == expected_amount and payment.network == expected_network:
            payment.status = "CONFIRMED"
            payment.confirmations = 6
            payment.verified_at = datetime.utcnow()
            db.commit()
            return {
                'verified': True,
                'message': 'Payment verified successfully',
                'confirmations': payment.confirmations
            }
        else:
            return {
                'verified': False,
                'message': 'Payment amount or network mismatch'
            }
    
    def check_expired_subscriptions(self, db: Session):
        now = datetime.utcnow()
        expired = db.query(Subscription).filter(
            Subscription.status == "ACTIVE",
            Subscription.expires_at <= now
        ).all()
        
        for subscription in expired:
            subscription.status = "EXPIRED"
            has_other = db.query(Subscription).filter(
                Subscription.user_id == subscription.user_id,
                Subscription.status == "ACTIVE",
                Subscription.id != subscription.id
            ).first()
            if not has_other:
                access = self.get_or_create_access(db, subscription.user_id)
                access.has_live_access = False
                access.has_ai_access = False
                access.max_live_trades = 0
        
        if expired:
            db.commit()
            logger.info(f"Expired {len(expired)} subscriptions")
        
        return expired
    
    def get_user_subscription(self, db: Session, user_id: str) -> Optional[Subscription]:
        return db.query(Subscription).filter(
            Subscription.user_id == user_id,
            Subscription.status == "ACTIVE"
        ).first()
    
    def get_subscription_history(self, db: Session, user_id: str) -> List[Subscription]:
        return db.query(Subscription).filter(
            Subscription.user_id == user_id
        ).order_by(Subscription.created_at.desc()).all()
    
    def get_payment_history(self, db: Session, user_id: str) -> List[Payment]:
        return db.query(Payment).filter(
            Payment.user_id == user_id
        ).order_by(Payment.created_at.desc()).all()
    
    def cancel_subscription(self, db: Session, user_id: str) -> Dict[str, Any]:
        subscription = self.get_user_subscription(db, user_id)
        if not subscription:
            return {'success': False, 'message': 'No active subscription found'}
        
        subscription.status = "CANCELLED"
        access = self.get_or_create_access(db, user_id)
        access.has_live_access = False
        access.has_ai_access = False
        
        db.commit()
        
        logger.info(f"Subscription cancelled for user {user_id}")
        return {'success': True, 'message': 'Subscription cancelled'}

subscription_service = SubscriptionService()
