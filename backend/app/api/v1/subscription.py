from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional

from ...core.database import get_db
from ...schemas.subscription import (
    PlanResponse, SubscriptionResponse, SubscriptionCreate,
    PaymentResponse, PaymentCreate, PaymentVerificationRequest,
    SubscriptionAccessResponse
)
from ...services.subscription_service import subscription_service
from ...api.dependencies import get_current_user
from ...models.user import User

router = APIRouter(prefix="/subscription", tags=["Subscription"])

@router.get("/plans", response_model=List[PlanResponse])
async def get_plans(
    db: Session = Depends(get_db),
):
    plans = subscription_service.get_plans(db)
    return plans

@router.get("/current", response_model=Optional[SubscriptionResponse])
async def get_current_subscription(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    subscription = subscription_service.get_user_subscription(db, current_user.id)
    return subscription

@router.get("/history", response_model=List[SubscriptionResponse])
async def get_subscription_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    subscriptions = subscription_service.get_subscription_history(db, current_user.id)
    return subscriptions

@router.get("/access", response_model=SubscriptionAccessResponse)
async def get_access(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    access = subscription_service.get_or_create_access(db, current_user.id)
    return access

@router.post("/create", response_model=SubscriptionResponse)
async def create_subscription(
    data: SubscriptionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        subscription = subscription_service.create_subscription(
            db, current_user.id, data.plan_code
        )
        return subscription
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/payment", response_model=PaymentResponse)
async def record_payment(
    payment_data: PaymentCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        payment = subscription_service.record_payment(db, current_user.id, payment_data)
        background_tasks.add_task(
            subscription_service.verify_payment,
            db,
            payment_data.transaction_hash,
            payment_data.amount_usdt,
            payment_data.network
        )
        return payment
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/verify-payment", response_model=dict)
async def verify_payment(
    verification: PaymentVerificationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    result = subscription_service.verify_payment(
        db,
        verification.transaction_hash,
        verification.amount_usdt,
        verification.network
    )
    return result

@router.get("/payments", response_model=List[PaymentResponse])
async def get_payment_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    payments = subscription_service.get_payment_history(db, current_user.id)
    return payments

@router.post("/cancel")
async def cancel_subscription(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    result = subscription_service.cancel_subscription(db, current_user.id)
    if not result['success']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result['message']
        )
    return result
