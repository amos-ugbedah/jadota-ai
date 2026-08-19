from sqlalchemy import Column, String, DateTime, Integer, DECIMAL, ForeignKey, Index
from sqlalchemy.sql import func
import uuid
from ..core.database import Base

class OHLCV(Base):
    __tablename__ = "ohlcv_data"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    symbol = Column(String(20), nullable=False)
    exchange = Column(String(20), nullable=False, default="BITGET")
    interval = Column(String(10), nullable=False)  # 1m, 5m, 15m, 1h, 4h, 1d, 1w
    
    timestamp = Column(DateTime, nullable=False)
    open = Column(DECIMAL(15, 8), nullable=False)
    high = Column(DECIMAL(15, 8), nullable=False)
    low = Column(DECIMAL(15, 8), nullable=False)
    close = Column(DECIMAL(15, 8), nullable=False)
    volume = Column(DECIMAL(25, 8), nullable=False)
    
    # Additional metrics
    number_of_trades = Column(Integer)
    vwap = Column(DECIMAL(15, 8))
    
    created_at = Column(DateTime, server_default=func.now())

    # Indexes for fast queries
    __table_args__ = (
        Index('idx_ohlcv_symbol_interval', symbol, interval),
        Index('idx_ohlcv_timestamp', timestamp),
        Index('idx_ohlcv_symbol_interval_timestamp', symbol, interval, timestamp),
    )

class CurrentPrice(Base):
    __tablename__ = "current_prices"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    symbol = Column(String(20), nullable=False, unique=True, index=True)
    price = Column(DECIMAL(15, 8), nullable=False)
    bid = Column(DECIMAL(15, 8))
    ask = Column(DECIMAL(15, 8))
    volume_24h = Column(DECIMAL(25, 8))
    high_24h = Column(DECIMAL(15, 8))
    low_24h = Column(DECIMAL(15, 8))
    
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        Index('idx_current_prices_symbol', symbol),
    )
