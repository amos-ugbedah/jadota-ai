from sqlalchemy.orm import Session
from decimal import Decimal
from datetime import datetime
import asyncio
import logging
from typing import Dict, Any, Optional, List

from ..models.live_trading import LiveAccount, LivePosition, LiveTrade
from ..models.exchange import ExchangeAccount, ExchangeOrder
from ..schemas.live_trading import ExecuteTradeRequest, ClosePositionRequest
from ..services.exchange_service import exchange_service
from ..services.risk_service import risk_service
from ..ai.consensus_engine import consensus_engine

logger = logging.getLogger(__name__)

class LiveTradingService:
    """Service for live trading execution."""
    
    def __init__(self):
        self.min_confidence = 60
        self.min_opportunity = 70
    
    async def create_live_account(
        self,
        db: Session,
        user_id: str,
        exchange_account_id: str,
        initial_capital: Decimal,
        protected_capital: Decimal
    ) -> LiveAccount:
        """Create a live trading account."""
        # Verify exchange account exists
        exchange_account = db.query(ExchangeAccount).filter(
            ExchangeAccount.id == exchange_account_id,
            ExchangeAccount.user_id == user_id,
            ExchangeAccount.is_active == True
        ).first()
        
        if not exchange_account:
            raise ValueError("Exchange account not found or inactive")
        
        # Create live account
        live_account = LiveAccount(
            user_id=user_id,
            exchange_account_id=exchange_account_id,
            initial_capital=initial_capital,
            protected_capital=protected_capital,
            trading_capital=initial_capital - protected_capital
        )
        
        db.add(live_account)
        db.commit()
        db.refresh(live_account)
        
        return live_account
    
    async def execute_trade(
        self,
        db: Session,
        user_id: str,
        trade_request: ExecuteTradeRequest
    ) -> Dict[str, Any]:
        """Execute a live trade based on AI signal."""
        # Get live account
        live_account = db.query(LiveAccount).filter(
            LiveAccount.user_id == user_id,
            LiveAccount.is_active == True,
            LiveAccount.is_paused == False
        ).first()
        
        if not live_account:
            raise ValueError("No active live account found or trading is paused")
        
        # Check if enough capital
        if trade_request.quantity * trade_request.entry_price > live_account.trading_capital:
            raise ValueError("Insufficient trading capital")
        
        # Check risk limits
        risk_check = await risk_service.check_risk_limits(
            db, user_id, {
                'symbol': trade_request.symbol,
                'side': trade_request.side,
                'entry_price': trade_request.entry_price,
                'stop_loss_price': trade_request.stop_loss_price,
                'position_size': trade_request.quantity
            }
        )
        
        if not risk_check['is_allowed']:
            raise ValueError(f"Risk check failed: {risk_check['reason']}")
        
        try:
            # Place order on exchange
            exchange_order = await exchange_service.place_order(
                db,
                user_id,
                {
                    'symbol': trade_request.symbol,
                    'side': 'BUY' if trade_request.side == 'LONG' else 'SELL',
                    'order_type': 'MARKET' if not trade_request.entry_price else 'LIMIT',
                    'quantity': trade_request.quantity,
                    'price': trade_request.entry_price
                }
            )
            
            # Create position in database
            position = LivePosition(
                user_id=user_id,
                live_account_id=live_account.id,
                symbol=trade_request.symbol,
                side=trade_request.side,
                entry_price=trade_request.entry_price or exchange_order.get('executed_price', 0),
                quantity=trade_request.quantity,
                notional_value=trade_request.quantity * (trade_request.entry_price or 1),
                stop_loss_price=trade_request.stop_loss_price,
                take_profit_price=trade_request.take_profit_price,
                ai_confidence=trade_request.ai_confidence,
                ai_reasoning=trade_request.ai_reasoning,
                entry_order_id=exchange_order.get('id'),
                risk_percent=Decimal('2.0'),
                risk_amount=trade_request.quantity * (trade_request.entry_price or 1) * Decimal('0.02')
            )
            
            db.add(position)
            
            # Update live account capital
            live_account.trading_capital -= trade_request.quantity * (trade_request.entry_price or 1)
            
            # Log the trade
            trade = LiveTrade(
                user_id=user_id,
                live_account_id=live_account.id,
                position_id=position.id,
                symbol=trade_request.symbol,
                side='BUY' if trade_request.side == 'LONG' else 'SELL',
                order_type='MARKET' if not trade_request.entry_price else 'LIMIT',
                quantity=trade_request.quantity,
                price=trade_request.entry_price,
                executed_price=exchange_order.get('executed_price', trade_request.entry_price),
                executed_quantity=exchange_order.get('executed_quantity', trade_request.quantity),
                status='EXECUTED',
                executed_at=datetime.utcnow(),
                exchange_order_id=exchange_order.get('exchange_order_id')
            )
            
            db.add(trade)
            db.commit()
            db.refresh(position)
            
            return {
                'position_id': position.id,
                'symbol': position.symbol,
                'side': position.side,
                'entry_price': float(position.entry_price),
                'quantity': float(position.quantity),
                'status': 'OPEN',
                'message': 'Trade executed successfully'
            }
            
        except Exception as e:
            logger.error(f"Trade execution failed: {e}")
            db.rollback()
            raise ValueError(f"Trade execution failed: {str(e)}")
    
    async def close_position(
        self,
        db: Session,
        user_id: str,
        close_request: ClosePositionRequest
    ) -> Dict[str, Any]:
        """Close an open position."""
        position = db.query(LivePosition).filter(
            LivePosition.id == close_request.position_id,
            LivePosition.user_id == user_id,
            LivePosition.status == "OPEN"
        ).first()
        
        if not position:
            raise ValueError("Position not found or already closed")
        
        try:
            # Determine closing side
            close_side = 'SELL' if position.side == 'LONG' else 'BUY'
            
            # Place closing order
            exchange_order = await exchange_service.place_order(
                db,
                user_id,
                {
                    'symbol': position.symbol,
                    'side': close_side,
                    'order_type': 'MARKET' if not close_request.close_price else 'LIMIT',
                    'quantity': position.quantity,
                    'price': close_request.close_price
                }
            )
            
            close_price = close_request.close_price or exchange_order.get('executed_price', 0)
            
            # Calculate PnL
            if position.side == 'LONG':
                pnl = (close_price - position.entry_price) * position.quantity
            else:
                pnl = (position.entry_price - close_price) * position.quantity
            
            # Update position
            position.status = "CLOSED"
            position.current_price = close_price
            position.closed_at = datetime.utcnow()
            position.realized_pnl = pnl
            position.exit_order_id = exchange_order.get('id')
            
            # Update live account
            live_account = db.query(LiveAccount).filter(
                LiveAccount.id == position.live_account_id
            ).first()
            
            if live_account:
                live_account.trading_capital += position.notional_value + pnl
                live_account.realized_profit += pnl
                live_account.total_pnl += pnl
                
                # Update risk tracker
                await risk_service.update_capital_tracker(db, user_id, pnl, position.symbol)
            
            # Log the trade
            trade = LiveTrade(
                user_id=user_id,
                live_account_id=live_account.id if live_account else None,
                position_id=position.id,
                symbol=position.symbol,
                side=close_side,
                order_type='MARKET' if not close_request.close_price else 'LIMIT',
                quantity=position.quantity,
                price=close_request.close_price,
                executed_price=exchange_order.get('executed_price', close_price),
                executed_quantity=exchange_order.get('executed_quantity', position.quantity),
                status='EXECUTED',
                executed_at=datetime.utcnow(),
                exchange_order_id=exchange_order.get('exchange_order_id')
            )
            
            db.add(trade)
            db.commit()
            db.refresh(position)
            
            return {
                'position_id': position.id,
                'symbol': position.symbol,
                'side': position.side,
                'entry_price': float(position.entry_price),
                'exit_price': float(close_price),
                'pnl': float(pnl),
                'pnl_percent': float((pnl / (position.entry_price * position.quantity)) * 100),
                'status': 'CLOSED'
            }
            
        except Exception as e:
            logger.error(f"Position close failed: {e}")
            db.rollback()
            raise ValueError(f"Position close failed: {str(e)}")
    
    async def update_positions(self, db: Session, symbol: str, current_price: Decimal):
        """Update all positions with current price."""
        positions = db.query(LivePosition).filter(
            LivePosition.symbol == symbol,
            LivePosition.status == "OPEN"
        ).all()
        
        for position in positions:
            position.current_price = current_price
            
            # Calculate unrealized PnL
            if position.side == "LONG":
                position.unrealized_pnl = (current_price - position.entry_price) * position.quantity
            else:
                position.unrealized_pnl = (position.entry_price - current_price) * position.quantity
            
            # Check stop loss
            if position.stop_loss_price:
                if position.side == "LONG" and current_price <= position.stop_loss_price:
                    await self.close_position(db, position.user_id, 
                        ClosePositionRequest(position_id=position.id, close_price=current_price))
                elif position.side == "SHORT" and current_price >= position.stop_loss_price:
                    await self.close_position(db, position.user_id,
                        ClosePositionRequest(position_id=position.id, close_price=current_price))
            
            # Check take profit
            if position.take_profit_price:
                if position.side == "LONG" and current_price >= position.take_profit_price:
                    await self.close_position(db, position.user_id,
                        ClosePositionRequest(position_id=position.id, close_price=current_price))
                elif position.side == "SHORT" and current_price <= position.take_profit_price:
                    await self.close_position(db, position.user_id,
                        ClosePositionRequest(position_id=position.id, close_price=current_price))
        
        db.commit()
        return positions
    
    async def get_open_positions(self, db: Session, user_id: str) -> List[LivePosition]:
        """Get all open positions for a user."""
        return db.query(LivePosition).filter(
            LivePosition.user_id == user_id,
            LivePosition.status == "OPEN"
        ).all()
    
    async def get_trade_history(self, db: Session, user_id: str, limit: int = 50) -> List[LiveTrade]:
        """Get trade history for a user."""
        return db.query(LiveTrade).filter(
            LiveTrade.user_id == user_id
        ).order_by(LiveTrade.created_at.desc()).limit(limit).all()

# Create singleton
live_trading_service = LiveTradingService()
