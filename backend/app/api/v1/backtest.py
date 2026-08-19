from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import json
import logging

from ...core.database import get_db
from ...models.backtest import BacktestRun
from ...schemas.backtest import BacktestRequest, BacktestResponse, OptimizationRequest
from ...trading.backtest_engine import backtest_engine
from ...trading.walk_forward import walk_forward_tester
from ...api.dependencies import get_current_user
from ...models.user import User

router = APIRouter(prefix="/backtest", tags=["Backtesting"])
logger = logging.getLogger(__name__)

@router.post("/run", response_model=Dict[str, Any])
async def run_backtest(
    request: BacktestRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Run a backtest on historical data.
    """
    # Create backtest record
    backtest = BacktestRun(
        user_id=current_user.id,
        strategy_name=request.strategy_name,
        symbols=request.symbols,
        start_date=request.start_date,
        end_date=request.end_date,
        initial_capital=request.initial_capital,
        risk_level=request.risk_level,
        parameters=request.parameters or {},
        status="RUNNING",
        started_at=datetime.utcnow()
    )
    db.add(backtest)
    db.commit()
    db.refresh(backtest)
    
    # Run backtest in background
    background_tasks.add_task(
        _run_backtest_task,
        backtest.id,
        request.symbols[0],  # For now, only first symbol
        request.start_date,
        request.end_date,
        float(request.initial_capital),
        request.risk_level,
        request.parameters or {},
        db
    )
    
    return {
        'id': backtest.id,
        'status': 'RUNNING',
        'message': 'Backtest started',
        'check_status': f'/api/v1/backtest/{backtest.id}/status'
    }

@router.get("/{backtest_id}/status", response_model=BacktestResponse)
async def get_backtest_status(
    backtest_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get backtest status and results.
    """
    backtest = db.query(BacktestRun).filter(
        BacktestRun.id == backtest_id,
        BacktestRun.user_id == current_user.id
    ).first()
    
    if not backtest:
        raise HTTPException(status_code=404, detail="Backtest not found")
    
    return backtest

@router.get("/history", response_model=List[BacktestResponse])
async def get_backtest_history(
    limit: int = Query(10, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get user's backtest history.
    """
    backtests = db.query(BacktestRun).filter(
        BacktestRun.user_id == current_user.id
    ).order_by(BacktestRun.created_at.desc()).limit(limit).all()
    
    return backtests

@router.post("/walk-forward")
async def run_walk_forward(
    symbol: str,
    start_date: datetime,
    end_date: datetime,
    initial_capital: float = 10000,
    risk_level: str = "MODERATE",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Run walk-forward testing.
    """
    result = await walk_forward_tester.run_walk_forward(
        db,
        symbol,
        start_date,
        end_date,
        initial_capital,
        risk_level
    )
    
    return {
        'symbol': symbol,
        'walk_forward_results': result
    }

@router.post("/optimize")
async def optimize_strategy(
    request: OptimizationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Optimize strategy parameters.
    """
    # This is a placeholder for parameter optimization
    # In practice, you'd run multiple backtests with different parameters
    results = []
    
    # Generate parameter combinations
    param_combinations = _generate_param_combinations(request.param_ranges)
    
    for params in param_combinations[:request.iterations]:
        result = await backtest_engine.run_backtest(
            db,
            request.symbol,
            request.start_date,
            request.end_date,
            float(request.initial_capital),
            "MODERATE",
            params
        )
        
        if 'error' not in result:
            results.append({
                'parameters': params,
                'metrics': result['metrics'],
                'final_capital': result.get('final_capital', 0),
                'total_trades': result.get('total_trades', 0)
            })
    
    # Sort by Sharpe ratio (or other metric)
    if results:
        results.sort(key=lambda x: x['metrics'].get('sharpe_ratio', 0), reverse=True)
    
    return {
        'strategy': request.strategy_name,
        'symbol': request.symbol,
        'iterations': len(results),
        'best_parameters': results[0] if results else None,
        'all_results': results[:10]  # Return top 10
    }

# Background task
async def _run_backtest_task(
    backtest_id: str,
    symbol: str,
    start_date: datetime,
    end_date: datetime,
    initial_capital: float,
    risk_level: str,
    parameters: Dict[str, Any],
    db: Session
):
    """Run backtest in background."""
    try:
        result = await backtest_engine.run_backtest(
            db,
            symbol,
            start_date,
            end_date,
            initial_capital,
            risk_level,
            parameters
        )
        
        # Update backtest record
        backtest = db.query(BacktestRun).filter(BacktestRun.id == backtest_id).first()
        if backtest:
            if 'error' in result:
                backtest.status = "FAILED"
                backtest.parameters = {**backtest.parameters, 'error': result['error']}
            else:
                metrics = result['metrics']
                backtest.status = "COMPLETED"
                backtest.final_capital = result.get('final_capital', 0)
                backtest.total_return = metrics.get('total_return', 0)
                backtest.win_rate = metrics.get('win_rate', 0)
                backtest.profit_factor = metrics.get('profit_factor', 0)
                backtest.max_drawdown = metrics.get('max_drawdown', 0)
                backtest.sharpe_ratio = metrics.get('sharpe_ratio', 0)
                backtest.sortino_ratio = metrics.get('sortino_ratio', 0)
                backtest.total_trades = metrics.get('total_trades', 0)
                backtest.winning_trades = metrics.get('winning_trades', 0)
                backtest.losing_trades = metrics.get('losing_trades', 0)
                backtest.avg_win = metrics.get('avg_win', 0)
                backtest.avg_loss = metrics.get('avg_loss', 0)
                backtest.completed_at = datetime.utcnow()
                
                # Store trade and equity data (simplified)
                backtest.walk_forward_results = {
                    'trades': result.get('trades', [])[-50:],  # Last 50 trades
                    'equity_curve': result.get('equity_curve', [])[-100:]  # Last 100 points
                }
            
            db.commit()
            
    except Exception as e:
        logger.error(f"Backtest task error: {e}")
        backtest = db.query(BacktestRun).filter(BacktestRun.id == backtest_id).first()
        if backtest:
            backtest.status = "FAILED"
            backtest.parameters = {**backtest.parameters, 'error': str(e)}
            db.commit()

def _generate_param_combinations(param_ranges: Dict[str, List[Any]]) -> List[Dict[str, Any]]:
    """Generate parameter combinations for optimization."""
    import itertools
    
    keys = list(param_ranges.keys())
    values = list(param_ranges.values())
    
    combinations = []
    for combo in itertools.product(*values):
        combinations.append(dict(zip(keys, combo)))
    
    return combinations
