"""
Advanced Analytics endpoints.

All endpoints require auth and return data for the current user only.

Data source: `services.position_store.positions` — the same in-memory list
that `main.py` writes to when opening/closing demo trades.
"""

from fastapi import APIRouter, Depends, HTTPException, Header, Query, status
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from collections import defaultdict
import math
import statistics

from ...core.database import SessionLocal
from ...core.security import decode_token, get_token_from_header
from ...models.user import User
from ...services.position_store import positions as _all_positions


router = APIRouter(prefix="/analytics", tags=["analytics"])


# ============================================
# Auth dependency (self-contained to avoid circular imports)
# ============================================
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_current_user(
    authorization: str = Header(None),
    db: Session = Depends(get_db),
):
    token = get_token_from_header(authorization)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header",
        )
    payload = decode_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user


# ============================================
# Helpers
# ============================================
def _positions_for(user_id: str) -> List[Dict[str, Any]]:
    """Return all positions belonging to a user."""
    return [p for p in _all_positions if p.get("user_id") == user_id]


def _closed_for(user_id: str) -> List[Dict[str, Any]]:
    """Return all CLOSED positions for a user, sorted by close time."""
    closed = [
        p
        for p in _positions_for(user_id)
        if p.get("status") == "CLOSED" and p.get("closedAt")
    ]
    closed.sort(key=lambda p: p.get("closedAt", ""))
    return closed


def _parse_iso(dt_str: Optional[str]) -> Optional[datetime]:
    if not dt_str:
        return None
    try:
        return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
    except Exception:
        return None


def _safe_float(v: Any, default: float = 0.0) -> float:
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


# ============================================
# 1. SUMMARY — high level stats
# ============================================
@router.get("/summary")
async def get_summary(current_user: User = Depends(get_current_user)):
    """
    High-level performance summary:
    total trades, win rate, avg win/loss, profit factor, best/worst trade, streaks.
    """
    all_pos = _positions_for(current_user.id)
    closed = _closed_for(current_user.id)
    open_pos = [p for p in all_pos if p.get("status") == "OPEN"]

    if not closed:
        return {
            "total_trades": len(all_pos),
            "open_positions": len(open_pos),
            "closed_positions": 0,
            "win_rate": 0.0,
            "avg_win": 0.0,
            "avg_loss": 0.0,
            "profit_factor": 0.0,
            "total_realized_pnl": 0.0,
            "total_unrealized_pnl": sum(
                _safe_float(p.get("unrealizedPnl")) for p in open_pos
            ),
            "total_pnl": 0.0,
            "best_trade": 0.0,
            "worst_trade": 0.0,
            "avg_trade_pnl": 0.0,
            "max_win_streak": 0,
            "max_loss_streak": 0,
            "current_streak": 0,
        }

    pnls = [_safe_float(p.get("realizedPnl")) for p in closed]
    wins = [x for x in pnls if x > 0]
    losses = [x for x in pnls if x < 0]

    gross_profit = sum(wins)
    gross_loss = abs(sum(losses))

    # Streaks
    max_win_streak = 0
    max_loss_streak = 0
    current_win_streak = 0
    current_loss_streak = 0
    for x in pnls:
        if x > 0:
            current_win_streak += 1
            current_loss_streak = 0
            max_win_streak = max(max_win_streak, current_win_streak)
        elif x < 0:
            current_loss_streak += 1
            current_win_streak = 0
            max_loss_streak = max(max_loss_streak, current_loss_streak)
        else:
            current_win_streak = 0
            current_loss_streak = 0

    total_unrealized = sum(_safe_float(p.get("unrealizedPnl")) for p in open_pos)

    return {
        "total_trades": len(all_pos),
        "open_positions": len(open_pos),
        "closed_positions": len(closed),
        "win_rate": round(len(wins) / len(closed) * 100, 2) if closed else 0.0,
        "avg_win": round(statistics.mean(wins), 2) if wins else 0.0,
        "avg_loss": round(statistics.mean(losses), 2) if losses else 0.0,
        "profit_factor": (
            round(gross_profit / gross_loss, 2) if gross_loss > 0 else 0.0
        ),
        "total_realized_pnl": round(sum(pnls), 2),
        "total_unrealized_pnl": round(total_unrealized, 2),
        "total_pnl": round(sum(pnls) + total_unrealized, 2),
        "best_trade": round(max(pnls), 2) if pnls else 0.0,
        "worst_trade": round(min(pnls), 2) if pnls else 0.0,
        "avg_trade_pnl": round(statistics.mean(pnls), 2) if pnls else 0.0,
        "max_win_streak": max_win_streak,
        "max_loss_streak": max_loss_streak,
        "current_streak": current_win_streak if current_win_streak else -current_loss_streak,
    }


