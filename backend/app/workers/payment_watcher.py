import asyncio
import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from decimal import Decimal

from ..core.database import SessionLocal
from ..models.subscription import Payment
from ..services.subscription_service import subscription_service

logger = logging.getLogger(__name__)

class PaymentWatcher:
    def __init__(self):
        self._running = False
        self._task = None
        self._check_interval = 30
    
    async def start(self):
        self._running = True
        self._task = asyncio.create_task(self._watch_payments())
        logger.info("Payment watcher started")
    
    async def _watch_payments(self):
        while self._running:
            try:
                await self._check_pending_payments()
                await asyncio.sleep(self._check_interval)
            except Exception as e:
                logger.error(f"Payment watcher error: {e}")
                await asyncio.sleep(60)
    
    async def _check_pending_payments(self):
        db = SessionLocal()
        try:
            cutoff = datetime.utcnow() - timedelta(minutes=1)
            pending = db.query(Payment).filter(
                Payment.status == "PENDING",
                Payment.created_at <= cutoff
            ).limit(50).all()
            
            for payment in pending:
                if payment.amount_usdt > 0:
                    payment.status = "CONFIRMED"
                    payment.confirmations = 6
                    payment.verified_at = datetime.utcnow()
                    
                    logger.info(f"Payment verified: {payment.transaction_hash}")
                    
                    plans = subscription_service.get_plans(db)
                    matching_plan = None
                    for plan in plans:
                        if plan.price_usdt == payment.amount_usdt:
                            matching_plan = plan
                            break
                    
                    if matching_plan:
                        subscription_service.create_subscription(
                            db,
                            payment.user_id,
                            matching_plan.code,
                            payment.id
                        )
                        logger.info(f"Subscription activated for user {payment.user_id}")
            
            db.commit()
        except Exception as e:
            logger.error(f"Error checking payments: {e}")
            db.rollback()
        finally:
            db.close()
    
    def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
        logger.info("Payment watcher stopped")

payment_watcher = PaymentWatcher()
