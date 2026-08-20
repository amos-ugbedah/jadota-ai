from sqlalchemy.orm import Session
from decimal import Decimal
from datetime import datetime
import asyncio
import logging
from typing import Dict, Any, Optional, List

from ..models.live_trading import LiveAccount, LivePosition, LiveTrade
from ..models.exchange import ExchangeAccount
from ..schemas.live_trading import ExecuteTradeRequest, ClosePositionRequest
from ..services.exchange_service import exchange_service
from ..services.risk_service import risk_service

logger = logging.getLogger(__name__)

class LiveTradingService:
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
        exchange_account = db.query(ExchangeAccount).filter(
            ExchangeAccount.id == exchange_account_id,
            ExchangeAccount.user_id == user_id,
            ExchangeAccount.is_active == True
        ).first()
        
        if not exchange_account:
            raise ValueError("Exchange account not found or inactive")
        
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
        live_account = db.query(LiveAccount).filter(
            LiveAccount.user_id == user_id,
            LiveAccount.is_active == True,
            LiveAccount.is_paused == False
        ).first()
        
        if not live_account:
            raise ValueError("No active live account found or trading is paused")
        
        if trade_request.quantity * trade_request.entry_price > live_account.trading_capital:
            raise ValueError("Insufficient trading capital")
        
        try:
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
            live_account.trading_capital -= trade_request.quantity * (trade_request.entry_price or 1)
            
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
        position = db.query(LivePosition).filter(
            LivePosition.id == close_request.position_id,
            LivePosition.user_id == user_id,
            LivePosition.status == "OPEN"
        ).first()
        
        if not position:
            raise ValueError("Position not found or already closed")
        
        try:
            close_side = 'SELL' if position.side == 'LONG' else 'BUY'
            
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
            
            if position.side == 'LONG':
                pnl = (close_price - position.entry_price) * position.quantity
            else:
                pnl = (position.entry_price - close_price) * position.quantity
            
            position.status = "CLOSED"
            position.current_price = close_price
            position.closed_at = datetime.utcnow()
            position.realized_pnl = pnl
            position.exit_order_id = exchange_order.get('id')
            
            live_account = db.query(LiveAccount).filter(
                LiveAccount.id == position.live_account_id
            ).first()
            
            if live_account:
                live_account.trading_capital += position.notional_value + pnl
                live_account.realized_profit += pnl
                live_account.total_pnl += pnl
                
                await risk_service.update_capital_tracker(db, user_id, pnl, position.symbol)
            
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
    
    async def get_open_positions(self, db: Session, user_id: str) -> List[LivePosition]:
        return db.query(LivePosition).filter(
            LivePosition.user_id == user_id,
            LivePosition.status == "OPEN"
        ).all()
    
    async def get_trade_history(self, db: Session, user_id: str, limit: int = 50) -> List[LiveTrade]:
        return db.query(LiveTrade).filter(
            LiveTrade.user_id == user_id
        ).order_by(LiveTrade.created_at.desc()).limit(limit).all()

live_trading_service = LiveTradingService()
