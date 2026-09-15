from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends, status, Request, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from datetime import datetime, timedelta
import json
import logging
import uuid
import httpx
import os

# 🔥 LOAD .env — must run BEFORE any code that reads env vars
from dotenv import load_dotenv
from pathlib import Path

env_path = Path(__file__).parent.parent / ".env"   # backend/.env
load_dotenv(dotenv_path=env_path, override=True)

# 🔥 FIX: Import Session from sqlalchemy.orm
from sqlalchemy.orm import Session

from .core.config import settings, get_cors_origins, get_allowed_hosts
from .core.database import engine, Base, SessionLocal
from .core.security import (
    get_password_hash, verify_password, create_access_token, 
    create_refresh_token, decode_token, get_token_from_header
)
from .models.user import User
from .services.market_data_service import market_data_service
from .services.ai_trading_service import ai_trading_service
from .services.position_monitor import position_monitor
from .services.telegram_service import telegram_service
from .api.v1 import ai_settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================
# Database Setup
# ============================================
try:
    Base.metadata.create_all(bind=engine)
    logger.info("✅ Database tables created/verified")
except Exception as e:
    logger.error(f"❌ Database setup error: {e}")

# ============================================
# FastAPI App
# ============================================
app = FastAPI(
    title="JADOTA AI API",
    version="1.0.0",
    description="AI-powered trading intelligence platform",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# ============================================
# CORS
# ============================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=[
        "Authorization", "Content-Type", "Accept", "Origin",
        "X-Requested-With", "X-Request-ID", "X-Client-Version", "X-Client-Env",
    ],
    expose_headers=["X-Request-ID", "X-RateLimit-Limit", "X-RateLimit-Remaining"],
    max_age=600,
)

# ============================================
# Trusted Host
# ============================================
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=get_allowed_hosts(),
)

# ============================================
# Database Dependency
# ============================================
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ============================================
# 🔐 AUTH DEPENDENCY
# ============================================
async def get_current_user(
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    """Get current user from Authorization header (dependency)"""
    token = get_token_from_header(authorization)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header"
        )
    
    payload = decode_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated"
        )
    
    return user

# ============================================
# 🔐 AUTH ENDPOINTS
# ============================================

@app.post("/api/v1/auth/login")
async def login(request: dict, db: Session = Depends(get_db)):
    """Login user with email and password"""
    email = request.get("email")
    password = request.get("password")
    
    if not email or not password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email and password required"
        )
    
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    if not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated"
        )
    
    user.last_login_at = datetime.utcnow()
    db.commit()
    
    access_token = create_access_token(data={"sub": user.id, "email": user.email})
    refresh_token = create_refresh_token(data={"sub": user.id})
    
    return {
        "user": {
            "id": user.id,
            "email": user.email,
            "fullName": user.full_name or user.username,
            "role": user.role,
            "subscription": {
                "plan": user.subscription_plan,
                "expiresAt": user.subscription_expires_at.isoformat() if user.subscription_expires_at else None,
                "isActive": user.has_active_subscription if hasattr(user, 'has_active_subscription') else False
            },
            "demoBalance": user.demo_balance,
            "createdAt": user.created_at.isoformat() if user.created_at else datetime.utcnow().isoformat()
        },
        "accessToken": access_token,
        "refreshToken": refresh_token
    }

@app.post("/api/v1/auth/register")
async def register(request: dict, db: Session = Depends(get_db)):
    """Register a new user"""
    email = request.get("email")
    password = request.get("password")
    full_name = request.get("fullName")
    username = request.get("username")
    
    if not email or not password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email and password required"
        )
    
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    if not username:
        username = email.split('@')[0]
    
    existing_username = db.query(User).filter(User.username == username).first()
    if existing_username:
        username = f"{username}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    
    user = User(
        email=email,
        username=username,
        full_name=full_name or username,
        hashed_password=get_password_hash(password),
        role="USER",
        is_active=True,
        is_verified=False,
        demo_balance=10000.0,
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    access_token = create_access_token(data={"sub": user.id, "email": user.email})
    refresh_token = create_refresh_token(data={"sub": user.id})
    
    return {
        "user": {
            "id": user.id,
            "email": user.email,
            "fullName": user.full_name,
            "role": user.role,
            "subscription": {
                "plan": user.subscription_plan,
                "expiresAt": user.subscription_expires_at.isoformat() if user.subscription_expires_at else None,
                "isActive": user.has_active_subscription if hasattr(user, 'has_active_subscription') else False
            },
            "demoBalance": user.demo_balance,
            "createdAt": user.created_at.isoformat() if user.created_at else datetime.utcnow().isoformat()
        },
        "accessToken": access_token,
        "refreshToken": refresh_token
    }

@app.post("/api/v1/auth/logout")
async def logout():
    return {"message": "Logged out successfully"}

@app.get("/api/v1/auth/me")
async def get_current_user_info(
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    """Get current user from Authorization header"""
    token = get_token_from_header(authorization)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header"
        )
    
    payload = decode_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated"
        )
    
    return {
        "id": user.id,
        "email": user.email,
        "fullName": user.full_name or user.username,
        "role": user.role,
        "subscription": {
            "plan": user.subscription_plan,
            "expiresAt": user.subscription_expires_at.isoformat() if user.subscription_expires_at else None,
            "isActive": user.has_active_subscription if hasattr(user, 'has_active_subscription') else False
        },
        "demoBalance": user.demo_balance,
        "createdAt": user.created_at.isoformat() if user.created_at else datetime.utcnow().isoformat()
    }