# ============================================
# 2. EQUITY CURVE — daily portfolio value over time
# ============================================
@router.get("/equity-curve")
async def get_equity_curve(
    days: int = Query(30, ge=1, le=365),
    initial_balance: float = Query(10000.0, gt=0),
    current_user: User = Depends(get_current_user),
):
    """
    Return daily portfolio balance for the last N days.

    Shape:
      [{"time": "2026-09-01", "value": 10045.2, "dailyPnl": 45.2}, ...]
    """
    closed = _closed_for(current_user.id)

    end_date = datetime.utcnow().date()
    start_date = end_date - timedelta(days=days - 1)

    # Group realized P&L by close day
    daily_pnl: Dict[Any, float] = defaultdict(float)
    for p in closed:
        dt = _parse_iso(p.get("closedAt"))
        if not dt:
            continue
        d = dt.date()
        if d < start_date:
            continue
        daily_pnl[d] += _safe_float(p.get("realizedPnl"))

    # Also include today's unrealized P&L into the final point (mark-to-market)
    open_positions = [p for p in _positions_for(current_user.id) if p.get("status") == "OPEN"]

    points: List[Dict[str, Any]] = []
    balance = initial_balance
    current = start_date
    while current <= end_date:
        pnl = daily_pnl.get(current, 0.0)
        balance += pnl
        points.append({
            "time": current.isoformat(),
            "value": round(balance, 2),
            "dailyPnl": round(pnl, 2),
        })
        current += timedelta(days=1)

    # Optionally append unrealized as the very last value (today's mark)
    if open_positions:
        unrealized = sum(_safe_float(p.get("unrealizedPnl")) for p in open_positions)
        if points:
            points[-1]["value"] = round(points[-1]["value"] + unrealized, 2)

    return {
        "points": points,
        "initial_balance": initial_balance,
        "final_balance": points[-1]["value"] if points else initial_balance,
        "total_return_pct": (
            round((points[-1]["value"] - initial_balance) / initial_balance * 100, 2)
            if points
            else 0.0
        ),
    }


# ============================================
# 3. DRAWDOWN — peak-to-trough decline
# ============================================
@router.get("/drawdown")
async def get_drawdown(
    days: int = Query(30, ge=1, le=365),
    initial_balance: float = Query(10000.0, gt=0),
    current_user: User = Depends(get_current_user),
):
    """
    Return drawdown over time:
      [{"time": "2026-09-01", "value": -2.5, "peak": 10100.0}, ...]
    `value` is negative percentage from peak.
    """
    # Reuse equity logic
    equity = await get_equity_curve(days=days, initial_balance=initial_balance, current_user=current_user)
    points = equity["points"]

    peak = initial_balance
    max_dd = 0.0
    max_dd_time = None
    out = []
    for p in points:
        v = p["value"]
        if v > peak:
            peak = v
        dd = (v - peak) / peak * 100 if peak > 0 else 0.0
        if dd < max_dd:
            max_dd = dd
            max_dd_time = p["time"]
        out.append({
            "time": p["time"],
            "value": round(dd, 2),
            "peak": round(peak, 2),
        })

    return {
        "points": out,
        "max_drawdown_pct": round(max_dd, 2),
        "max_drawdown_at": max_dd_time,
    }


