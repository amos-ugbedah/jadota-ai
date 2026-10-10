"""
Position model — persistent storage for demo + live trading positions.

Columns map directly to the camelCase dict the API and frontend expect,
via row_to_dict() in services/position_store.py.

Task #4b additions:
    reconciliation_status — "synced" | "orphaned" | "error" | NULL (demo)
    last_reconciled_at    — timestamp of last Bitget check
"""

from sqlalchemy import Column, String, Float, DateTime, Text
from sqlalchemy.sql import func
import uuid

from ..core.database import Base


class Position(Base):
    __tablename__ = "positions"
    __table_args__ = {"extend_existing": True}

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), nullable=False, index=True)

    symbol = Column(String(20), nullable=False, index=True)
    side = Column(String(10), nullable=False)  # BUY / SELL

    # Position sizing
    size = Column(Float, nullable=False, default=0.0)
    entry_price = Column(Float, nullable=False, default=0.0)
    current_price = Column(Float, default=0.0)

    # P&L
    unrealized_pnl = Column(Float, default=0.0)
    realized_pnl = Column(Float, default=0.0)

    # Optional amount metadata (set by AI trades)
    trade_amount = Column(Float, nullable=True)
    base_amount = Column(Float, nullable=True)

    # Risk management
    stop_loss = Column(Float, nullable=True)
    take_profit = Column(Float, nullable=True)
    stop_loss_pct = Column(Float, nullable=True)
    take_profit_pct = Column(Float, nullable=True)

    # AI metadata
    ai_confidence = Column(Float, nullable=True)
    ai_reasoning = Column(Text, nullable=True)

    # Lifecycle
    status = Column(String(20), default="OPEN", index=True)
    close_reason = Column(String(30), nullable=True)  # STOP_LOSS / TAKE_PROFIT / MANUAL / RECONCILED_CANCELLED
    opened_at = Column(DateTime, default=func.now())
    closed_at = Column(DateTime, nullable=True)

    # Bitget linkage (Task #4a-2)
    bitget_order_id = Column(String(100), nullable=True, index=True)
    source = Column(String(20), default="demo", index=True)  # demo | bitget

    # 🔥 Task #4b: reconciliation metadata
    reconciliation_status = Column(String(20), nullable=True, index=True)
    last_reconciled_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    def __repr__(self):
        return f"<Position {self.id[:8]} {self.symbol} {self.side} {self.status} src={self.source}>"