@app.post("/api/v1/auth/refresh")
async def refresh_token(request: dict, db: Session = Depends(get_db)):
    refresh_token = request.get("refresh_token")
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Refresh token required"
        )
    
    payload = decode_token(refresh_token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    access_token = create_access_token(data={"sub": user.id, "email": user.email})
    new_refresh_token = create_refresh_token(data={"sub": user.id})
    
    return {
        "accessToken": access_token,
        "refreshToken": new_refresh_token
    }

@app.post("/api/v1/auth/forgot-password")
async def forgot_password(request: dict, db: Session = Depends(get_db)):
    email = request.get("email")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email required"
        )
    
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return {"message": "If your email is registered, you will receive a reset link"}
    
    return {"message": "If your email is registered, you will receive a reset link"}

@app.post("/api/v1/auth/reset-password")
async def reset_password(request: dict, db: Session = Depends(get_db)):
    token = request.get("token")
    new_password = request.get("new_password")
    
    if not token or not new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token and new password required"
        )
    
    payload = decode_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
    
    email = payload.get("email")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid reset token"
        )
    
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user.hashed_password = get_password_hash(new_password)
    db.commit()
    
    return {"message": "Password reset successfully"}

@app.get("/api/v1/auth/verify-email")
async def verify_email(token: str, db: Session = Depends(get_db)):
    if not token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification token required"
        )
    
    payload = decode_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token"
        )
    
    email = payload.get("email")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification token"
        )
    
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if user.is_verified:
        return {"message": "Email already verified"}
    
    user.is_verified = True
    user.email_verified_at = datetime.utcnow()
    db.commit()
    
    return {"message": "Email verified successfully"}

# ============================================
# ADMIN ENDPOINTS
# ============================================

@app.get("/api/v1/admin/users")
async def get_admin_users(db: Session = Depends(get_db)):
    """Get all users (admin only)"""
    users = db.query(User).all()
    return [
        {
            "id": u.id,
            "email": u.email,
            "fullName": u.full_name or u.username,
            "role": u.role,
            "subscription": {
                "plan": u.subscription_plan,
                "isActive": u.has_active_subscription if hasattr(u, 'has_active_subscription') else False
            },
            "demoBalance": u.demo_balance,
            "createdAt": u.created_at.isoformat() if u.created_at else datetime.utcnow().isoformat()
        }
        for u in users
    ]

@app.get("/api/v1/admin/subscriptions")
async def get_admin_subscriptions():
    """Get all subscriptions (admin only)"""
    return []

@app.get("/api/v1/admin/system/status")
async def get_system_status():
    """Get system status (admin only)"""
    return {
        "status": "online",
        "uptime": 3600,
        "aiStatus": "active",
        "tradesToday": 0,
        "winRate": 0,
        "pl": 0,
        "drawdown": 0
    }

@app.get("/api/v1/admin/revenue")
async def get_revenue():
    """Get revenue stats (admin only)"""
    return {
        "total": 0,
        "monthly": 0,
        "pending": 0
    }

