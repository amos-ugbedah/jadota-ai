from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from decimal import Decimal

from ...core.database import get_db
from ...schemas.risk import (
    RiskSettingsResponse, RiskSettingsUpdate,
    CapitalTrackerResponse, RiskEventResponse,
    PositionSizeRequest, PositionSizeResponse,
    RiskCheckRequest, RiskCheckResponse
)
from ...services.risk_service import risk_service
from ...services.demo_service import DemoService
from ...api.dependencies import get_current_user
from ...models.user import User

router = APIRouter(prefix="/risk", tags=["Risk Management"])

@router.get("/settings", response_model=RiskSettingsResponse)
async def get_risk_settings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get user's risk settings."""
    settings = risk_service.get_or_create_risk_settings(db, current_user.id)
    return settings

@router.put("/settings", response_model=RiskSettingsResponse)
async def update_risk_settings(
    update_data: RiskSettingsUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update user's risk settings."""
    settings = risk_service.get_or_create_risk_settings(db, current_user.id)
    
    for key, value in update_data.dict(exclude_unset=True).items():
        setattr(settings, key, value)
    
    db.commit()
    db.refresh(settings)
    return settings

@router.get("/capital", response_model=CapitalTrackerResponse)
async def get_capital_tracker(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get user's capital tracker."""
    tracker = risk_service.get_or_create_capital_tracker(db, current_user.id)
    return tracker

@router.post("/position-size", response_model=PositionSizeResponse)
async def calculate_position_size(
    request: PositionSizeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Calculate position size based on risk parameters."""
    result = risk_service.calculate_position_size(db, current_user.id, request)
    return result

@router.post("/check-trade", response_model=RiskCheckResponse)
async def check_trade_risk(
    request: RiskCheckRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Check if a trade is within risk limits."""
    result = risk_service.check_risk_limits(db, current_user.id, request)
    return result

@router.get("/events", response_model=List[RiskEventResponse])
async def get_risk_events(
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get user's risk events."""
    from ...models.risk import RiskEvent
    events = db.query(RiskEvent).filter(
        RiskEvent.user_id == current_user.id
    ).order_by(RiskEvent.created_at.desc()).limit(limit).all()
    return events

@router.post("/emergency-shutdown")
async def emergency_shutdown(
    reason: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Emergency shutdown of trading."""
    risk_service.emergency_shutdown(db, current_user.id, reason)
    return {"message": "Trading paused", "reason": reason}

@router.post("/resume-trading")
async def resume_trading(
    notes: str = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Resume trading after pause."""
    risk_service.resume_trading(db, current_user.id, notes)
    return {"message": "Trading resumed"}

@router.post("/reset-daily-limits")
async def reset_daily_limits(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Reset daily risk limits."""
    tracker = risk_service.get_or_create_capital_tracker(db, current_user.id)
    tracker.daily_pnl = 0
    tracker.daily_start_capital = tracker.trading_capital
    tracker.daily_loss_count = 0
    db.commit()
    return {"message": "Daily limits reset"}
