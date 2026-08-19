from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from decimal import Decimal
from datetime import datetime
from ..models.user import User
from ..models.demo_account import DemoAccount
from ..models.position import Position
from ..models.trade import Trade
from ..schemas.demo import CreatePosition, CreateTrade

class DemoService:
    @staticmethod
    def get_or_create_account(db: Session, user_id: str) -> DemoAccount:
        """Get or create a demo account for a user."""
        account = db.query(DemoAccount).filter(DemoAccount.user_id == user_id).first()
        if not account:
            account = DemoAccount(
                user_id=user_id,
                initial_balance=10000.00,
                current_balance=10000.00
            )
            db.add(account)
            db.commit()
            db.refresh(account)
        return account

    @staticmethod
    def get_account(db: Session, user_id: str) -> DemoAccount:
        """Get user's demo account."""
        return db.query(DemoAccount).filter(DemoAccount.user_id == user_id).first()

    @staticmethod
    def get_positions(db: Session, user_id: str, status: str = "OPEN") -> List[Position]:
        """Get user's positions."""
        return db.query(Position).filter(
            Position.user_id == user_id,
            Position.status == status
        ).all()

    @staticmethod
    def get_trades(db: Session, user_id: str, limit: int = 50) -> List[Trade]:
        """Get user's trade history."""
        return db.query(Trade).filter(
            Trade.user_id == user_id
        ).order_by(Trade.created_at.desc()).limit(limit).all()

    @staticmethod
    def open_position(db: Session, user_id: str, position_data: CreatePosition) -> Position:
        """Open a new position."""
        # Get account
        account = DemoService.get_or_create_account(db, user_id)
        
        # Calculate notional value
        notional_value = position_data.quantity * position_data.entry_price
        
        # Check if user has enough balance
        if notional_value > account.current_balance:
            raise ValueError("Insufficient balance")
        
        # Create position
        position = Position(
            user_id=user_id,
            account_id=account.id,
            symbol=position_data.symbol,
            side=position_data.side,
            entry_price=position_data.entry_price,
            current_price=position_data.entry_price,
            quantity=position_data.quantity,
            notional_value=notional_value,
            stop_loss_price=position_data.stop_loss_price,
            take_profit_price=position_data.take_profit_price,
            ai_confidence=position_data.ai_confidence,
            ai_reasoning=position_data.ai_reasoning,
            risk_percent=Decimal('2.0'),  # Default 2% risk
            risk_amount=notional_value * Decimal('0.02')
        )
        
        db.add(position)
        
        # Update account balance (deduct used capital)
        account.current_balance -= notional_value
        
        db.commit()
        db.refresh(position)
        db.refresh(account)
        
        return position

    @staticmethod
    def close_position(db: Session, user_id: str, position_id: str, close_price: Decimal) -> Position:
        """Close a position."""
        position = db.query(Position).filter(
            Position.id == position_id,
            Position.user_id == user_id,
            Position.status == "OPEN"
        ).first()
        
        if not position:
            raise ValueError("Position not found or already closed")
        
        # Calculate PnL
        if position.side == "LONG":
            pnl = (close_price - position.entry_price) * position.quantity
        else:  # SHORT
            pnl = (position.entry_price - close_price) * position.quantity
        
        # Update position
        position.status = "CLOSED"
        position.current_price = close_price
        position.closed_at = datetime.utcnow()
        position.realized_pnl = pnl
        
        # Get account and update balance
        account = db.query(DemoAccount).filter(DemoAccount.id == position.account_id).first()
        if account:
            # Return capital + PnL
            account.current_balance += position.notional_value + pnl
            account.total_pnl += pnl
            
            # Update performance metrics
            account.total_trades += 1
            if pnl > 0:
                account.winning_trades += 1
            else:
                account.losing_trades += 1
            
            # Update win rate
            if account.total_trades > 0:
                account.win_rate = (account.winning_trades / account.total_trades) * 100
            
            # Update total return
            account.total_return = ((account.current_balance - account.initial_balance) / account.initial_balance) * 100
            
            # Update profit factor
            # Simplified: total wins / total losses
            if account.losing_trades > 0:
                account.profit_factor = account.winning_trades / account.losing_trades
            else:
                account.profit_factor = account.winning_trades if account.winning_trades > 0 else 0
        
        db.commit()
        db.refresh(position)
        
        return position

    @staticmethod
    def update_positions(db: Session, symbol: str, current_price: Decimal):
        """Update all positions with current price."""
        positions = db.query(Position).filter(
            Position.symbol == symbol,
            Position.status == "OPEN"
        ).all()
        
        for position in positions:
            position.current_price = current_price
            
            # Calculate unrealized PnL
            if position.side == "LONG":
                position.unrealized_pnl = (current_price - position.entry_price) * position.quantity
            else:  # SHORT
                position.unrealized_pnl = (position.entry_price - current_price) * position.quantity
            
            # Check stop loss
            if position.stop_loss_price:
                if position.side == "LONG" and current_price <= position.stop_loss_price:
                    # Trigger stop loss
                    DemoService.close_position(db, position.user_id, position.id, current_price)
                elif position.side == "SHORT" and current_price >= position.stop_loss_price:
                    # Trigger stop loss
                    DemoService.close_position(db, position.user_id, position.id, current_price)
            
            # Check take profit
            if position.take_profit_price:
                if position.side == "LONG" and current_price >= position.take_profit_price:
                    # Trigger take profit
                    DemoService.close_position(db, position.user_id, position.id, current_price)
                elif position.side == "SHORT" and current_price <= position.take_profit_price:
                    # Trigger take profit
                    DemoService.close_position(db, position.user_id, position.id, current_price)
        
        db.commit()
        return positions