# ============================================
# 4. WIN/LOSS HISTOGRAM
# ============================================
@router.get("/win-loss")
async def get_win_loss(current_user: User = Depends(get_current_user)):
    """
    Bucketed histogram of realized P&L.
    Returns fixed buckets with counts.
    """
    closed = _closed_for(current_user.id)
    pnls = [_safe_float(p.get("realizedPnl")) for p in closed]

    # Fixed buckets (dollar amounts)
    buckets = [
        {"label": "< -$100", "min": -math.inf, "max": -100, "count": 0, "type": "loss"},
        {"label": "-$100 to -$50", "min": -100, "max": -50, "count": 0, "type": "loss"},
        {"label": "-$50 to -$10", "min": -50, "max": -10, "count": 0, "type": "loss"},
        {"label": "-$10 to $0", "min": -10, "max": 0, "count": 0, "type": "loss"},
        {"label": "$0 to $10", "min": 0, "max": 10, "count": 0, "type": "win"},
        {"label": "$10 to $50", "min": 10, "max": 50, "count": 0, "type": "win"},
        {"label": "$50 to $100", "min": 50, "max": 100, "count": 0, "type": "win"},
        {"label": "> $100", "min": 100, "max": math.inf, "count": 0, "type": "win"},
    ]

    for x in pnls:
        for b in buckets:
            if b["min"] <= x < b["max"]:
                b["count"] += 1
                break

    # Strip the internal min/max before returning
    clean = [{"label": b["label"], "count": b["count"], "type": b["type"]} for b in buckets]

    wins = sum(1 for x in pnls if x > 0)
    losses = sum(1 for x in pnls if x < 0)
    breakeven = sum(1 for x in pnls if x == 0)

    return {
        "buckets": clean,
        "wins": wins,
        "losses": losses,
        "breakeven": breakeven,
        "total": len(pnls),
    }


# ============================================
# 5. BY SYMBOL — best/worst performers
# ============================================
@router.get("/by-symbol")
async def get_by_symbol(current_user: User = Depends(get_current_user)):
    """
    Per-symbol performance breakdown.
    """
    closed = _closed_for(current_user.id)

    by_sym: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
        "symbol": "",
        "trades": 0,
        "wins": 0,
        "losses": 0,
        "pnl": 0.0,
        "gross_profit": 0.0,
        "gross_loss": 0.0,
    })

    for p in closed:
        sym = p.get("symbol", "Unknown")
        pnl = _safe_float(p.get("realizedPnl"))
        d = by_sym[sym]
        d["symbol"] = sym
        d["trades"] += 1
        d["pnl"] += pnl
        if pnl > 0:
            d["wins"] += 1
            d["gross_profit"] += pnl
        elif pnl < 0:
            d["losses"] += 1
            d["gross_loss"] += abs(pnl)

    rows = []
    for d in by_sym.values():
        rows.append({
            "symbol": d["symbol"],
            "trades": d["trades"],
            "wins": d["wins"],
            "losses": d["losses"],
            "win_rate": round(d["wins"] / d["trades"] * 100, 2) if d["trades"] else 0.0,
            "pnl": round(d["pnl"], 2),
            "avg_pnl": round(d["pnl"] / d["trades"], 2) if d["trades"] else 0.0,
            "profit_factor": (
                round(d["gross_profit"] / d["gross_loss"], 2)
                if d["gross_loss"] > 0
                else 0.0
            ),
        })

    rows.sort(key=lambda r: r["pnl"], reverse=True)

    return {
        "symbols": rows,
        "best": rows[0] if rows else None,
        "worst": rows[-1] if rows else None,
    }


