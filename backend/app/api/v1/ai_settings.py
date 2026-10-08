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

# 🔥 NEW: strategy registry
from ...ai.strategies import list_strategies, get_strategy, strategy_names

router = APIRouter(prefix="/ai-settings", tags=["AI Settings"])


def _serialize_settings(settings: AISettings) -> dict:
    """
    Convert AISettings model to response dict with symbols as list.

    Fully defensive against:
      - NULL columns (legacy rows / incomplete migrations)
      - Wrong types (str stored in float column, etc.)
      - Out-of-range values that would fail Pydantic `ge`/`le` bounds

    Every field gets a safe default. Bounds match the schema in
    schemas/ai_settings.py exactly so validation can never fail here.
    """

    def _f(v, default, lo=None, hi=None):
        if v is None:
            return default
        try:
            v = float(v)
        except (TypeError, ValueError):
            return default
        if lo is not None and v < lo:
            return lo
        if hi is not None and v > hi:
            return hi
        return v

    def _i(v, default, lo=None, hi=None):
        if v is None:
            return default
        try:
            v = int(v)
        except (TypeError, ValueError):
            return default
        if lo is not None and v < lo:
            return lo
        if hi is not None and v > hi:
            return hi
        return v

    def _b(v, default=False):
        return default if v is None else bool(v)

    def _s(v, default=""):
        return default if v is None else str(v)

    # symbols — triple fallback (helper → manual split → hard default)
    symbols_list = None
    if settings.symbols is not None:
        try:
            symbols_list = settings.get_symbols_list()
        except Exception:
            try:
                symbols_list = [
                    s.strip() for s in str(settings.symbols).split(",") if s.strip()
                ]
            except Exception:
                symbols_list = None
    if not symbols_list:
        symbols_list = ["BTC/USDT", "ETH/USDT", "SOL/USDT", "BNB/USDT"]

    # timestamps — never return None for created_at
    from datetime import datetime as _dt
    created = settings.created_at or _dt.utcnow()
    updated = settings.updated_at or created

    return {
        "id": _s(settings.id),
        "user_id": _s(settings.user_id),
        "confidence_threshold": _f(settings.confidence_threshold, 70.0, 50, 90),
        "strategy_type": _s(settings.strategy_type, "balanced"),
        "trade_amount": _f(settings.trade_amount, 25.0, 1, 10000),
        "stop_loss_percent": _f(settings.stop_loss_percent, 2.0, 0.5, 10),
        "take_profit_percent": _f(settings.take_profit_percent, 4.0, 1, 20),
        "max_daily_loss": _f(settings.max_daily_loss, 5.0, 0.5, 30),
        "max_drawdown": _f(settings.max_drawdown, 15.0, 5, 50),
        "max_positions": _i(settings.max_positions, 5, 1, 20),
        "risk_per_trade": _f(settings.risk_per_trade, 2.0, 0.5, 5),
        "position_size_multiplier": _f(settings.position_size_multiplier, 1.0, 0.1, 3.0),
        "symbols": symbols_list,
        "auto_trade_enabled": _b(settings.auto_trade_enabled, False),
        "max_trades_per_day": _i(settings.max_trades_per_day, 10, 1, 50),
        "total_trades": _i(settings.total_trades, 0),
        "winning_trades": _i(settings.winning_trades, 0),
        "losing_trades": _i(settings.losing_trades, 0),
        "total_pnl": _f(settings.total_pnl, 0.0),
        "best_trade": _f(settings.best_trade, 0.0),
        "worst_trade": _f(settings.worst_trade, 0.0),
        "created_at": created,
        "updated_at": updated,
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


# ============================================
# 🔥 NEW: STRATEGIES — list & apply
# ============================================
@router.get("/strategies")
async def get_available_strategies():
    """List all available AI trading strategies with their defaults."""
    return {"strategies": list_strategies()}


@router.post("/apply-strategy/{name}")
async def apply_strategy(
    name: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Apply a strategy's defaults to the user's AI settings."""
    if name.lower() not in strategy_names():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unknown strategy: {name}. Available: {', '.join(strategy_names())}",
        )

    strat = get_strategy(name)

    settings = db.query(AISettings).filter(
        AISettings.user_id == current_user.id
    ).first()

    if not settings:
        settings = AISettings(user_id=current_user.id)
        db.add(settings)
        db.flush()

    defaults = strat.config
    settings.strategy_type = strat.NAME
    settings.confidence_threshold = defaults.get("confidence_threshold", 65)
    settings.stop_loss_percent = defaults.get("stop_loss_percent", 2.0)
    settings.take_profit_percent = defaults.get("take_profit_percent", 4.0)
    settings.position_size_multiplier = defaults.get("position_size_multiplier", 1.0)
    settings.max_positions = defaults.get("max_positions", 5)
    settings.max_trades_per_day = defaults.get("max_trades_per_day", 10)
    settings.risk_per_trade = defaults.get("risk_per_trade", 2.0)

    db.commit()
    db.refresh(settings)

    return {
        "success": True,
        "message": f"Applied {strat.LABEL} strategy",
        "strategy": strat.to_dict(),
        "settings": _serialize_settings(settings),
    }


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
    """Apply a strategy preset to user's settings (legacy — kept for backward compatibility)"""
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
    
    total = settings.total_trades or 0
    wins = settings.winning_trades or 0
    win_rate = (wins / total * 100) if total > 0 else 0
    
    return {
        "total_trades": total,
        "winning_trades": wins,
        "losing_trades": settings.losing_trades or 0,
        "win_rate": round(win_rate, 2),
        "total_pnl": round(settings.total_pnl or 0.0, 2),
        "best_trade": settings.best_trade or 0.0,
        "worst_trade": settings.worst_trade or 0.0
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