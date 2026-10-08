"""
Payment endpoints — user-facing + admin.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List

from ...core.database import SessionLocal
from ...core.security import decode_token, get_token_from_header
from ...models.user import User
from ...models.payment import Payment, PaymentStatus
from ...schemas.payment import (
    PaymentCreateRequest,
    PaymentResponse,
    PaymentVerifyResponse,
    AdminApproveRequest,
)
from ...services.payment_service import (
    get_plan_price,
    get_receiving_wallet,
    verify_usdt_payment,
    activate_subscription,
    PAYMENT_WINDOW_MINUTES,
)

router = APIRouter(prefix="/payments", tags=["Payments"])


# ============================================
# Dependencies
# ============================================
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_current_user(
    authorization: str = Header(None),
    db: Session = Depends(get_db),
):
    token = get_token_from_header(authorization)
    if not token:
        raise HTTPException(status_code=401, detail="Missing authorization header")
    payload = decode_token(token)
    if not payload or not payload.get("sub"):
        raise HTTPException(status_code=401, detail="Invalid token")
    user = db.query(User).filter(User.id == payload["sub"]).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")
    return user


async def require_admin(
    authorization: str = Header(None),
    db: Session = Depends(get_db),
):
    user = await get_current_user(authorization=authorization, db=db)
    if user.role not in ("ADMIN", "SUPER_ADMIN"):
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


# ============================================
# USER ENDPOINTS
# ============================================
@router.post("/create", response_model=PaymentResponse)
async def create_payment(
    body: PaymentCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new pending payment for a subscription upgrade."""
    plan_key = body.plan.lower()
    amount = get_plan_price(plan_key)

    if amount <= 0:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid plan: {body.plan}. Choose 'pro' or 'enterprise'.",
        )

    # Reuse an existing pending payment if one is still valid
    existing = (
        db.query(Payment)
        .filter(
            Payment.user_id == current_user.id,
            Payment.status == PaymentStatus.PENDING,
            Payment.plan == plan_key.upper(),
            Payment.expires_at > datetime.utcnow(),
        )
        .order_by(Payment.created_at.desc())
        .first()
    )
    if existing:
        return existing

    network = "BEP20"
    payment = Payment(
        user_id=current_user.id,
        plan=plan_key.upper(),
        months=body.months,
        amount_usdt=amount,
        network=network,
        wallet_address=get_receiving_wallet(network),
        status=PaymentStatus.PENDING,
        expires_at=datetime.utcnow() + timedelta(minutes=PAYMENT_WINDOW_MINUTES),
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)
    return payment


@router.get("/{payment_id}", response_model=PaymentResponse)
async def get_payment(
    payment_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a specific payment's details."""
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    if payment.user_id != current_user.id and current_user.role not in ("ADMIN", "SUPER_ADMIN"):
        raise HTTPException(status_code=403, detail="Access denied")
    return payment


@router.post("/{payment_id}/verify", response_model=PaymentVerifyResponse)
async def verify_payment(
    payment_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Check the blockchain for the user's payment.
    If a matching tx is found, activate the subscription.
    """
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    if payment.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    if payment.status == PaymentStatus.COMPLETED:
        return PaymentVerifyResponse(
            success=True,
            status=payment.status,
            message="Payment already confirmed",
            tx_hash=payment.tx_hash,
        )

    if payment.status != PaymentStatus.PENDING:
        return PaymentVerifyResponse(
            success=False,
            status=payment.status,
            message=f"Payment is {payment.status} and cannot be verified",
        )

    if datetime.utcnow() > payment.expires_at:
        payment.status = PaymentStatus.EXPIRED
        db.commit()
        return PaymentVerifyResponse(
            success=False,
            status=payment.status,
            message="Payment window expired. Please create a new payment.",
        )

    # Mark as verifying
    payment.status = PaymentStatus.VERIFYING
    db.commit()

    tx_hash = await verify_usdt_payment(
        wallet_address=payment.wallet_address,
        expected_amount=payment.amount_usdt,
        created_at=payment.created_at,
        network=payment.network,
    )

    if not tx_hash:
        # Revert to pending — user can retry or admin can approve manually
        payment.status = PaymentStatus.PENDING
        db.commit()
        return PaymentVerifyResponse(
            success=False,
            status=payment.status,
            message=(
                "No matching payment found yet on-chain. "
                "If you've already sent it, wait 1-2 minutes and try again. "
                "Otherwise, contact support with your transaction hash."
            ),
        )

    # Success
    payment.tx_hash = tx_hash
    payment.status = PaymentStatus.COMPLETED
    payment.verified_at = datetime.utcnow()
    payment.completed_at = datetime.utcnow()

    activate_subscription(current_user, payment.plan, payment.months)
    db.commit()
    db.refresh(payment)

    return PaymentVerifyResponse(
        success=True,
        status=payment.status,
        message=f"Payment confirmed! {payment.plan} plan activated.",
        tx_hash=tx_hash,
    )


@router.post("/{payment_id}/cancel", response_model=PaymentResponse)
async def cancel_payment(
    payment_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    if payment.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    if payment.status != PaymentStatus.PENDING:
        raise HTTPException(status_code=400, detail=f"Cannot cancel a {payment.status} payment")

    payment.status = PaymentStatus.CANCELLED
    db.commit()
    db.refresh(payment)
    return payment


@router.get("/", response_model=List[PaymentResponse])
async def list_my_payments(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List the current user's payment history (newest first)."""
    return (
        db.query(Payment)
        .filter(Payment.user_id == current_user.id)
        .order_by(Payment.created_at.desc())
        .limit(50)
        .all()
    )


# ============================================
# ADMIN ENDPOINTS
# ============================================
@router.get("/admin/all", response_model=List[PaymentResponse])
async def admin_list_payments(
    status_filter: str = None,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """List all payments (admin). Optionally filter by status."""
    q = db.query(Payment)
    if status_filter:
        q = q.filter(Payment.status == status_filter)
    return q.order_by(Payment.created_at.desc()).limit(200).all()


@router.post("/admin/{payment_id}/approve", response_model=PaymentVerifyResponse)
async def admin_approve_payment(
    payment_id: str,
    body: AdminApproveRequest,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Manually approve a payment (fallback when auto-verification fails).
    Activates the subscription immediately.
    """
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    if payment.status == PaymentStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Payment already completed")

    target_user = db.query(User).filter(User.id == payment.user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="Payment's user no longer exists")

    payment.tx_hash = body.tx_hash or payment.tx_hash
    payment.admin_notes = body.admin_notes
    payment.status = PaymentStatus.COMPLETED
    payment.verified_at = datetime.utcnow()
    payment.completed_at = datetime.utcnow()

    activate_subscription(target_user, payment.plan, payment.months)
    db.commit()

    return PaymentVerifyResponse(
        success=True,
        status=payment.status,
        message=f"Payment approved. {payment.plan} activated for {target_user.email}.",
        tx_hash=payment.tx_hash,
    )


@router.post("/admin/{payment_id}/reject", response_model=PaymentResponse)
async def admin_reject_payment(
    payment_id: str,
    body: AdminApproveRequest,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    payment.status = PaymentStatus.FAILED
    payment.admin_notes = body.admin_notes or "Rejected by admin"
    db.commit()
    db.refresh(payment)
    return payment