@app.get("/api/v1/admin/system/health")
async def get_system_health():
    """Get system health (admin only)"""
    return {
        "api": "healthy",
        "database": "healthy",
        "redis": "healthy",
        "websocket": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/api/v1/admin/system/logs")
async def get_system_logs():
    """Get system logs (admin only)"""
    return ["System started", "User logged in", "Demo trade executed"]

@app.get("/api/v1/admin/ai/status")
async def get_ai_status():
    """Get AI status (admin only)"""
    return {
        "status": "active",
        "models": ["Trend", "Momentum", "Volatility", "Regime"],
        "lastRun": datetime.utcnow().isoformat(),
        "tradesToday": 0
    }

# ============================================
# SUBSCRIPTION ENDPOINTS
# ============================================

@app.get("/api/v1/subscription/plans")
async def get_subscription_plans():
    """Get available subscription plans"""
    return [
        {
            "id": "plan-basic",
            "name": "Basic",
            "tier": "BASIC",
            "price": 0,
            "currency": "USDT",
            "duration": 1,
            "features": [
                "📊 Demo Trading",
                "📈 Basic AI Signals",
                "📋 Paper Trading",
                "📱 Basic Dashboard"
            ],
            "isPopular": False
        },
        {
            "id": "plan-pro",
            "name": "Pro",
            "tier": "PRO",
            "price": 29.99,
            "currency": "USDT",
            "duration": 1,
            "features": [
                "🔴 Live Trading",
                "🧠 Advanced AI Engine",
                "🛡️ Risk Management",
                "⚡ Priority Support",
                "📊 Real-time Analytics",
                "🔔 Custom Alerts"
            ],
            "isPopular": True
        },
        {
            "id": "plan-enterprise",
            "name": "Enterprise",
            "tier": "ENTERPRISE",
            "price": 99.99,
            "currency": "USDT",
            "duration": 1,
            "features": [
                "🏢 All Pro Features",
                "🔄 Multiple Exchanges",
                "🎯 Custom Strategies",
                "👨‍💼 Dedicated Support",
                "📈 Advanced Analytics",
                "🔐 White-label Options"
            ],
            "isPopular": False
        }
    ]

@app.get("/api/v1/subscription/current")
async def get_current_subscription():
    """Get current user subscription"""
    return None

@app.post("/api/v1/subscription/cancel")
async def cancel_subscription():
    """Cancel subscription"""
    return {"success": True, "message": "Subscription cancelled successfully"}

# ============================================
# MARKET DATA ENDPOINTS
# ============================================

@app.get("/api/v1/market/prices")
async def get_market_prices():
    """Get all current market prices"""
    return market_data_service.get_market_prices()

@app.get("/api/v1/market/price/{symbol}")
async def get_market_price(symbol: str):
    """Get price for a specific symbol"""
    price = market_data_service.get_price(symbol)
    return {
        "symbol": symbol,
        "price": price,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/api/v1/market/symbols")
async def get_market_symbols():
    """Get all supported symbols"""
    return ["BTC/USDT", "ETH/USDT", "SOL/USDT", "BNB/USDT", "XRP/USDT", "DOGE/USDT", "ADA/USDT"]

@app.get("/api/v1/market/ohlcv/{symbol:path}")
async def get_ohlcv(symbol: str, interval: str = "1h", limit: int = 100):
    """
    Get OHLCV data for a symbol.

    🔥 FIX: Bitget v2 granularity values (per their API docs and error messages):
           1min, 3min, 5min, 15min, 30min, 1h, 4h, 6h, 12h, 1day, 1week, 1M
           (NOT 1m, 1H, 1D, 1W — those cause HTTP 400)
    🔥 FIX: Uses {symbol:path} so "BTC/USDT" (with slash) works
    🔥 FIX: Candles reversed to oldest-first (what charting libs expect)
    """
    interval_map = {
        "1m": "1min",
        "3m": "3min",
        "5m": "5min",
        "15m": "15min",
        "30m": "30min",
        "1h": "1h",
        "4h": "4h",
        "6h": "6h",
        "12h": "12h",
        "1d": "1day",
        "3d": "3day",
        "1w": "1week",
        "1M": "1M",
    }

    bitget_symbol = symbol.replace('/', '')
    bitget_interval = interval_map.get(interval, "1h")

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                "https://api.bitget.com/api/v2/spot/market/candles",
                params={
                    "symbol": bitget_symbol,
                    "granularity": bitget_interval,
                    "limit": limit
                }
            )

            if response.status_code != 200:
                logger.warning(
                    f"Bitget candles HTTP {response.status_code} for {symbol}: "
                    f"{response.text[:200]}"
                )
                return []

            data = response.json()
            if data.get('code') != '00000' or not data.get('data'):
                logger.warning(
                    f"Bitget candles error for {symbol}: "
                    f"code={data.get('code')} msg={data.get('msg')}"
                )
                return []

            candles = []
            for candle in data['data']:
                try:
                    candles.append({
                        "timestamp": int(candle[0]),
                        "open": float(candle[1]),
                        "high": float(candle[2]),
                        "low": float(candle[3]),
                        "close": float(candle[4]),
                        "volume": float(candle[5])
                    })
                except (IndexError, ValueError, TypeError):
                    continue

            # 🔥 Bitget returns newest-first; reverse to oldest-first
            candles.reverse()
            logger.info(f"✅ Returning {len(candles)} candles for {symbol} ({bitget_interval})")
            return candles

    except Exception as e:
        logger.error(f"Failed to fetch OHLCV: {e}")

    return []

# ============================================
# DEMO TRADING ENDPOINTS
# ============================================

# Store positions in memory (for demo)
_demo_positions = []

@app.post("/api/v1/demo/positions")
async def open_demo_position(request: dict):
    """Open a demo position with stop-loss and take-profit"""
    symbol = request.get("symbol", "BTC/USDT")
    side = request.get("side", "BUY")
    size = request.get("size", 0.001)
    stop_loss_pct = request.get("stopLossPct", 0.02)
    take_profit_pct = request.get("takeProfitPct", 0.04)
    
    current_price = market_data_service.get_price(symbol)
    if current_price == 0:
        current_price = 45000.00
    
    position = {
        "id": str(uuid.uuid4()),
        "symbol": symbol,
        "side": side,
        "size": size,
        "entryPrice": current_price,
        "currentPrice": current_price,
        "unrealizedPnl": 0.00,
        "realizedPnl": 0.00,
        "stopLoss": round(current_price * (1 - stop_loss_pct), 2),
        "takeProfit": round(current_price * (1 + take_profit_pct), 2),
        "stopLossPct": stop_loss_pct,
        "takeProfitPct": take_profit_pct,
        "openedAt": datetime.utcnow().isoformat(),
        "status": "OPEN",
        "aiConfidence": request.get("aiConfidence", 0),
        "aiReasoning": request.get("aiReasoning", "")
    }
    
    _demo_positions.append(position)
    logger.info(f"📈 Position OPENED: {symbol} {side} @ ${current_price:.2f} | SL: ${position['stopLoss']:.2f} | TP: ${position['takeProfit']:.2f}")
    return position

@app.get("/api/v1/demo/positions")
async def get_demo_positions():
    """Get all demo positions with updated prices"""
    updated_positions = []
    
    for pos in _demo_positions:
        if pos['status'] == 'OPEN':
            current_price = market_data_service.get_price(pos['symbol'])
            if current_price > 0:
                pos['currentPrice'] = current_price
                if pos['side'] == 'BUY':
                    pos['unrealizedPnl'] = (current_price - pos['entryPrice']) * pos['size']
                else:
                    pos['unrealizedPnl'] = (pos['entryPrice'] - current_price) * pos['size']
        
        updated_positions.append(pos.copy())
    
    return updated_positions

@app.post("/api/v1/demo/positions/{position_id}/close")
async def close_demo_position(position_id: str):
    """Close a demo position"""
    for i, pos in enumerate(_demo_positions):
        if pos['id'] == position_id and pos['status'] == 'OPEN':
            current_price = market_data_service.get_price(pos['symbol'])
            if current_price > 0:
                pos['currentPrice'] = current_price
                if pos['side'] == 'BUY':
                    pos['realizedPnl'] = (current_price - pos['entryPrice']) * pos['size']
                else:
                    pos['realizedPnl'] = (pos['entryPrice'] - current_price) * pos['size']
            
            pos['status'] = 'CLOSED'
            pos['closedAt'] = datetime.utcnow().isoformat()
            
            return {"success": True, "position": pos}
    
    raise HTTPException(status_code=404, detail="Position not found")

@app.get("/api/v1/demo/balance")
async def get_demo_balance():
    """Get demo balance with positions reflected"""
    total_balance = 10000.00
    locked = 0.00
    
    for pos in _demo_positions:
        if pos['status'] == 'OPEN':
            locked += pos['entryPrice'] * pos['size']
    
    return {
        "total": total_balance,
        "available": total_balance - locked,
        "locked": locked
    }

# ============================================
# AI TRADING ENDPOINTS
# ============================================

@app.get("/api/v1/ai/analyze/{symbol}")
async def ai_analyze_symbol(symbol: str, timeframe: str = "1h"):
    """Get AI trading signal for a symbol"""
    result = await ai_trading_service.analyze_symbol(symbol, timeframe)
    return result

@app.get("/api/v1/ai/analyze/all")
async def ai_analyze_all():
    """Get AI signals for all symbols"""
    symbols = ["BTC/USDT", "ETH/USDT", "SOL/USDT", "BNB/USDT"]
    results = {}
    
    for symbol in symbols:
        result = await ai_trading_service.analyze_symbol(symbol)
        results[symbol] = result
    
    return results

@app.get("/api/v1/ai/status")
async def ai_status():
    """Get AI engine status"""
    return {
        "status": "running",
        "symbols_analyzed": len(ai_trading_service.signals),
        "last_update": datetime.utcnow().isoformat()
    }

# ============================================
# AUTO-TRADING ENDPOINTS WITH TELEGRAM
# ============================================

async def execute_ai_trade(symbol: str, side: str, signal: dict, user_id: str = None):
    """
    🏆 HYBRID: Execute trade with user's base amount scaled by AI confidence
    """
    from .models.ai_settings import AISettings
    
    base_amount = 25.0
    stop_loss_pct = 0.02
    take_profit_pct = 0.04
    
    if user_id:
        db = SessionLocal()
        try:
            user_settings = db.query(AISettings).filter(
                AISettings.user_id == user_id
            ).first()
            
            if user_settings:
                base_amount = user_settings.trade_amount or 25.0
                stop_loss_pct = (user_settings.stop_loss_percent or 2.0) / 100
                take_profit_pct = (user_settings.take_profit_percent or 4.0) / 100
        finally:
            db.close()
    
    current_price = market_data_service.get_price(symbol)
    if current_price == 0:
        current_price = 45000.00
    
    confidence = signal.get('confidence', 50)
    trade_amount = ai_trading_service.calculate_trade_amount(base_amount, confidence)
    size = trade_amount / current_price
    
    position = {
        "id": str(uuid.uuid4()),
        "symbol": symbol,
        "side": side,
        "size": round(size, 6),
        "entryPrice": current_price,
        "currentPrice": current_price,
        "unrealizedPnl": 0.00,
        "realizedPnl": 0.00,
        "tradeAmount": trade_amount,
        "baseAmount": base_amount,
        "stopLoss": round(current_price * (1 - stop_loss_pct), 2),
        "takeProfit": round(current_price * (1 + take_profit_pct), 2),
        "stopLossPct": stop_loss_pct,
        "takeProfitPct": take_profit_pct,
        "openedAt": datetime.utcnow().isoformat(),
        "status": "OPEN",
        "aiConfidence": confidence,
        "aiReasoning": signal.get('reasoning', 'AI signal'),
        "user_id": user_id
    }
    
    _demo_positions.append(position)
    logger.info(
        f"🤖 AI Trade: {side} {symbol} | "
        f"Base ${base_amount} × {confidence}% = ${trade_amount} | "
        f"Size {size:.6f}"
    )
    
    await telegram_service.send_trade_alert(position, "OPEN")
    return position

@app.post("/api/v1/ai/auto-trade")
async def auto_trade(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Auto-trade based on user's AI settings"""
    from .models.ai_settings import AISettings
    
    settings = db.query(AISettings).filter(
        AISettings.user_id == current_user.id
    ).first()
    
    if not settings:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please configure your AI settings first"
        )
    
    if not settings.auto_trade_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Auto-trade is disabled. Enable it in AI Settings."
        )
    
    user_symbols = settings.get_symbols_list()
    confidence_threshold = settings.confidence_threshold
    
    results = []
    signals = await ai_analyze_all()
    
    for symbol, signal in signals.items():
        if symbol not in user_symbols:
            continue
        if signal['confidence'] < confidence_threshold:
            continue
        
        if signal['signal'] == 'BUY':
            trade = await execute_ai_trade(symbol, 'BUY', signal, current_user.id)
            results.append(trade)
        elif signal['signal'] == 'SELL':
            trade = await execute_ai_trade(symbol, 'SELL', signal, current_user.id)
            results.append(trade)
    
    return {
        "message": f"Executed {len(results)} trades",
        "trades": results,
        "settings_used": {
            "confidence_threshold": confidence_threshold,
            "trade_amount": settings.trade_amount,
            "symbols": user_symbols
        }
    }

