from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from decimal import Decimal
from datetime import datetime, timedelta
import math
import logging
from typing import Dict, Any, Optional, List, Tuple

from ..models.risk import RiskSettings, RiskEvent, CapitalTracker
from ..models.position import Position
from ..models.trade import Trade
from ..schemas.risk import RiskCheckRequest, PositionSizeRequest

logger = logging.getLogger(__name__)

class RiskService:
    """Risk management service for position sizing and risk limits."""
    
    # Correlation matrix for major assets (simplified)
    CORRELATIONS = {
        ('BTCUSDT', 'ETHUSDT'): 0.85,
        ('BTCUSDT', 'SOLUSDT'): 0.75,
        ('BTCUSDT', 'BNBUSDT'): 0.80,
        ('BTCUSDT', 'XRPUSDT'): 0.65,
        ('BTCUSDT', 'DOGEUSDT'): 0.60,
        ('BTCUSDT', 'ADAUSDT'): 0.70,
        ('ETHUSDT', 'SOLUSDT'): 0.80,
        ('ETHUSDT', 'BNBUSDT'): 0.85,
        ('ETHUSDT', 'XRPUSDT'): 0.70,
        ('ETHUSDT', 'DOGEUSDT'): 0.65,
        ('ETHUSDT', 'ADAUSDT'): 0.75,
    }
    
    @staticmethod
    def get_or_create_risk_settings(db: Session, user_id: str) -> RiskSettings:
        """Get or create risk settings for a user."""
        settings = db.query(RiskSettings).filter(RiskSettings.user_id == user_id).first()
        if not settings:
            settings = RiskSettings(user_id=user_id)
            db.add(settings)
            db.commit()
            db.refresh(settings)
        return settings
    
    @staticmethod
    def get_or_create_capital_tracker(db: Session, user_id: str) -> CapitalTracker:
        """Get or create capital tracker for a user."""
        tracker = db.query(CapitalTracker).filter(CapitalTracker.user_id == user_id).first()
        if not tracker:
            tracker = CapitalTracker(
                user_id=user_id,
                initial_capital=10000,
                protected_capital=5000,
                trading_capital=5000,
                reserve_capital=0
            )
            db.add(tracker)
            db.commit()
            db.refresh(tracker)
        return tracker
    
    @staticmethod
    def calculate_position_size(
        db: Session,
        user_id: str,
        request: PositionSizeRequest
    ) -> Dict[str, Any]:
        """
        Calculate position size using Kelly Criterion and risk management.
        """
        # Get risk settings
        settings = RiskService.get_or_create_risk_settings(db, user_id)
        
        # Determine risk percentage (use user's setting or request)
        risk_pct = float(request.risk_percent)
        if risk_pct > float(settings.max_risk_per_trade):
            risk_pct = float(settings.max_risk_per_trade)
        
        # Calculate position size using fixed fractional method
        # position_size = (capital * risk_pct) / (entry_price * stop_loss_pct)
        capital = float(request.capital)
        entry_price = float(request.entry_price)
        stop_loss_pct = float(request.stop_loss_pct) / 100
        
        # Basic position size
        position_size = (capital * (risk_pct / 100)) / (entry_price * stop_loss_pct)
        
        # Apply position size cap
        max_position_pct = float(settings.max_position_size_pct) / 100
        max_position_value = capital * max_position_pct
        max_position_size = max_position_value / entry_price
        
        if position_size > max_position_size:
            position_size = max_position_size
        
        # Calculate risk amount
        risk_amount = position_size * entry_price * stop_loss_pct
        
        # Calculate stop loss price
        stop_loss_price = entry_price * (1 - stop_loss_pct)
        
        # Calculate take profit levels (1:1, 2:1, 3:1)
        take_profit_1 = entry_price * (1 + stop_loss_pct)
        take_profit_2 = entry_price * (1 + stop_loss_pct * 2)
        take_profit_3 = entry_price * (1 + stop_loss_pct * 3)
        
        return {
            'position_size': Decimal(str(round(position_size, 8))),
            'risk_amount': Decimal(str(round(risk_amount, 2))),
            'stop_loss_price': Decimal(str(round(stop_loss_price, 2))),
            'take_profit_1': Decimal(str(round(take_profit_1, 2))),
            'take_profit_2': Decimal(str(round(take_profit_2, 2))),
            'take_profit_3': Decimal(str(round(take_profit_3, 2))),
            'max_loss': Decimal(str(round(risk_amount, 2)))
        }
    
    @staticmethod
    def check_risk_limits(
        db: Session,
        user_id: str,
        trade_request: RiskCheckRequest
    ) -> Dict[str, Any]:
        """
        Check if trade is within risk limits.
        """
        warnings = []
        is_allowed = True
        reason = None
        
        # Get risk settings and capital tracker
        settings = RiskService.get_or_create_risk_settings(db, user_id)
        tracker = RiskService.get_or_create_capital_tracker(db, user_id)
        
        # Check daily loss limit
        daily_loss_pct = float(tracker.daily_loss_count) / float(tracker.daily_start_capital) * 100 if tracker.daily_start_capital > 0 else 0
        if daily_loss_pct >= float(settings.max_risk_per_day):
            is_allowed = False
            reason = f"Daily loss limit reached ({daily_loss_pct:.2f}% >= {settings.max_risk_per_day}%)"
            warnings.append(reason)
        
        # Check weekly loss limit
        weekly_loss_pct = float(tracker.weekly_loss_count) / float(tracker.weekly_start_capital) * 100 if tracker.weekly_start_capital > 0 else 0
        if weekly_loss_pct >= float(settings.max_risk_per_week):
            is_allowed = False
            reason = f"Weekly loss limit reached ({weekly_loss_pct:.2f}% >= {settings.max_risk_per_week}%)"
            warnings.append(reason)
        
        # Check max drawdown
        if tracker.initial_capital > 0:
            drawdown_pct = float(tracker.total_pnl) / float(tracker.initial_capital) * 100
            if drawdown_pct <= -float(settings.max_drawdown):
                is_allowed = False
                reason = f"Max drawdown reached ({drawdown_pct:.2f}% <= -{settings.max_drawdown}%)"
                warnings.append(reason)
        
        # Check simultaneous trades
        open_positions = db.query(Position).filter(
            Position.user_id == user_id,
            Position.status == "OPEN"
        ).count()
        
        if open_positions >= settings.max_simultaneous_trades:
            is_allowed = False
            reason = f"Max simultaneous trades reached ({open_positions}/{settings.max_simultaneous_trades})"
            warnings.append(reason)
        
        # Check correlation with existing positions
        if is_allowed:
            correlation_warning = RiskService._check_correlation(
                db, user_id, trade_request.symbol, settings.correlation_limit
            )
            if correlation_warning:
                warnings.append(correlation_warning)
                # Allow but warn
        
        # Calculate risk score
        risk_score = RiskService._calculate_risk_score(
            db, user_id, trade_request, settings
        )
        
        # Check emergency shutdown
        if settings.emergency_shutdown_enabled and tracker.is_paused:
            is_allowed = False
            reason = "Emergency shutdown active"
            warnings.append(reason)
        
        return {
            'is_allowed': is_allowed,
            'reason': reason,
            'risk_score': Decimal(str(round(risk_score, 2))),
            'warnings': warnings
        }
    
    @staticmethod
    def _check_correlation(
        db: Session,
        user_id: str,
        new_symbol: str,
        correlation_limit: float
    ) -> Optional[str]:
        """Check correlation with existing positions."""
        open_positions = db.query(Position).filter(
            Position.user_id == user_id,
            Position.status == "OPEN"
        ).all()
        
        for pos in open_positions:
            pair = tuple(sorted([new_symbol, pos.symbol]))
            correlation = RiskService.CORRELATIONS.get(pair, 0.5)
            
            if correlation > float(correlation_limit):
                return f"High correlation ({correlation:.2f}) with existing position in {pos.symbol}"
        
        return None
    
    @staticmethod
    def _calculate_risk_score(
        db: Session,
        user_id: str,
        trade_request: RiskCheckRequest,
        settings: RiskSettings
    ) -> float:
        """Calculate risk score (0-100, higher = more risky)."""
        score = 0
        
        # Position size risk
        capital = 10000  # Default, should be from tracker
        position_value = float(trade_request.position_size) * float(trade_request.entry_price)
        capital_usage = position_value / capital * 100 if capital > 0 else 0
        if capital_usage > 20:
            score += 20
        elif capital_usage > 10:
            score += 10
        
        # Stop loss distance
        stop_loss_pct = abs(float(trade_request.stop_loss_price) / float(trade_request.entry_price) - 1) * 100
        if stop_loss_pct > 5:
            score += 20
        elif stop_loss_pct > 2:
            score += 10
        
        # Volatility (simplified)
        score += 10
        
        # Number of open positions
        open_positions = db.query(Position).filter(
            Position.user_id == user_id,
            Position.status == "OPEN"
        ).count()
        if open_positions > 3:
            score += 10
        
        return min(100, score)
    
    @staticmethod
    def update_capital_tracker(
        db: Session,
        user_id: str,
        pnl: Decimal,
        symbol: str = None
    ) -> CapitalTracker:
        """Update capital tracker with new PnL."""
        tracker = RiskService.get_or_create_capital_tracker(db, user_id)
        
        # Update totals
        tracker.total_pnl += pnl
        if pnl > 0:
            tracker.realized_profit += pnl
        else:
            # Track losses for daily/weekly limits
            tracker.daily_loss_count += abs(pnl)
            tracker.weekly_loss_count += abs(pnl)
        
        # Update trading capital
        tracker.trading_capital = tracker.initial_capital + tracker.total_pnl - tracker.protected_capital
        
        # Reset daily counters if new day
        if tracker.updated_at.date() < datetime.utcnow().date():
            tracker.daily_pnl = 0
            tracker.daily_start_capital = tracker.trading_capital
            tracker.daily_loss_count = 0
        
        # Reset weekly counters if new week
        if tracker.updated_at.isocalendar().week < datetime.utcnow().isocalendar().week:
            tracker.weekly_pnl = 0
            tracker.weekly_start_capital = tracker.trading_capital
            tracker.weekly_loss_count = 0
        
        db.commit()
        db.refresh(tracker)
        return tracker
    
    @staticmethod
    def emergency_shutdown(db: Session, user_id: str, reason: str):
        """Emergency shutdown of trading."""
        tracker = RiskService.get_or_create_capital_tracker(db, user_id)
        tracker.is_paused = True
        tracker.paused_reason = reason
        tracker.paused_at = datetime.utcnow()
        
        # Create risk event
        event = RiskEvent(
            user_id=user_id,
            event_type="EMERGENCY_SHUTDOWN",
            severity="CRITICAL",
            description=reason,
            action_taken="PAUSE_TRADING"
        )
        db.add(event)
        
        db.commit()
        db.refresh(tracker)
        logger.warning(f"Emergency shutdown triggered for user {user_id}: {reason}")
    
    @staticmethod
    def resume_trading(db: Session, user_id: str, notes: str = None):
        """Resume trading after pause."""
        tracker = RiskService.get_or_create_capital_tracker(db, user_id)
        tracker.is_paused = False
        tracker.paused_reason = None
        tracker.paused_at = None
        
        db.commit()
        db.refresh(tracker)
        logger.info(f"Trading resumed for user {user_id}")

# Create singleton
risk_service = RiskService()
