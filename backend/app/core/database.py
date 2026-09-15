from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .config import settings
import logging

logger = logging.getLogger(__name__)

# Determine if we're using SQLite
is_sqlite = "sqlite" in settings.database_url

# Create engine with appropriate settings
if is_sqlite:
    engine = create_engine(
        settings.database_url,
        connect_args={"check_same_thread": False},
        pool_size=settings.database_pool_size,
        max_overflow=40,
        pool_pre_ping=True,
    )
    logger.info("✅ SQLite database configured")
else:
    engine = create_engine(
        settings.database_url,
        pool_size=settings.database_pool_size,
        max_overflow=40,
        pool_pre_ping=True,
        echo=False,  # Set to True for SQL debugging
    )
    logger.info("✅ PostgreSQL database configured")

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

# ============================================
# Database Dependency for FastAPI
# ============================================
def get_db():
    """
    Database dependency for FastAPI routes.
    Usage: db: Session = Depends(get_db)
    """
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

# ============================================
# Database Initialization
# ============================================
def init_db():
    """
    Initialize database - create all tables.
    Call this on application startup.
    """
    try:
        # Import all models here to ensure they are registered
        from ..models import user, trade, position, subscription, payment, risk_event
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Database tables created/verified successfully")
        return True
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        return False

# ============================================
# Database Health Check
# ============================================
def check_db_connection() -> bool:
    """
    Check if database connection is healthy.
    Returns True if connected, False otherwise.
    """
    try:
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        return True
    except Exception as e:
        logger.error(f"❌ Database connection check failed: {e}")
        return False

# ============================================
# Helper: Get database info
# ============================================
def get_db_info() -> dict:
    """
    Get database connection information.
    """
    return {
        "url": settings.database_url.split('@')[-1] if '@' in settings.database_url else settings.database_url,
        "type": "sqlite" if is_sqlite else "postgresql",
        "pool_size": settings.database_pool_size,
        "connected": check_db_connection()
    }