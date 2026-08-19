from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal

class BacktestRequest(BaseModel):
    strategy_name: str = Field(..., description="Strategy name")
    symbols: List[str] = Field(..., description="Symbols to backtest")
    start_date: datetime = Field(..., description="Start date")
    end_date: datetime = Field(..., description="End date")
    initial_capital: Decimal = Field(10000, description="Starting capital")
    risk_level: str = Field("MODERATE", description="Risk level: LOW, MODERATE, HIGH")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Strategy parameters")

class BacktestResponse(BaseModel):
    id: str
    strategy_name: str
    symbols: List[str]
    start_date: datetime
    end_date: datetime
    initial_capital: Decimal
    final_capital: Decimal
    total_return: Decimal
    annualized_return: Decimal
    win_rate: Decimal
    profit_factor: Decimal
    max_drawdown: Decimal
    sharpe_ratio: Decimal
    sortino_ratio: Decimal
    calmar_ratio: Decimal
    total_trades: int
    winning_trades: int
    losing_trades: int
    avg_win: Decimal
    avg_loss: Decimal
    fees: Decimal
    estimated_slippage: Decimal
    status: str
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True

class BacktestResult(BaseModel):
    id: str
    trades: List[Dict[str, Any]]
    equity_curve: List[Dict[str, Any]]
    metrics: Dict[str, Any]
    
class OptimizationRequest(BaseModel):
    strategy_name: str
    symbol: str
    start_date: datetime
    end_date: datetime
    param_ranges: Dict[str, List[Any]]
    initial_capital: Decimal = 10000
    iterations: int = 100
