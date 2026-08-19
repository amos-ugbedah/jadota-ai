import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from decimal import Decimal
import logging
from sqlalchemy.orm import Session

from ..models.market_data import OHLCV
from ..ai.consensus_engine import consensus_engine

logger = logging.getLogger(__name__)

class BacktestEngine:
    """Backtesting engine for strategy validation."""
    
    def __init__(self):
        self.fee_rate = 0.001  # 0.1% trading fee
        self.slippage_rate = 0.0005  # 0.05% slippage
    
    async def run_backtest(
        self,
        db: Session,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        initial_capital: float,
        risk_level: str = "MODERATE",
        parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Run a backtest on historical data.
        """
        try:
            # Fetch historical data
            data = self._fetch_historical_data(db, symbol, start_date, end_date)
            if data.empty:
                return {'error': 'No data available for the specified period'}
            
            # Initialize backtest
            capital = float(initial_capital)
            position = None
            trades = []
            equity_curve = [{'timestamp': data.iloc[0]['timestamp'], 'equity': capital}]
            
            # Run the strategy on each candle
            for i in range(50, len(data)):
                current_data = data.iloc[:i+1].copy()
                current_price = current_data.iloc[-1]['close']
                timestamp = current_data.iloc[-1]['timestamp']
                
                # Get signal from AI engine
                signal = await consensus_engine.analyze(current_data, symbol)
                
                # Calculate position size based on risk level
                if signal.get('should_trade', False):
                    direction = signal.get('direction', 'NEUTRAL')
                    confidence = signal.get('confidence', 0)
                    opportunity_score = signal.get('opportunity_score', 0)
                    
                    if direction != 'NEUTRAL' and confidence > 60:
                        # Determine position size
                        position_size = self._calculate_position_size(
                            capital, current_price, risk_level, opportunity_score
                        )
                        
                        # Open or adjust position
                        if position is None:
                            # Open new position
                            position = self._open_position(
                                direction, current_price, position_size, 
                                timestamp, confidence, opportunity_score
                            )
                            trades.append(position)
                            capital -= position_size * current_price * (1 + self.fee_rate)
                        elif position['side'] == direction:
                            # Add to existing position (pyramiding)
                            pass
                        elif position['side'] != direction:
                            # Close position and open new one
                            # Close existing
                            close_result = self._close_position(position, current_price, timestamp)
                            capital += close_result['proceeds']
                            trades.append(close_result)
                            
                            # Open new
                            position = self._open_position(
                                direction, current_price, position_size,
                                timestamp, confidence, opportunity_score
                            )
                            trades.append(position)
                            capital -= position_size * current_price * (1 + self.fee_rate)
                
                # Update equity curve
                if position:
                    unrealized_pnl = self._calculate_unrealized_pnl(position, current_price)
                    total_equity = capital + unrealized_pnl
                else:
                    total_equity = capital
                
                equity_curve.append({'timestamp': timestamp, 'equity': total_equity})
            
            # Close any open position
            if position:
                final_price = data.iloc[-1]['close']
                close_result = self._close_position(position, final_price, data.iloc[-1]['timestamp'])
                capital += close_result['proceeds']
                trades.append(close_result)
            
            # Calculate performance metrics
            metrics = self._calculate_metrics(trades, equity_curve, initial_capital, capital)
            
            return {
                'trades': trades,
                'equity_curve': equity_curve,
                'metrics': metrics,
                'final_capital': capital,
                'total_trades': len([t for t in trades if t.get('type') == 'close'])
            }
            
        except Exception as e:
            logger.error(f"Backtest error: {e}")
            return {'error': str(e)}
    
    def _fetch_historical_data(
        self, 
        db: Session, 
        symbol: str, 
        start_date: datetime, 
        end_date: datetime
    ) -> pd.DataFrame:
        """Fetch historical OHLCV data from database."""
        data = db.query(OHLCV).filter(
            OHLCV.symbol == symbol,
            OHLCV.interval == '1h',
            OHLCV.timestamp >= start_date,
            OHLCV.timestamp <= end_date
        ).order_by(OHLCV.timestamp.asc()).all()
        
        if not data:
            return pd.DataFrame()
        
        return pd.DataFrame([{
            'timestamp': d.timestamp,
            'open': float(d.open),
            'high': float(d.high),
            'low': float(d.low),
            'close': float(d.close),
            'volume': float(d.volume)
        } for d in data])
    
    def _calculate_position_size(
        self, 
        capital: float, 
        price: float, 
        risk_level: str,
        opportunity_score: float
    ) -> float:
        """Calculate position size based on risk level."""
        # Base position size as % of capital
        risk_multipliers = {
            'LOW': 0.1,
            'MODERATE': 0.2,
            'HIGH': 0.3
        }
        base_pct = risk_multipliers.get(risk_level, 0.2)
        
        # Adjust based on opportunity score (70-100 -> 0.5-1.0 multiplier)
        score_multiplier = 0.5 + ((opportunity_score - 70) / 60)
        score_multiplier = max(0.5, min(1.0, score_multiplier))
        
        # Calculate position size
        position_pct = base_pct * score_multiplier
        position_value = capital * position_pct
        
        return position_value / price
    
    def _open_position(
        self,
        direction: str,
        price: float,
        size: float,
        timestamp: datetime,
        confidence: float,
        opportunity_score: float
    ) -> Dict[str, Any]:
        """Open a new position."""
        return {
            'type': 'open',
            'side': direction,
            'entry_price': price,
            'size': size,
            'timestamp': timestamp,
            'confidence': confidence,
            'opportunity_score': opportunity_score
        }
    
    def _close_position(
        self,
        position: Dict[str, Any],
        price: float,
        timestamp: datetime
    ) -> Dict[str, Any]:
        """Close an existing position."""
        pnl = (price - position['entry_price']) * position['size']
        if position['side'] == 'SHORT':
            pnl = -pnl
        
        return {
            'type': 'close',
            'side': position['side'],
            'entry_price': position['entry_price'],
            'exit_price': price,
            'size': position['size'],
            'pnl': pnl,
            'return_pct': (pnl / (position['entry_price'] * position['size'])) * 100,
            'timestamp': timestamp,
            'holding_period': (timestamp - position['timestamp']).total_seconds() / 3600
        }
    
    def _calculate_unrealized_pnl(self, position: Dict[str, Any], current_price: float) -> float:
        """Calculate unrealized PnL for open position."""
        pnl = (current_price - position['entry_price']) * position['size']
        if position['side'] == 'SHORT':
            pnl = -pnl
        return pnl
    
    def _calculate_metrics(
        self,
        trades: List[Dict[str, Any]],
        equity_curve: List[Dict[str, Any]],
        initial_capital: float,
        final_capital: float
    ) -> Dict[str, Any]:
        """Calculate performance metrics."""
        # Filter closed trades
        closed_trades = [t for t in trades if t.get('type') == 'close']
        
        if not closed_trades:
            return {
                'total_return': 0,
                'win_rate': 0,
                'profit_factor': 0,
                'max_drawdown': 0,
                'sharpe_ratio': 0,
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0
            }
        
        # Calculate returns
        total_return = ((final_capital - initial_capital) / initial_capital) * 100
        
        # Win rate
        winning_trades = [t for t in closed_trades if t['pnl'] > 0]
        losing_trades = [t for t in closed_trades if t['pnl'] <= 0]
        win_rate = (len(winning_trades) / len(closed_trades)) * 100
        
        # Profit factor
        total_wins = sum(t['pnl'] for t in winning_trades) if winning_trades else 0
        total_losses = abs(sum(t['pnl'] for t in losing_trades)) if losing_trades else 0
        profit_factor = total_wins / total_losses if total_losses > 0 else float('inf')
        
        # Max drawdown
        equity_values = [e['equity'] for e in equity_curve]
        max_drawdown = self._calculate_max_drawdown(equity_values)
        
        # Sharpe ratio (assuming 0% risk-free rate)
        returns = np.diff(equity_values) / equity_values[:-1]
        sharpe_ratio = (np.mean(returns) / np.std(returns)) * np.sqrt(252) if np.std(returns) > 0 else 0
        
        # Sortino ratio
        downside_returns = returns[returns < 0]
        sortino_ratio = (np.mean(returns) / np.std(downside_returns)) * np.sqrt(252) if len(downside_returns) > 0 and np.std(downside_returns) > 0 else 0
        
        # Calmar ratio
        calmar_ratio = (total_return / 100) / (max_drawdown / 100) if max_drawdown > 0 else 0
        
        # Average win/loss
        avg_win = total_wins / len(winning_trades) if winning_trades else 0
        avg_loss = total_losses / len(losing_trades) if losing_trades else 0
        
        return {
            'total_return': round(total_return, 2),
            'win_rate': round(win_rate, 2),
            'profit_factor': round(profit_factor, 2),
            'max_drawdown': round(max_drawdown, 2),
            'sharpe_ratio': round(sharpe_ratio, 2),
            'sortino_ratio': round(sortino_ratio, 2),
            'calmar_ratio': round(calmar_ratio, 2),
            'total_trades': len(closed_trades),
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'avg_win': round(avg_win, 2),
            'avg_loss': round(avg_loss, 2)
        }
    
    def _calculate_max_drawdown(self, equity_values: List[float]) -> float:
        """Calculate maximum drawdown."""
        if len(equity_values) < 2:
            return 0
        
        peak = equity_values[0]
        max_drawdown = 0
        
        for value in equity_values:
            if value > peak:
                peak = value
            drawdown = (peak - value) / peak * 100
            if drawdown > max_drawdown:
                max_drawdown = drawdown
        
        return max_drawdown

# Create singleton
backtest_engine = BacktestEngine()
