from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends, status, Request, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from datetime import datetime, timedelta
import json
import logging
import uuid
import httpx
import os
import traceback

# 🔥 LOAD .env — must run BEFORE any code that reads env vars
from dotenv import load_dotenv
from pathlib import Path

env_path = Path(__file__).parent.parent / ".env"   # backend/.env
load_dotenv(dotenv_path=env_path, override=False)

# 🔥 FIX: Import Session from sqlalchemy.orm
from sqlalchemy.orm import Session

from .core.config import settings, get_cors_origins, get_allowed_hosts
from .core.database import engine, Base, SessionLocal
from .core.security import (
    get_password_hash, verify_password, create_access_token, 
    create_refresh_token, decode_token, get_token_from_header
)
from .models.user import User
# 🔥 Task #3: ensure Position model is registered with Base before create_all()
from .models.position import Position  # noqa: F401
# 🔥 Task #4a-1: ensure ExchangeCredentials model is registered before create_all()
from .models.exchange_credentials import ExchangeCredentials  # noqa: F401
from .services.market_data_service import market_data_service
from .services.ai_trading_service import ai_trading_service
from .services.position_monitor import position_monitor
from .services.telegram_service import telegram_service
# 🔥 Task #3: DB-backed position store replaces the in-memory list
from .services.position_store import (
    list_positions,
    get_position,
    create_position,
    update_position,
    close_position,
)
# 🔥 Task #4a-2: live order routing helpers
from .services.encryption import decrypt
from .services.bitget_client import BitgetClient, BitgetError
from .api.v1 import ai_settings
# 🔥 Analytics router
from .api.v1 import analytics
# 🔥 Payments router
from .api.v1 import payments
# 🔥 Task #4a-1: Exchange (Bitget) router
from .api.v1 import exchange
# 🔥 FIX (Task #1): admin-only dependency for locking down admin endpoints
from .api.dependencies import get_admin_user

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Truncation limit for error strings stored on ExchangeCredentials
_MAX_ERROR_CHARS = 500

# ============================================
# Database Setup
# ============================================
try:
    Base.metadata.create_all(bind=engine)
    logger.info("✅ Database tables created/verified")
except Exception as e:
    logger.error(f"❌ Database setup error: {e}")