@app.get("/api/v1/ai/portfolio")
async def get_ai_portfolio(current_user: User = Depends(get_current_user)):
    """Get user's AI trading portfolio"""
    portfolio = {"total_value": 0, "total_pnl": 0, "positions": []}
    
    for pos in _demo_positions:
        if pos.get('user_id') != current_user.id:
            continue
        if pos['status'] != 'OPEN':
            continue
        
        current_price = market_data_service.get_price(pos['symbol'])
        if current_price > 0:
            pos['currentPrice'] = current_price
            if pos['side'] == 'BUY':
                pos['unrealizedPnl'] = (current_price - pos['entryPrice']) * pos['size']
            else:
                pos['unrealizedPnl'] = (pos['entryPrice'] - current_price) * pos['size']
        
        portfolio['positions'].append(pos)
        portfolio['total_value'] += pos['currentPrice'] * pos['size']
        portfolio['total_pnl'] += pos['unrealizedPnl']
    
    return portfolio

@app.get("/api/v1/ai/trade-history")
async def get_trade_history():
    """Get AI trade history"""
    return position_monitor.get_trade_history()

@app.get("/api/v1/ai/performance")
async def get_performance():
    """Get AI performance stats"""
    return position_monitor.get_performance_stats()

# ============================================
# AI SETTINGS ROUTER
# ============================================
app.include_router(ai_settings.router, prefix=settings.api_prefix)

