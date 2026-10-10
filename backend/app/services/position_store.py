"""
Persistent position store.

Positions live in the `positions` Postgres table. All API consumers
(main.py, analytics.py, position_monitor.py) go through these helpers,
which convert between the DB rows and the camelCase dicts the API
and frontend use.

Public API (first arg is always a SQLAlchemy Session):
    list_positions(db, user_id=None, status=None, limit=None) -> List[Dict]
    get_position(db, position_id) -> Optional[Dict]
    create_position(db, data) -> Dict
    update_position(db, position_id, updates) -> Optional[Dict]
    close_position(db, position_id, reason, exit_price=None) -> Optional[Dict]
"""

from datetime import datetime
from typing import Optional, List, Dict, Any

from sqlalchemy.orm import Session

from ..models.position import Position


# ============================================
# Serialization
# ============================================
def row_to_dict(row: Position) -> Dict[str, Any]:
    """Convert a Position row to the camelCase dict the API expects."""
    return {
        "id": row.id,
        "user_id": row.user_id,
        "symbol": row.symbol,
        "side": row.side,
        "size": row.size,
        "entryPrice": row.entry_price,
        "currentPrice": row.current_price,
        "unrealizedPnl": row.unrealized_pnl,
        "realizedPnl": row.realized_pnl,
        "tradeAmount": row.trade_amount,
        "baseAmount": row.base_amount,
        "stopLoss": row.stop_loss,
        "takeProfit": row.take_profit,
        "stopLossPct": row.stop_loss_pct,
        "takeProfitPct": row.take_profit_pct,
        "aiConfidence": row.ai_confidence,
        "aiReasoning": row.ai_reasoning,
        "status": row.status,
        "closeReason": row.close_reason,
        "openedAt": row.opened_at.isoformat() if row.opened_at else None,
        "closedAt": row.closed_at.isoformat() if row.closed_at else None,
        # 🔥 Task #4a-2
        "bitgetOrderId": row.bitget_order_id,
        "source": row.source,
        "createdAt": row.created_at.isoformat() if row.created_at else None,
        "updatedAt": row.updated_at.isoformat() if row.updated_at else None,
    }


def _parse_dt(v):
    if v is None or isinstance(v, datetime):
        return v
    try:
        return datetime.fromisoformat(str(v).replace("Z", "+00:00"))
    except Exception:
        return None


# ============================================
# Queries
# ============================================
def list_positions(
    db: Session,
    user_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """Fetch positions with optional filters. Newest first."""
    q = db.query(Position)
    if user_id:
        q = q.filter(Position.user_id == user_id)
    if status:
        q = q.filter(Position.status == status)
    q = q.order_by(Position.opened_at.desc())
    if limit:
        q = q.limit(limit)
    return [row_to_dict(r) for r in q.all()]


def get_position(db: Session, position_id: str) -> Optional[Dict[str, Any]]:
    """Fetch a single position by ID."""
    row = db.query(Position).filter(Position.id == position_id).first()
    return row_to_dict(row) if row else None


def get_position_row(db: Session, position_id: str) -> Optional[Position]:
    """Raw row access for callers that need to mutate."""
    return db.query(Position).filter(Position.id == position_id).first()


# ============================================
# Writes
# ============================================
def create_position(db: Session, data: Dict[str, Any]) -> Dict[str, Any]:
    """Insert a new position from a camelCase dict."""
    row = Position(
        id=data.get("id"),
        user_id=data["user_id"],
        symbol=data["symbol"],
        side=data["side"],
        size=float(data.get("size", 0.0)),
        entry_price=float(data.get("entryPrice", 0.0)),
        current_price=float(data.get("currentPrice", data.get("entryPrice", 0.0))),
        unrealized_pnl=float(data.get("unrealizedPnl", 0.0)),
        realized_pnl=float(data.get("realizedPnl", 0.0)),
        trade_amount=data.get("tradeAmount"),
        base_amount=data.get("baseAmount"),
        stop_loss=data.get("stopLoss"),
        take_profit=data.get("takeProfit"),
        stop_loss_pct=data.get("stopLossPct"),
        take_profit_pct=data.get("takeProfitPct"),
        ai_confidence=data.get("aiConfidence"),
        ai_reasoning=data.get("aiReasoning"),
        status=data.get("status", "OPEN"),
        close_reason=data.get("closeReason"),
        opened_at=_parse_dt(data.get("openedAt")) or datetime.utcnow(),
        # 🔥 Task #4a-2
        bitget_order_id=data.get("bitgetOrderId"),
        source=data.get("source", "demo"),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row_to_dict(row)


_CAMEL_TO_SNAKE = {
    "currentPrice": "current_price",
    "unrealizedPnl": "unrealized_pnl",
    "realizedPnl": "realized_pnl",
    "entryPrice": "entry_price",
    "stopLoss": "stop_loss",
    "takeProfit": "take_profit",
    "stopLossPct": "stop_loss_pct",
    "takeProfitPct": "take_profit_pct",
    "aiConfidence": "ai_confidence",
    "aiReasoning": "ai_reasoning",
    "tradeAmount": "trade_amount",
    "baseAmount": "base_amount",
    "closeReason": "close_reason",
    "status": "status",
    "size": "size",
    "symbol": "symbol",
    "side": "side",
    # 🔥 Task #4a-2
    "bitgetOrderId": "bitget_order_id",
    "source": "source",
}


def update_position(
    db: Session, position_id: str, updates: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """Apply camelCase updates to a position. Returns the updated dict."""
    row = db.query(Position).filter(Position.id == position_id).first()
    if not row:
        return None

    for key, value in updates.items():
        if key == "closedAt":
            row.closed_at = _parse_dt(value)
            continue
        if key == "openedAt":
            row.opened_at = _parse_dt(value)
            continue
        col = _CAMEL_TO_SNAKE.get(key)
        if col:
            setattr(row, col, value)

    db.commit()
    db.refresh(row)
    return row_to_dict(row)


def close_position(
    db: Session,
    position_id: str,
    reason: str,
    exit_price: Optional[float] = None,
) -> Optional[Dict[str, Any]]:
    """Mark a position CLOSED, computing realized P&L."""
    row = db.query(Position).filter(Position.id == position_id).first()
    if not row or row.status == "CLOSED":
        return row_to_dict(row) if row else None

    price = float(exit_price) if exit_price is not None else float(row.current_price or 0.0)
    if row.side == "BUY":
        realized = (price - row.entry_price) * row.size
    else:
        realized = (row.entry_price - price) * row.size

    row.current_price = price
    row.realized_pnl = round(realized, 8)
    row.status = "CLOSED"
    row.close_reason = reason
    row.closed_at = datetime.utcnow()

    db.commit()
    db.refresh(row)
    return row_to_dict(row)


# ============================================
# Backwards-compat shim
# ============================================
positions: list = []