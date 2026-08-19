from sqlalchemy import Column, String, Boolean, DateTime, Integer, Float, DECIMAL, ForeignKey, Text, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
from ..core.database import Base

class BacktestRun(Base):
    __tablename__ = "backtest_runs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    
    # Configuration
    strategy_name = Column(String(100), nullable=False)
    symbols = Column(JSON, nullable=False)  # List of symbols
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    initial_capital = Column(DECIMAL(15, 2), nullable=False)
    risk_level = Column(String(20), nullable=False)
    parameters = Column(JSON, nullable=True)
    
    # Results
    final_capital = Column(DECIMAL(15, 2))
    total_return = Column(DECIMAL(10, 2))
    annualized_return = Column(DECIMAL(10, 2))
    win_rate = Column(DECIMAL(5, 2))
    profit_factor = Column(DECIMAL(10, 2))
    max_drawdown = Column(DECIMAL(10, 2))
    sharpe_ratio = Column(DECIMAL(10, 2))
    sortino_ratio = Column(DECIMAL(10, 2))
    calmar_ratio = Column(DECIMAL(10, 2))
    
    # Trade statistics
    total_trades = Column(Integer)
    winning_trades = Column(Integer)
    losing_trades = Column(Integer)
    avg_win = Column(DECIMAL(15, 2))
    avg_loss = Column(DECIMAL(15, 2))
    
    # Fees and slippage
    fees = Column(DECIMAL(15, 2))
    estimated_slippage = Column(DECIMAL(15, 2))
    
    # Walk-forward results
    walk_forward_results = Column(JSON, nullable=True)
    
    # Status
    status = Column(String(20), default="PENDING")  # PENDING, RUNNING, COMPLETED, FAILED
    
    # Timestamps
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    
    # Relationships
    user = relationship("User")
