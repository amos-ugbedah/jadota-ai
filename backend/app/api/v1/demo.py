from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from ...core.database import get_db
from ...schemas.demo import (
    DemoAccountResponse, CreatePosition, PositionResponse,
    CreateTrade, TradeResponse, PerformanceMetrics
)
from ...services.demo_service import DemoService
from ...api.dependencies import get_current_user
from ...models.user import User

router = APIRouter(prefix="/demo", tags=["Demo Trading"])

@router.get("/account", response_model=DemoAccountResponse)
async def get_demo_account(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get user's demo account."""
    account = DemoService.get_or_create_account(db, current_user.id)
    return account

@router.get("/positions", response_model=List[PositionResponse])
async def get_positions(
    status: str = "OPEN",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get user's positions."""
    positions = DemoService.get_positions(db, current_user.id, status)
    return positions

@router.get("/trades", response_model=List[TradeResponse])
async def get_trades(
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get user's trade history."""
    trades = DemoService.get_trades(db, current_user.id, limit)
    return trades

@router.post("/positions", response_model=PositionResponse, status_code=status.HTTP_201_CREATED)
async def open_position(
    position_data: CreatePosition,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Open a new position."""
    try:
        position = DemoService.open_position(db, current_user.id, position_data)
        return position
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

@router.post("/positions/{position_id}/close", response_model=PositionResponse)
async def close_position(
    position_id: str,
    close_price: float,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Close a position."""
    try:
        position = DemoService.close_position(
            db, 
            current_user.id, 
            position_id, 
            Decimal(str(close_price))
        )
        return position
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

@router.get("/performance", response_model=PerformanceMetrics)
async def get_performance(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get user's performance metrics."""
    account = DemoService.get_account(db, current_user.id)
    if not account:
        return PerformanceMetrics(
            total_pnl=0,
            total_return=0,
            win_rate=0,
            profit_factor=0,
            max_drawdown=0,
            sharpe_ratio=0,
            total_trades=0,
            winning_trades=0,
            losing_trades=0
        )
    
    return PerformanceMetrics(
        total_pnl=account.total_pnl,
        total_return=account.total_return,
        win_rate=account.win_rate,
        profit_factor=account.profit_factor,
        max_drawdown=account.max_drawdown,
        sharpe_ratio=account.sharpe_ratio,
        total_trades=account.total_trades,
        winning_trades=account.winning_trades,
        losing_trades=account.losing_trades
    )

@router.post("/reset")
async def reset_demo_account(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Reset demo account to initial state."""
    account = DemoService.get_account(db, current_user.id)
    if account:
        # Close all open positions
        positions = DemoService.get_positions(db, current_user.id, "OPEN")
        for position in positions:
            DemoService.close_position(db, current_user.id, position.id, position.current_price or position.entry_price)
        
        # Reset account
        account.current_balance = account.initial_balance
        account.total_pnl = 0
        account.total_return = 0
        account.win_rate = 0
        account.profit_factor = 0
        account.max_drawdown = 0
        account.sharpe_ratio = 0
        account.total_trades = 0
        account.winning_trades = 0
        account.losing_trades = 0
        
        db.commit()
        db.refresh(account)
    
    return {"message": "Demo account reset successfully"}