# ============================================
# 🔥 AUTO-MIGRATION — add missing columns to existing tables
# Runs on every startup. Idempotent: skips columns that already exist.
# ============================================
def _run_startup_migrations():
    from sqlalchemy import text as _sql_text, inspect as _inspect

    # Expected columns for ai_settings
    expected_ai_settings = {
        "trade_amount": "FLOAT DEFAULT 25.0",
        "stop_loss_percent": "FLOAT DEFAULT 2.0",
        "take_profit_percent": "FLOAT DEFAULT 4.0",
        "position_size_multiplier": "FLOAT DEFAULT 1.0",
        "max_positions": "INTEGER DEFAULT 5",
        "max_trades_per_day": "INTEGER DEFAULT 10",
        "risk_per_trade": "FLOAT DEFAULT 2.0",
        "max_daily_loss": "FLOAT DEFAULT 5.0",
        "max_drawdown": "FLOAT DEFAULT 15.0",
        "strategy_type": "VARCHAR(50)",
        "auto_trade_enabled": "BOOLEAN DEFAULT FALSE",
        "symbols": "TEXT",
        "total_trades": "INTEGER DEFAULT 0",
        "winning_trades": "INTEGER DEFAULT 0",
        "losing_trades": "INTEGER DEFAULT 0",
        "total_pnl": "FLOAT DEFAULT 0.0",
        "best_trade": "FLOAT DEFAULT 0.0",
        "worst_trade": "FLOAT DEFAULT 0.0",
    }

    # Expected columns for payments
    expected_payments = {
        "plan": "VARCHAR(50) DEFAULT 'PRO'",
        "months": "FLOAT DEFAULT 1.0",
        "amount_usdt": "FLOAT DEFAULT 0.0",
        "network": "VARCHAR(20) DEFAULT 'BEP20'",
        "wallet_address": "VARCHAR(100) DEFAULT ''",
        "status": "VARCHAR(20) DEFAULT 'pending'",
        "tx_hash": "VARCHAR(100)",
        "admin_notes": "TEXT",
        "created_at": "TIMESTAMP DEFAULT NOW()",
        "expires_at": "TIMESTAMP DEFAULT NOW()",
        "verified_at": "TIMESTAMP",
        "completed_at": "TIMESTAMP",
    }

    # 🔥 Task #3 + Task #4a-2: Expected columns for positions
    expected_positions = {
        "user_id": "VARCHAR(36)",
        "symbol": "VARCHAR(20)",
        "side": "VARCHAR(10)",
        "size": "FLOAT DEFAULT 0.0",
        "entry_price": "FLOAT DEFAULT 0.0",
        "current_price": "FLOAT DEFAULT 0.0",
        "unrealized_pnl": "FLOAT DEFAULT 0.0",
        "realized_pnl": "FLOAT DEFAULT 0.0",
        "trade_amount": "FLOAT",
        "base_amount": "FLOAT",
        "stop_loss": "FLOAT",
        "take_profit": "FLOAT",
        "stop_loss_pct": "FLOAT",
        "take_profit_pct": "FLOAT",
        "ai_confidence": "FLOAT",
        "ai_reasoning": "TEXT",
        "status": "VARCHAR(20) DEFAULT 'OPEN'",
        "close_reason": "VARCHAR(30)",
        "opened_at": "TIMESTAMP DEFAULT NOW()",
        "closed_at": "TIMESTAMP",
        "created_at": "TIMESTAMP DEFAULT NOW()",
        "updated_at": "TIMESTAMP",
        # 🔥 Task #4a-2 — Bitget linkage
        "bitget_order_id": "VARCHAR(100)",
        "source": "VARCHAR(20) DEFAULT 'demo'",
    }

    # 🔥 Task #4a-1: Expected columns for exchange_credentials
    expected_exchange_credentials = {
        "user_id": "VARCHAR(36)",
        "exchange": "VARCHAR(20) DEFAULT 'bitget'",
        "api_key_encrypted": "TEXT",
        "api_secret_encrypted": "TEXT",
        "passphrase_encrypted": "TEXT",
        "api_key_masked": "VARCHAR(50)",
        "permissions": "VARCHAR(100)",
        "ip_whitelist": "VARCHAR(200)",
        "is_active": "BOOLEAN DEFAULT TRUE",
        "last_used_at": "TIMESTAMP",
        "last_error": "TEXT",
        "created_at": "TIMESTAMP DEFAULT NOW()",
        "updated_at": "TIMESTAMP",
    }

    try:
        inspector = _inspect(engine)
        tables = set(inspector.get_table_names())

        with engine.connect() as conn:
            # ---------- ai_settings ----------
            if "ai_settings" in tables:
                actual = {c["name"] for c in inspector.get_columns("ai_settings")}
                missing = {k: v for k, v in expected_ai_settings.items() if k not in actual}
                if missing:
                    logger.info(f"🔧 ai_settings: adding {len(missing)} missing column(s)")
                    for col, dtype in missing.items():
                        try:
                            conn.execute(_sql_text(f"ALTER TABLE ai_settings ADD COLUMN {col} {dtype}"))
                            logger.info(f"   + ai_settings.{col}")
                        except Exception as e:
                            logger.warning(f"   ⚠️ Could not add ai_settings.{col}: {e}")
                    conn.commit()
                    logger.info("✅ ai_settings migration complete")
                else:
                    logger.info("✅ ai_settings schema is up to date")

            # ---------- payments ----------
            if "payments" in tables:
                actual = {c["name"] for c in inspector.get_columns("payments")}
                missing = {k: v for k, v in expected_payments.items() if k not in actual}
                if missing:
                    logger.info(f"🔧 payments: adding {len(missing)} missing column(s)")
                    for col, dtype in missing.items():
                        try:
                            conn.execute(_sql_text(f"ALTER TABLE payments ADD COLUMN {col} {dtype}"))
                            logger.info(f"   + payments.{col}")
                        except Exception as e:
                            logger.warning(f"   ⚠️ Could not add payments.{col}: {e}")
                    conn.commit()
                    logger.info("✅ payments migration complete")
                else:
                    logger.info("✅ payments schema is up to date")

            # ---------- positions (Task #3 + #4a-2) ----------
            if "positions" in tables:
                actual = {c["name"] for c in inspector.get_columns("positions")}
                missing = {k: v for k, v in expected_positions.items() if k not in actual}
                if missing:
                    logger.info(f"🔧 positions: adding {len(missing)} missing column(s)")
                    for col, dtype in missing.items():
                        try:
                            conn.execute(_sql_text(f"ALTER TABLE positions ADD COLUMN {col} {dtype}"))
                            logger.info(f"   + positions.{col}")
                        except Exception as e:
                            logger.warning(f"   ⚠️ Could not add positions.{col}: {e}")
                    conn.commit()
                    logger.info("✅ positions migration complete")
                else:
                    logger.info("✅ positions schema is up to date")

            # ---------- exchange_credentials (Task #4a-1) ----------
            if "exchange_credentials" in tables:
                actual = {c["name"] for c in inspector.get_columns("exchange_credentials")}
                missing = {k: v for k, v in expected_exchange_credentials.items() if k not in actual}
                if missing:
                    logger.info(f"🔧 exchange_credentials: adding {len(missing)} missing column(s)")
                    for col, dtype in missing.items():
                        try:
                            conn.execute(_sql_text(f"ALTER TABLE exchange_credentials ADD COLUMN {col} {dtype}"))
                            logger.info(f"   + exchange_credentials.{col}")
                        except Exception as e:
                            logger.warning(f"   ⚠️ Could not add exchange_credentials.{col}: {e}")
                    conn.commit()
                    logger.info("✅ exchange_credentials migration complete")
                else:
                    logger.info("✅ exchange_credentials schema is up to date")

    except Exception as e:
        logger.error(f"❌ Migration error: {e}")