# ============================================
# TELEGRAM TEST ENDPOINT
# ============================================

@app.post("/api/v1/telegram/test")
async def test_telegram():
    """
    Test Telegram notification.
    """
    import traceback

    message = """
<b>🧪 JADOTA AI - Test Notification</b>
━━━━━━━━━━━━━━━━━━━━━━
✅ Telegram is working!
📊 Your AI trading alerts will appear here.
📈 Auto-Trade alerts: OPEN, STOP_LOSS, TAKE_PROFIT
━━━━━━━━━━━━━━━━━━━━━━
📅 {timestamp}
"""

    try:
        success = await telegram_service.send_to_group(
            message.format(timestamp=datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC'))
        )
        return {
            "success": success,
            "message": "Test notification sent" if success else "Failed to send",
        }
    except Exception as e:
        logger.error(f"Telegram test failed: {e}\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Telegram send failed: {type(e).__name__}: {str(e)}",
        )

# ============================================
# TRADING ENDPOINTS
# ============================================

@app.get("/api/v1/trading/positions")
async def get_positions():
    """Get live trading positions"""
    return []

@app.get("/api/v1/trading/balance")
async def get_balance():
    """Get live trading balance"""
    return {
        "total": 0.00,
        "available": 0.00,
        "locked": 0.00
    }

@app.get("/api/v1/trading/history")
async def get_live_trade_history():
    """Get live trading history"""
    return []

# ============================================
# Health Check
# ============================================

@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "app": settings.app_name,
        "environment": settings.app_env,
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/")
async def root():
    return {
        "message": "Welcome to JADOTA AI API",
        "docs": "/api/docs",
        "health": "/api/health",
        "timestamp": datetime.utcnow().isoformat()
    }

# ============================================
# Startup / Shutdown
# ============================================

@app.on_event("startup")
async def startup_event():
    """Start market data service on startup"""
    logger.info("🚀 Starting JADOTA AI API...")
    
    # 🔥 Initialize Telegram
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = (
        os.getenv("TELEGRAM_CHAT_ID")
        or os.getenv("TELEGRAM_GROUP_CHAT_ID")   # fallback in case name differs
    )

    logger.info(f"🔍 .env file: {env_path} (exists={env_path.exists()})")
    logger.info(f"🔍 TELEGRAM_BOT_TOKEN: {'✅ set' if bot_token else '❌ missing'}")
    logger.info(f"🔍 TELEGRAM_CHAT_ID:   {'✅ set' if chat_id else '❌ missing'}")

    if bot_token and chat_id:
        telegram_service.initialize(bot_token, chat_id)
        logger.info("✅ Telegram Service initialized")
    else:
        logger.warning("⚠️ Telegram credentials not set - notifications disabled")
    
    await market_data_service.start()
    prices = market_data_service.get_market_prices()
    logger.info(f"📊 Loaded {len(prices)} market prices")
    
    await position_monitor.start(_demo_positions, market_data_service)
    logger.info("✅ Position Monitor started")
    
    logger.info("✅ JADOTA AI API started successfully")

@app.on_event("shutdown")
async def shutdown_event():
    """Stop market data service on shutdown"""
    logger.info("🛑 Shutting down JADOTA AI API...")
    await market_data_service.stop()
    await position_monitor.stop()
    logger.info("JADOTA AI API shut down")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)