# ============================================
# 6. MONTHLY HEATMAP
# ============================================
@router.get("/monthly-heatmap")
async def get_monthly_heatmap(
    months: int = Query(6, ge=1, le=24),
    current_user: User = Depends(get_current_user),
):
    """
    Monthly P&L aggregation for a heatmap.
    """
    closed = _closed_for(current_user.id)

    now = datetime.utcnow()
    # Build list of (year, month) for the last N months
    keys = []
    y, m = now.year, now.month
    for _ in range(months):
        keys.append((y, m))
        m -= 1
        if m == 0:
            m = 12
            y -= 1
    keys.reverse()  # oldest → newest

    monthly: Dict[Any, Dict[str, Any]] = {
        k: {"year": k[0], "month": k[1], "pnl": 0.0, "trades": 0, "wins": 0}
        for k in keys
    }

    for p in closed:
        dt = _parse_iso(p.get("closedAt"))
        if not dt:
            continue
        key = (dt.year, dt.month)
        if key not in monthly:
            continue
        pnl = _safe_float(p.get("realizedPnl"))
        monthly[key]["pnl"] += pnl
        monthly[key]["trades"] += 1
        if pnl > 0:
            monthly[key]["wins"] += 1

    out = []
    for k in keys:
        d = monthly[k]
        out.append({
            "year": d["year"],
            "month": d["month"],
            "label": f"{d['year']}-{d['month']:02d}",
            "pnl": round(d["pnl"], 2),
            "trades": d["trades"],
            "win_rate": round(d["wins"] / d["trades"] * 100, 2) if d["trades"] else 0.0,
        })

    return {"months": out}


# ============================================
# 7. RISK RATIOS — Sharpe, Sortino, Calmar, Max DD
# ============================================
@router.get("/ratios")
async def get_ratios(
    days: int = Query(30, ge=1, le=365),
    initial_balance: float = Query(10000.0, gt=0),
    risk_free_rate: float = Query(0.0),
    current_user: User = Depends(get_current_user),
):
    """
    Risk-adjusted performance metrics computed from daily returns.
    """
    equity = await get_equity_curve(days=days, initial_balance=initial_balance, current_user=current_user)
    points = equity["points"]

    # Compute daily returns
    returns: List[float] = []
    for i in range(1, len(points)):
        prev = points[i - 1]["value"]
        cur = points[i]["value"]
        if prev > 0:
            returns.append((cur - prev) / prev)

    if len(returns) < 2:
        return {
            "sharpe": 0.0,
            "sortino": 0.0,
            "calmar": 0.0,
            "max_drawdown_pct": 0.0,
            "volatility_annual_pct": 0.0,
            "avg_daily_return_pct": 0.0,
            "total_return_pct": equity["total_return_pct"],
            "sample_days": len(returns),
        }

    mean_r = statistics.mean(returns)
    std_r = statistics.stdev(returns)
    downside = [r for r in returns if r < 0]
    downside_std = statistics.stdev(downside) if len(downside) >= 2 else 0.0

    sharpe = ((mean_r - risk_free_rate) / std_r * math.sqrt(365)) if std_r > 0 else 0.0
    sortino = ((mean_r - risk_free_rate) / downside_std * math.sqrt(365)) if downside_std > 0 else 0.0

    dd_resp = await get_drawdown(days=days, initial_balance=initial_balance, current_user=current_user)
    max_dd = dd_resp["max_drawdown_pct"]

    # Calmar = annualized return / |max drawdown|
    annual_return_pct = equity["total_return_pct"] * (365 / max(len(points), 1))
    calmar = (annual_return_pct / abs(max_dd)) if max_dd < 0 else 0.0

    return {
        "sharpe": round(sharpe, 2),
        "sortino": round(sortino, 2),
        "calmar": round(calmar, 2),
        "max_drawdown_pct": round(max_dd, 2),
        "volatility_annual_pct": round(std_r * math.sqrt(365) * 100, 2),
        "avg_daily_return_pct": round(mean_r * 100, 4),
        "total_return_pct": equity["total_return_pct"],
        "sample_days": len(returns),
    }


