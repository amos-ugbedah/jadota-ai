from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from ...core.database import get_db
from ...schemas.exchange import (
    ExchangeAccountCreate, ExchangeAccountResponse,
    ExchangeBalanceResponse, ExchangeOrderCreate,
    ExchangeOrderResponse, ExchangeOrderCancelResponse
)
from ...services.exchange_service import exchange_service
from ...api.dependencies import get_current_user
from ...models.user import User

router = APIRouter(prefix="/exchange", tags=["Exchange Integration"])

@router.post("/connect", response_model=ExchangeAccountResponse)
async def connect_exchange(
    data: ExchangeAccountCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Connect a Bitget exchange account."""
    try:
        account = await exchange_service.create_account(db, current_user.id, data)
        return account
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/balance", response_model=List[ExchangeBalanceResponse])
async def get_balance(
    asset: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get exchange balance."""
    try:
        balances = await exchange_service.get_balance(db, current_user.id, asset)
        return balances
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/order", response_model=ExchangeOrderResponse)
async def place_order(
    order_data: ExchangeOrderCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Place an order on the exchange."""
    try:
        result = await exchange_service.place_order(db, current_user.id, order_data)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.delete("/order/{order_id}", response_model=ExchangeOrderCancelResponse)
async def cancel_order(
    order_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Cancel an order."""
    try:
        result = await exchange_service.cancel_order(db, current_user.id, order_id)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/order/{order_id}", response_model=ExchangeOrderResponse)
async def get_order_status(
    order_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get order status."""
    try:
        result = await exchange_service.get_order_status(db, current_user.id, order_id)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

@router.get("/account", response_model=ExchangeAccountResponse)
async def get_exchange_account(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get connected exchange account."""
    account = db.query(ExchangeAccount).filter(
        ExchangeAccount.user_id == current_user.id,
        ExchangeAccount.is_active == True
    ).first()
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active exchange account found"
        )
    
    return account

@router.delete("/disconnect")
async def disconnect_exchange(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Disconnect exchange account."""
    account = db.query(ExchangeAccount).filter(
        ExchangeAccount.user_id == current_user.id,
        ExchangeAccount.is_active == True
    ).first()
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active exchange account found"
        )
    
    account.is_active = False
    db.commit()
    
    return {"message": "Exchange account disconnected"}