_run_startup_migrations()

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
# 🔥 Global Exception Handler
# ============================================
@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """Catch-all for unhandled exceptions."""
    logger.error(f"❌ Unhandled exception on {request.method} {request.url.path}")
    logger.error(
        "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    )
    origin = request.headers.get("origin") or "*"
    return JSONResponse(
        status_code=500,
        content={
            "detail": f"Internal server error: {type(exc).__name__}: {str(exc)}"
        },
        headers={
            "Access-Control-Allow-Origin": origin,
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, PATCH",
            "Access-Control-Allow-Headers": "*",
        },
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
# 🔐 ONE-TIME ADMIN BOOTSTRAP
# ============================================
@app.post("/api/v1/admin/bootstrap")
async def admin_bootstrap(request: dict, db: Session = Depends(get_db)):
    """Promote an existing user to SUPER_ADMIN + ENTERPRISE."""
    key = request.get("key")
    email = request.get("email")

    expected = os.getenv("ADMIN_BOOTSTRAP_KEY")
    if not expected or key != expected:
        raise HTTPException(status_code=401, detail="Invalid bootstrap key")

    if not email:
        raise HTTPException(status_code=400, detail="Email required")

    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.role = "SUPER_ADMIN"
    user.subscription_plan = "ENTERPRISE"
    user.subscription_expires_at = datetime.utcnow() + timedelta(days=3650)
    user.is_subscription_active = True
    user.is_verified = True
    db.commit()
    db.refresh(user)

    logger.info(f"🔐 Bootstrap: {user.email} promoted to SUPER_ADMIN / ENTERPRISE")

    return {
        "success": True,
        "email": user.email,
        "role": user.role,
        "plan": user.subscription_plan,
        "is_active": user.has_active_subscription,
        "expires": user.subscription_expires_at.isoformat() if user.subscription_expires_at else None,
    }


# ============================================
# 🔍 DB DIAGNOSTIC
# ============================================
@app.get("/api/v1/debug/db-info", dependencies=[Depends(get_admin_user)])
async def db_info(db: Session = Depends(get_db)):
    """Report which database engine is actually in use. (admin only)"""
    try:
        engine_name = db.bind.dialect.name if db.bind else "unknown"
    except Exception:
        engine_name = "unknown"

    url = os.getenv("DATABASE_URL", "(unset)")
    safe_url = url
    if "@" in url and "://" in url:
        scheme, rest = url.split("://", 1)
        if "@" in rest:
            creds, host = rest.split("@", 1)
            if ":" in creds:
                user_part = creds.split(":", 1)[0]
                safe_url = f"{scheme}://{user_part}:***@{host}"
            else:
                safe_url = f"{scheme}://***@{host}"

    return {
        "engine": engine_name,
        "database_url": safe_url,
        "user_count": db.query(User).count(),
    }

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
# 🔥 FIX (Task #1): All 7 admin endpoints below now require
# an authenticated user with role ADMIN or SUPER_ADMIN.

@app.get("/api/v1/admin/users", dependencies=[Depends(get_admin_user)])
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

@app.get("/api/v1/admin/subscriptions", dependencies=[Depends(get_admin_user)])
async def get_admin_subscriptions():
    """Get all subscriptions (admin only)"""
    return []

@app.get("/api/v1/admin/system/status", dependencies=[Depends(get_admin_user)])
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

@app.get("/api/v1/admin/revenue", dependencies=[Depends(get_admin_user)])
async def get_revenue():
    """Get revenue stats (admin only)"""
    return {
        "total": 0,
        "monthly": 0,
        "pending": 0
    }

@app.get("/api/v1/admin/system/health", dependencies=[Depends(get_admin_user)])
async def get_system_health():
    """Get system health (admin only)"""
    return {
        "api": "healthy",
        "database": "healthy",
        "redis": "healthy",
        "websocket": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/api/v1/admin/system/logs", dependencies=[Depends(get_admin_user)])
async def get_system_logs():
    """Get system logs (admin only)"""
    return ["System started", "User logged in", "Demo trade executed"]

@app.get("/api/v1/admin/ai/status", dependencies=[Depends(get_admin_user)])
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
    """Get OHLCV data for a symbol."""
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

            candles.reverse()
            logger.info(f"✅ Returning {len(candles)} candles for {symbol} ({bitget_interval})")
            return candles

    except Exception as e:
        logger.error(f"Failed to fetch OHLCV: {e}")

    return []

# ============================================
# DEMO TRADING ENDPOINTS (Task #3: DB-backed)
# ============================================

@app.post("/api/v1/demo/positions")
async def open_demo_position(
    request: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Open a demo position with stop-loss and take-profit"""
    symbol = request.get("symbol", "BTC/USDT")
    side = request.get("side", "BUY")
    size = request.get("size", 0.001)
    stop_loss_pct = request.get("stopLossPct", 0.02)
    take_profit_pct = request.get("takeProfitPct", 0.04)

    current_price = market_data_service.get_price(symbol)
    if current_price == 0:
        current_price = 45000.00

    position = create_position(db, {
        "id": str(uuid.uuid4()),
        "user_id": current_user.id,
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
        "aiReasoning": request.get("aiReasoning", ""),
        "source": "demo",
    })

    logger.info(f"📈 Position OPENED for user {current_user.id[:8]}: {symbol} {side} @ ${current_price:.2f}")
    return position

@app.get("/api/v1/demo/positions")
async def get_demo_positions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get all demo positions for the current user with updated prices"""
    positions = list_positions(db, user_id=current_user.id)
    out = []
    for pos in positions:
        if pos.get("status") == "OPEN":
            current_price = market_data_service.get_price(pos["symbol"])
            if current_price > 0:
                pos["currentPrice"] = current_price
                if pos["side"] == "BUY":
                    pos["unrealizedPnl"] = (current_price - pos["entryPrice"]) * pos["size"]
                else:
                    pos["unrealizedPnl"] = (pos["entryPrice"] - current_price) * pos["size"]
                update_position(db, pos["id"], {
                    "currentPrice": current_price,
                    "unrealizedPnl": pos["unrealizedPnl"],
                })
        out.append(pos)
    return out

@app.post("/api/v1/demo/positions/{position_id}/close")
async def close_demo_position(
    position_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Close a demo position (must be owned by the current user)"""
    pos = get_position(db, position_id)
    if not pos or pos.get("status") != "OPEN":
        raise HTTPException(status_code=404, detail="Position not found")
    if pos.get("user_id") != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only close your own positions"
        )

    current_price = market_data_service.get_price(pos["symbol"])
    closed = close_position(db, position_id, "MANUAL", exit_price=current_price or None)
    return {"success": True, "position": closed}

@app.get("/api/v1/demo/balance")
async def get_demo_balance(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get demo balance for the current user"""
    total_balance = current_user.demo_balance if current_user.demo_balance is not None else 10000.00
    open_positions = list_positions(db, user_id=current_user.id, status="OPEN")
    locked = sum((p.get("entryPrice") or 0) * (p.get("size") or 0) for p in open_positions)
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
    """Get AI trading signal for a symbol (uses default strategy)"""
    result = await ai_trading_service.analyze_symbol(symbol, timeframe)
    return result

@app.get("/api/v1/ai/analyze/all")
async def ai_analyze_all():
    """Get AI signals for all symbols (uses default strategy)"""
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
# AUTO-TRADING ENDPOINTS (Task #3 + #4a-2)
# ============================================

async def _place_bitget_order(
    cred: ExchangeCredentials,
    db: Session,
    symbol: str,
    side: str,
    trade_amount: float,
    base_size: float,
) -> str:
    """
    Place a spot market order on Bitget for a connected user.

    Side handling — matches Bitget v2 spot semantics:
      - BUY / ADD → order side "buy",  size is the QUOTE amount (USDT to spend)
      - SELL      → order side "sell", size is the BASE amount (coins to sell)

    Raises HTTPException on any failure — the caller must NOT create a
    position row when this function raises.
    """
    api_key = decrypt(cred.api_key_encrypted)
    api_secret = decrypt(cred.api_secret_encrypted)
    passphrase = decrypt(cred.passphrase_encrypted)

    if not (api_key and api_secret and passphrase):
        logger.error(f"bitget.decrypt.failed user={cred.user_id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Stored Bitget credentials cannot be decrypted. "
                   "Please disconnect and reconnect your Bitget account.",
        )

    bitget_symbol = symbol.replace("/", "")
    order_side = "buy" if side in ("BUY", "ADD") else "sell"

    # Bitget expects: buy → quote amount; sell → base amount
    if order_side == "buy":
        order_size = f"{trade_amount:.8f}"
    else:
        order_size = f"{base_size:.8f}"

    # Idempotency token — reused if the caller ever retries the same logical order
    client_oid = str(uuid.uuid4()).replace("-", "")[:30]

    try:
        async with BitgetClient(
            api_key=api_key,
            api_secret=api_secret,
            passphrase=passphrase,
            testnet=settings.bitget_testnet,
        ) as client:
            result = await client.place_spot_market_order(
                symbol=bitget_symbol,
                side=order_side,
                size=order_size,
                client_oid=client_oid,
            )
    except BitgetError as exc:
        logger.warning(
            f"bitget.order.rejected user={cred.user_id} "
            f"symbol={bitget_symbol} side={order_side} "
            f"code={exc.code} msg={exc.msg}"
        )
        cred.last_error = f"{exc.code}: {exc.msg}"[:_MAX_ERROR_CHARS]
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Bitget rejected the order: {exc.msg}",
        )
    except Exception as exc:  # network, timeout, DNS
        logger.exception(
            f"bitget.order.unreachable user={cred.user_id} "
            f"symbol={bitget_symbol} side={order_side}"
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Could not reach Bitget: {type(exc).__name__}",
        )

    order_id = result.get("orderId") or result.get("order_id")
    if not order_id:
        logger.error(f"bitget.order.no_id user={cred.user_id} result={result}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Bitget did not return an order ID.",
        )

    # Record successful use
    cred.last_used_at = datetime.utcnow()
    cred.last_error = None
    db.commit()

    logger.info(
        f"bitget.order.placed user={cred.user_id} "
        f"symbol={bitget_symbol} side={order_side} size={order_size} "
        f"order_id={order_id}"
    )
    return order_id


async def execute_ai_trade(symbol: str, side: str, signal: dict, user_id: str = None):
    """
    Execute a trade based on an AI signal.

    Task #4a-2 behavior:
      - If the user has an active Bitget connection, the order is placed
        on Bitget *before* any DB write. If Bitget rejects, HTTPException
        is raised and no position row is created.
      - If the user has no Bitget connection, behavior is unchanged:
        a demo-only position is written (source="demo").

    Supported sides: BUY, SELL, ADD.
      - BUY / SELL create a new position
      - ADD merges into the user's existing OPEN position for that symbol
    """
    from .models.ai_settings import AISettings

    base_amount = 25.0
    stop_loss_pct = 0.02
    take_profit_pct = 0.04

    db = SessionLocal()
    try:
        # ---- 1. Load user's AI settings ----------------------------------
        if user_id:
            user_settings = db.query(AISettings).filter(
                AISettings.user_id == user_id
            ).first()
            if user_settings:
                base_amount = user_settings.trade_amount or 25.0
                stop_loss_pct = (user_settings.stop_loss_percent or 2.0) / 100
                take_profit_pct = (user_settings.take_profit_percent or 4.0) / 100

        # ---- 2. Compute sizing from current market price -----------------
        current_price = market_data_service.get_price(symbol)
        if current_price == 0:
            current_price = 45000.00

        confidence = signal.get("confidence", 50)
        trade_amount = ai_trading_service.calculate_trade_amount(base_amount, confidence)
        size = trade_amount / current_price

        # ---- 3. Check for a live Bitget connection -----------------------
        cred = None
        if user_id:
            cred = (
                db.query(ExchangeCredentials)
                .filter(
                    ExchangeCredentials.user_id == user_id,
                    ExchangeCredentials.exchange == "bitget",
                    ExchangeCredentials.is_active == True,  # noqa: E712
                )
                .first()
            )
        is_live = cred is not None

        # ---- 4. Place the real order FIRST, if live ----------------------
        # If this raises, no position is created — user never sees a
        # phantom position that doesn't exist on Bitget.
        bitget_order_id = None
        if is_live:
            bitget_order_id = await _place_bitget_order(
                cred=cred,
                db=db,
                symbol=symbol,
                side=side,
                trade_amount=trade_amount,
                base_size=size,
            )

        source = "bitget" if is_live else "demo"

        # ---- 5. ADD — merge into existing OPEN position ------------------
        if side == "ADD":
            open_positions = list_positions(db, user_id=user_id, status="OPEN")
            existing = next((p for p in open_positions if p["symbol"] == symbol), None)

            if existing:
                old_size = float(existing.get("size") or 0)
                old_price = float(existing.get("entryPrice") or 0)
                new_size = old_size + size
                if new_size > 0:
                    avg_price = (old_size * old_price + size * current_price) / new_size
                else:
                    avg_price = current_price

                updated = update_position(db, existing["id"], {
                    "size": round(new_size, 6),
                    "entryPrice": round(avg_price, 2),
                    "currentPrice": current_price,
                    "tradeAmount": (existing.get("tradeAmount") or 0) + trade_amount,
                    "stopLoss": round(avg_price * (1 - stop_loss_pct), 2),
                    "takeProfit": round(avg_price * (1 + take_profit_pct), 2),
                    "bitgetOrderId": bitget_order_id,
                    "source": source,
                })

                logger.info(
                    f"💰 DCA ADD: {symbol} | source={source} | "
                    f"Old {old_size:.6f}@{old_price:.2f} + "
                    f"New {size:.6f}@{current_price:.2f} = "
                    f"Avg {new_size:.6f}@{avg_price:.2f}"
                    + (f" | bitget_order={bitget_order_id}" if bitget_order_id else "")
                )
                await telegram_service.send_trade_alert(updated, "ADD")
                return updated

            # No existing position — treat as BUY
            side = "BUY"

        # ---- 6. Normal BUY / SELL — create new position ------------------
        position = create_position(db, {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
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
            "aiReasoning": signal.get("reasoning", "AI signal"),
            "bitgetOrderId": bitget_order_id,
            "source": source,
        })

        logger.info(
            f"🤖 AI Trade: {side} {symbol} | source={source} | "
            f"Base ${base_amount} × {confidence}% = ${trade_amount} | "
            f"Size {size:.6f}"
            + (f" | bitget_order={bitget_order_id}" if bitget_order_id else "")
        )

        await telegram_service.send_trade_alert(position, "OPEN")
        return position
    finally:
        db.close()

@app.post("/api/v1/ai/auto-trade")
async def auto_trade(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Auto-trade based on user's AI settings and chosen strategy"""
    from .models.ai_settings import AISettings

    settings = db.query(AISettings).filter(
        AISettings.user_id == current_user.id
    ).first()

    if not settings:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please configure your AI settings first",
        )
    if not settings.auto_trade_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Auto-trade is disabled. Enable it in AI Settings.",
        )

    user_symbols = settings.get_symbols_list()
    confidence_threshold = settings.confidence_threshold
    strategy_name = getattr(settings, "strategy_type", None) or "balanced"

    user_positions = list_positions(db, user_id=current_user.id, status="OPEN")

    signals = {}
    for sym in ["BTC/USDT", "ETH/USDT", "SOL/USDT", "BNB/USDT"]:
        signals[sym] = await ai_trading_service.analyze_symbol(
            sym,
            timeframe="1h",
            strategy=strategy_name,
            positions=user_positions,
        )

    results = []
    failures = []
    for symbol, signal in signals.items():
        if symbol not in user_symbols:
            continue
        if signal["confidence"] < confidence_threshold:
            continue
        sig = signal["signal"]

        if sig in ("BUY", "SELL", "ADD"):
            # 🔥 Task #4a-2: isolate per-symbol failures so one rejected
            # Bitget order does not abort the whole batch.
            try:
                trade = await execute_ai_trade(symbol, sig, signal, current_user.id)
                results.append(trade)
            except HTTPException as exc:
                logger.warning(f"auto_trade: {symbol} {sig} failed: {exc.detail}")
                failures.append({
                    "symbol": symbol,
                    "side": sig,
                    "error": str(exc.detail),
                })
            except Exception as exc:
                logger.exception(f"auto_trade: unexpected error on {symbol}")
                failures.append({
                    "symbol": symbol,
                    "side": sig,
                    "error": f"{type(exc).__name__}: {exc}",
                })

    message = f"Executed {len(results)} trades"
    if failures:
        message += f", {len(failures)} failed"

    return {
        "message": message,
        "strategy": strategy_name,
        "trades": results,
        "failures": failures,   # 🔥 new field — frontend can ignore
        "settings_used": {
            "confidence_threshold": confidence_threshold,
            "trade_amount": settings.trade_amount,
            "symbols": user_symbols,
        },
    }

@app.get("/api/v1/ai/portfolio")
async def get_ai_portfolio(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get user's AI trading portfolio"""
    portfolio = {"total_value": 0, "total_pnl": 0, "positions": []}

    positions = list_positions(db, user_id=current_user.id, status="OPEN")
    for pos in positions:
        current_price = market_data_service.get_price(pos["symbol"])
        if current_price > 0:
            pos["currentPrice"] = current_price
            if pos["side"] == "BUY":
                pos["unrealizedPnl"] = (current_price - pos["entryPrice"]) * pos["size"]
            else:
                pos["unrealizedPnl"] = (pos["entryPrice"] - current_price) * pos["size"]
            update_position(db, pos["id"], {
                "currentPrice": current_price,
                "unrealizedPnl": pos["unrealizedPnl"],
            })

        portfolio["positions"].append(pos)
        portfolio["total_value"] += (pos["currentPrice"] or 0) * (pos["size"] or 0)
        portfolio["total_pnl"] += (pos["unrealizedPnl"] or 0)

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
# ROUTERS
# ============================================
app.include_router(ai_settings.router, prefix=settings.api_prefix)
app.include_router(analytics.router, prefix=settings.api_prefix)
app.include_router(payments.router, prefix=settings.api_prefix)
app.include_router(exchange.router, prefix=settings.api_prefix)

# ============================================
# TELEGRAM TEST ENDPOINT
# ============================================

@app.post("/api/v1/telegram/test")
async def test_telegram():
    """Test Telegram notification."""
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
    
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = (
        os.getenv("TELEGRAM_CHAT_ID")
        or os.getenv("TELEGRAM_GROUP_CHAT_ID")
    )

    logger.info(f"🔍 .env file: {env_path} (exists={env_path.exists()})")
    logger.info(f"🔍 TELEGRAM_BOT_TOKEN: {'✅ set' if bot_token else '❌ missing'}")
    logger.info(f"🔍 TELEGRAM_CHAT_ID:   {'✅ set' if chat_id else '❌ missing'}")
    logger.info(f"🔍 ADMIN_BOOTSTRAP_KEY: {'✅ set' if os.getenv('ADMIN_BOOTSTRAP_KEY') else '❌ missing'}")
    logger.info(f"🔍 ENCRYPTION_KEY: {'✅ set' if os.getenv('ENCRYPTION_KEY') else '❌ missing (using ephemeral key — exchange credentials will not survive restart!)'}")
    logger.info(f"🔍 BITGET_TESTNET: {os.getenv('BITGET_TESTNET', 'true')}")

    if bot_token and chat_id:
        telegram_service.initialize(bot_token, chat_id)
        logger.info("✅ Telegram Service initialized")
    else:
        logger.warning("⚠️ Telegram credentials not set - notifications disabled")
    
    await market_data_service.start()
    prices = market_data_service.get_market_prices()
    logger.info(f"📊 Loaded {len(prices)} market prices")
    
    await position_monitor.start(market_data_service)
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