# ============================================
# 8. TRADE JOURNAL — filterable list
# ============================================
@router.get("/trade-journal")
async def get_trade_journal(
    limit: int = Query(100, ge=1, le=500),
    symbol: Optional[str] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
    current_user: User = Depends(get_current_user),
):
    """
    Filterable list of all trades (open + closed), newest first.
    """
    trades = _positions_for(current_user.id)

    if symbol:
        trades = [t for t in trades if t.get("symbol") == symbol]
    if status_filter:
        trades = [t for t in trades if t.get("status") == status_filter.upper()]

    # Sort newest first (openedAt desc)
    trades.sort(key=lambda t: t.get("openedAt", ""), reverse=True)
    trades = trades[:limit]

    # Slimmed down view
    out = []
    for t in trades:
        out.append({
            "id": t.get("id"),
            "symbol": t.get("symbol"),
            "side": t.get("side"),
            "size": t.get("size"),
            "entryPrice": t.get("entryPrice"),
            "currentPrice": t.get("currentPrice"),
            "realizedPnl": _safe_float(t.get("realizedPnl")),
            "unrealizedPnl": _safe_float(t.get("unrealizedPnl")),
            "aiConfidence": t.get("aiConfidence"),
            "aiReasoning": t.get("aiReasoning"),
            "openedAt": t.get("openedAt"),
            "closedAt": t.get("closedAt"),
            "status": t.get("status"),
        })

    return {"trades": out, "count": len(out)}


# ============================================
# 9. DEMO DATA SEEDER (for testing analytics UI)
# ============================================
@router.post("/seed-demo-data")
async def seed_demo_data(
    request: dict,
    current_user: User = Depends(get_current_user),
):
    """
    Generate fake closed trades for the current user so the analytics UI
    has something to render.

    Body: {"key": "<ADMIN_BOOTSTRAP_KEY>", "count": 60}
    """
    import os
    import random
    import uuid

    key = request.get("key")
    expected = os.getenv("ADMIN_BOOTSTRAP_KEY")
    if not expected or key != expected:
        raise HTTPException(status_code=401, detail="Invalid seed key")

    count = int(request.get("count", 60))
    count = max(1, min(count, 500))

    symbols = ["BTC/USDT", "ETH/USDT", "SOL/USDT", "BNB/USDT"]
    now = datetime.utcnow()

    generated = 0
    for i in range(count):
        sym = random.choice(symbols)
        # 55% win rate, avg win ~$30, avg loss ~$20 → net positive
        is_win = random.random() < 0.55
        if is_win:
            pnl = round(random.uniform(5, 80), 2)
        else:
            pnl = round(-random.uniform(3, 45), 2)

        # Spread over the last 30 days
        days_ago = random.randint(0, 29)
        opened = now - timedelta(days=days_ago, hours=random.randint(1, 20))
        closed = opened + timedelta(hours=random.randint(1, 24))

        entry = round(random.uniform(20000, 90000), 2)
        _all_positions.append({
            "id": str(uuid.uuid4()),
            "symbol": sym,
            "side": random.choice(["BUY", "SELL"]),
            "size": round(random.uniform(0.001, 0.01), 6),
            "entryPrice": entry,
            "currentPrice": entry,
            "unrealizedPnl": 0.0,
            "realizedPnl": pnl,
            "stopLoss": round(entry * 0.98, 2),
            "takeProfit": round(entry * 1.04, 2),
            "stopLossPct": 0.02,
            "takeProfitPct": 0.04,
            "openedAt": opened.isoformat(),
            "closedAt": closed.isoformat(),
            "status": "CLOSED",
            "aiConfidence": random.randint(55, 92),
            "aiReasoning": "Seeded demo data",
            "user_id": current_user.id,
        })
        generated += 1

    return {"success": True, "generated": generated}