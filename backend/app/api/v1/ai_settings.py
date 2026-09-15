"""
AI Settings API Endpoints - Professional Trading Configuration
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from ...core.database import get_db
from ...models.user import User
from ...models.ai_settings import AISettings
from ...api.dependencies import get_current_user
from ...schemas.ai_settings import (
    AISettingsResponse,
    AISettingsUpdate,
    StrategyPreset
)

router = APIRouter(prefix="/ai-settings", tags=["AI Settings"])

def _serialize_settings(settings: AISettings) -> dict:
    """Convert AISettings model to response dict with symbols as list"""
    return {
        "id": settings.id,
        "user_id": settings.user_id,
        "confidence_threshold": settings.confidence_threshold,
        "strategy_type": settings.strategy_type,
        "trade_amount": settings.trade_amount,
        "stop_loss_percent": settings.stop_loss_percent,
        "take_profit_percent": settings.take_profit_percent,
        "max_daily_loss": settings.max_daily_loss,
        "max_drawdown": settings.max_drawdown,
        "max_positions": settings.max_positions,
        "risk_per_trade": settings.risk_per_trade,
        "position_size_multiplier": settings.position_size_multiplier,
        "symbols": settings.get_symbols_list(),
        "auto_trade_enabled": settings.auto_trade_enabled,
        "max_trades_per_day": settings.max_trades_per_day,
        "total_trades": settings.total_trades,
        "winning_trades": settings.winning_trades,
        "losing_trades": settings.losing_trades,
        "total_pnl": settings.total_pnl,
        "best_trade": settings.best_trade,
        "worst_trade": settings.worst_trade,
        "created_at": settings.created_at,
        "updated_at": settings.updated_at,
    }

@router.get("/", response_model=AISettingsResponse)
async def get_ai_settings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's AI settings with defaults if not exists"""
    settings = db.query(AISettings).filter(
        AISettings.user_id == current_user.id
    ).first()
    
    if not settings:
        settings = AISettings(
            user_id=current_user.id,
            confidence_threshold=70.0,
            trade_amount=25.0,
            stop_loss_percent=2.0,
            take_profit_percent=4.0,
            position_size_multiplier=1.0,
            symbols='BTC/USDT,ETH/USDT,SOL/USDT,BNB/USDT',
            max_positions=5,
            auto_trade_enabled=False,
            max_daily_loss=5.0,
            max_drawdown=15.0,
            strategy_type='balanced',
            risk_per_trade=2.0,
            max_trades_per_day=10
        )
        db.add(settings)
        db.commit()
        db.refresh(settings)
    
    return _serialize_settings(settings)

@router.put("/", response_model=AISettingsResponse)
async def update_ai_settings(
    update_data: AISettingsUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update AI settings"""
    settings = db.query(AISettings).filter(
        AISettings.user_id == current_user.id
    ).first()
    
    if not settings:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Settings not found"
        )
    
    update_dict = update_data.dict(exclude_unset=True)
    
    if 'symbols' in update_dict and isinstance(update_dict['symbols'], list):
        update_dict['symbols'] = ','.join(update_dict['symbols'])
    
    for key, value in update_dict.items():
        setattr(settings, key, value)
    
    db.commit()
    db.refresh(settings)
    
    return _serialize_settings(settings)

@router.get("/presets", response_model=List[StrategyPreset])
async def get_strategy_presets():
    """Get available strategy presets"""
    return [
        {
            "type": "conservative",
            "label": "🛡️ Conservative",
            "description": "High confidence, tight stop-loss, smaller positions",
            "icon": "shield",
            "risk_level": "Low",
            "settings": {
                "confidence_threshold": 80,
                "stop_loss_percent": 1.5,
                "take_profit_percent": 3.0,
                "position_size_multiplier": 0.7,
                "max_positions": 3,
                "trade_amount": 10
            }
        },
        {
            "type": "balanced",
            "label": "⚖️ Balanced",
            "description": "Balanced risk-reward with moderate position sizing",
            "icon": "scale",
            "risk_level": "Medium",
            "settings": {
                "confidence_threshold": 70,
                "stop_loss_percent": 2.0,
                "take_profit_percent": 4.0,
                "position_size_multiplier": 1.0,
                "max_positions": 5,
                "trade_amount": 25
            }
        },
        {
            "type": "aggressive",
            "label": "⚡ Aggressive",
            "description": "Lower confidence threshold, wider stops, larger positions",
            "icon": "zap",
            "risk_level": "High",
            "settings": {
                "confidence_threshold": 60,
                "stop_loss_percent": 3.0,
                "take_profit_percent": 6.0,
                "position_size_multiplier": 1.5,
                "max_positions": 8,
                "trade_amount": 50
            }
        }
    ]

@router.get("/symbols")
async def get_available_symbols():
    """Get all available trading symbols"""
    return [
        {"symbol": "BTC/USDT", "name": "Bitcoin", "icon": "₿"},
        {"symbol": "ETH/USDT", "name": "Ethereum", "icon": "⟠"},
        {"symbol": "SOL/USDT", "name": "Solana", "icon": "◎"},
        {"symbol": "BNB/USDT", "name": "BNB", "icon": "◆"},
        {"symbol": "XRP/USDT", "name": "Ripple", "icon": "✕"},
        {"symbol": "DOGE/USDT", "name": "Dogecoin", "icon": "Ð"},
        {"symbol": "ADA/USDT", "name": "Cardano", "icon": "₳"}
    ]

@router.post("/apply-preset/{preset_type}")
async def apply_strategy_preset(
    preset_type: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Apply a strategy preset to user's settings"""
    settings = db.query(AISettings).filter(
        AISettings.user_id == current_user.id
    ).first()
    
    if not settings:
        settings = AISettings(user_id=current_user.id)
        db.add(settings)
    
    presets = settings.get_preset_values(preset_type)
    settings.strategy_type = preset_type
    for key, value in presets.items():
        setattr(settings, key, value)
    
    db.commit()
    db.refresh(settings)
    
    return {
        "message": f"Applied {preset_type} strategy preset",
        "settings": _serialize_settings(settings)
    }

@router.get("/performance-stats")
async def get_ai_performance_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get AI trading performance statistics"""
    settings = db.query(AISettings).filter(
        AISettings.user_id == current_user.id
    ).first()
    
    if not settings:
        return {
            "total_trades": 0, "winning_trades": 0, "losing_trades": 0,
            "win_rate": 0, "total_pnl": 0, "best_trade": 0, "worst_trade": 0
        }
    
    win_rate = (settings.winning_trades / settings.total_trades * 100) if settings.total_trades > 0 else 0
    
    return {
        "total_trades": settings.total_trades,
        "winning_trades": settings.winning_trades,
        "losing_trades": settings.losing_trades,
        "win_rate": round(win_rate, 2),
        "total_pnl": round(settings.total_pnl, 2),
        "best_trade": settings.best_trade,
        "worst_trade": settings.worst_trade
    }

@router.post("/toggle-auto-trade")
async def toggle_auto_trade(
    enabled: bool,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Enable/disable auto-trading"""
    settings = db.query(AISettings).filter(
        AISettings.user_id == current_user.id
    ).first()
    
    if not settings:
        settings = AISettings(user_id=current_user.id)
        db.add(settings)
    
    settings.auto_trade_enabled = enabled
    db.commit()
    
    return {
        "auto_trade_enabled": settings.auto_trade_enabled,
        "message": f"Auto-trade {'enabled' if enabled else 'disabled'}"
    }