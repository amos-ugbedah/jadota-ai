import pandas as pd
import numpy as np
from typing import Dict, Any, List, Tuple
from datetime import datetime, timedelta
import logging
from sqlalchemy.orm import Session

from .backtest_engine import backtest_engine

logger = logging.getLogger(__name__)

class WalkForwardTester:
    """
    Walk-forward testing to prevent overfitting.
    Splits data into training and testing periods.
    """
    
    def __init__(self):
        self.train_window = 90  # days
        self.test_window = 30   # days
        self.min_trades = 10
    
    async def run_walk_forward(
        self,
        db: Session,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        initial_capital: float,
        risk_level: str = "MODERATE"
    ) -> Dict[str, Any]:
        """
        Run walk-forward backtest.
        """
        results = []
        current_date = start_date
        
        while current_date + timedelta(days=self.train_window + self.test_window) <= end_date:
            # Define training period
            train_start = current_date
            train_end = current_date + timedelta(days=self.train_window)
            
            # Define testing period
            test_start = train_end
            test_end = train_end + timedelta(days=self.test_window)
            
            logger.info(f"Walk-forward iteration: {train_start.date()} -> {test_end.date()}")
            
            # Run backtest on training data to find optimal parameters
            # (For now, use default parameters)
            
            # Run backtest on testing data
            result = await backtest_engine.run_backtest(
                db,
                symbol,
                test_start,
                test_end,
                initial_capital,
                risk_level
            )
            
            if 'error' not in result:
                results.append({
                    'period': {
                        'train_start': train_start,
                        'train_end': train_end,
                        'test_start': test_start,
                        'test_end': test_end
                    },
                    'metrics': result['metrics'],
                    'trades': len(result.get('trades', [])),
                    'final_capital': result.get('final_capital', initial_capital)
                })
                
                # Update capital for next iteration
                initial_capital = result.get('final_capital', initial_capital)
            
            # Move window forward
            current_date = test_end
        
        # Aggregate results
        return self._aggregate_results(results, initial_capital)
    
    def _aggregate_results(self, results: List[Dict], final_capital: float) -> Dict[str, Any]:
        """Aggregate walk-forward results."""
        if not results:
            return {'error': 'No walk-forward results'}
        
        metrics_list = [r['metrics'] for r in results if 'metrics' in r]
        
        if not metrics_list:
            return {'error': 'No metrics available'}
        
        # Calculate average metrics
        avg_metrics = {}
        for key in ['total_return', 'win_rate', 'profit_factor', 'max_drawdown', 'sharpe_ratio']:
            values = [m.get(key, 0) for m in metrics_list if key in m]
            avg_metrics[f'avg_{key}'] = np.mean(values) if values else 0
            avg_metrics[f'std_{key}'] = np.std(values) if values else 0
        
        avg_metrics['total_iterations'] = len(results)
        avg_metrics['final_capital'] = final_capital
        
        return avg_metrics

# Create singleton
walk_forward_tester = WalkForwardTester()
