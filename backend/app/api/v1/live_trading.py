from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from decimal import Decimal

from ...core.database import get_db
from ...schemas.live_trading import (
    LiveAccountCreate, LiveAccountResponse,
    LivePositionResponse, LiveTradeResponse,
    ExecuteTradeRequest, ClosePositionRequest
)
from ...services.live_trading_service import live_trading_service
from ...api.dependencies import get_current_user
from ...models.user import User

router = APIRouter(prefix="/live", tags=["Live Trading"])

@router.post("/account", response_model=LiveAccountResponse)
async def create_live_account(
    data: LiveAccountCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a live trading account."""
    try:
        account = await live_trading_service.create_live_account(
            db,
            current_user.id,
            data.exchange_account_id,
            data.initial_capital,
            data.protected_capital
        )
        return account
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/account", response_model=LiveAccountResponse)
async def get_live_account(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get live trading account."""
    account = db.query(LiveAccount).filter(
        LiveAccount.user_id == current_user.id,
        LiveAccount.is_active == True
    ).first()
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active live account found"
        )
    
    return account

@router.get("/positions", response_model=List[LivePositionResponse])
async def get_open_positions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get open positions."""
    positions = await live_trading_service.get_open_positions(db, current_user.id)
    return positions

@router.get("/trades", response_model=List[LiveTradeResponse])
async def get_trade_history(
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get trade history."""
    trades = await live_trading_service.get_trade_history(db, current_user.id, limit)
    return trades

@router.post("/execute", response_model=dict)
async def execute_trade(
    trade_request: ExecuteTradeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Execute a live trade."""
    try:
        result = await live_trading_service.execute_trade(
            db, current_user.id, trade_request
        )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/close", response_model=dict)
async def close_position(
    close_request: ClosePositionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Close an open position."""
    try:
        result = await live_trading_service.close_position(
            db, current_user.id, close_request
        )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/pause")
async def pause_trading(
    reason: str = "Manual pause",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Pause live trading."""
    account = db.query(LiveAccount).filter(
        LiveAccount.user_id == current_user.id,
        LiveAccount.is_active == True
    ).first()
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active live account found"
        )
    
    account.is_paused = True
    account.paused_reason = reason
    db.commit()
    
    return {"message": f"Trading paused: {reason}"}

@router.post("/resume")
async def resume_trading(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Resume live trading."""
    account = db.query(LiveAccount).filter(
        LiveAccount.user_id == current_user.id,
        LiveAccount.is_active == True
    ).first()
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active live account found"
        )
    
    account.is_paused = False
    account.paused_reason = None
    db.commit()
    
    return {"message": "Trading resumed"}
