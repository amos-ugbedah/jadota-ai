"""
AI Strategy Settings Model - Professional Trading Configuration
"""

from sqlalchemy import Column, String, Float, Integer, Boolean, DateTime, Text
from sqlalchemy.sql import func
import uuid
from ..core.database import Base

class AISettings(Base):
    __tablename__ = "ai_settings"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), unique=True, nullable=False, index=True)
    
    # ============================================
    # STRATEGY SETTINGS
    # ============================================
    confidence_threshold = Column(Float, default=70.0)
    strategy_type = Column(String(50), default='balanced')
    
    # 🔥 PER-TRADE AMOUNT (Base amount in USDT)
    trade_amount = Column(Float, default=25.0)
    
    # ============================================
    # RISK MANAGEMENT
    # ============================================
    stop_loss_percent = Column(Float, default=2.0)
    take_profit_percent = Column(Float, default=4.0)
    max_daily_loss = Column(Float, default=5.0)
    max_drawdown = Column(Float, default=15.0)
    max_positions = Column(Integer, default=5)
    
    # ============================================
    # POSITION SIZING
    # ============================================
    position_size_multiplier = Column(Float, default=1.0)
    risk_per_trade = Column(Float, default=2.0)
    
    # ============================================
    # TRADING SYMBOLS
    # ============================================
    symbols = Column(Text, default='BTC/USDT,ETH/USDT,SOL/USDT,BNB/USDT')
    
    # ============================================
    # AUTOMATION
    # ============================================
    auto_trade_enabled = Column(Boolean, default=False)
    max_trades_per_day = Column(Integer, default=10)
    
    # ============================================
    # PERFORMANCE TRACKING
    # ============================================
    total_trades = Column(Integer, default=0)
    winning_trades = Column(Integer, default=0)
    losing_trades = Column(Integer, default=0)
    total_pnl = Column(Float, default=0.0)
    best_trade = Column(Float, default=0.0)
    worst_trade = Column(Float, default=0.0)
    
    # ============================================
    # TIMESTAMPS
    # ============================================
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    
    # ============================================
    # HELPER METHODS
    # ============================================
    
    def get_symbols_list(self):
        return [s.strip() for s in self.symbols.split(',') if s.strip()]
    
    def set_symbols_list(self, symbols_list):
        self.symbols = ','.join(symbols_list)
    
    def get_strategy_label(self):
        labels = {
            'conservative': '🛡️ Conservative',
            'balanced': '⚖️ Balanced',
            'aggressive': '⚡ Aggressive'
        }
        return labels.get(self.strategy_type, 'Balanced')
    
    def get_strategy_description(self):
        descriptions = {
            'conservative': 'High confidence, tight stop-loss, smaller positions',
            'balanced': 'Balanced risk-reward with moderate position sizing',
            'aggressive': 'Lower confidence threshold, wider stops, larger positions'
        }
        return descriptions.get(self.strategy_type, 'Balanced approach')
    
    def get_preset_values(self, strategy_type: str):
        presets = {
            'conservative': {
                'confidence_threshold': 80,
                'stop_loss_percent': 1.5,
                'take_profit_percent': 3.0,
                'position_size_multiplier': 0.7,
                'max_positions': 3,
                'max_daily_loss': 3.0,
                'max_drawdown': 10.0,
                'risk_per_trade': 1.0,
                'trade_amount': 10.0
            },
            'balanced': {
                'confidence_threshold': 70,
                'stop_loss_percent': 2.0,
                'take_profit_percent': 4.0,
                'position_size_multiplier': 1.0,
                'max_positions': 5,
                'max_daily_loss': 5.0,
                'max_drawdown': 15.0,
                'risk_per_trade': 2.0,
                'trade_amount': 25.0
            },
            'aggressive': {
                'confidence_threshold': 60,
                'stop_loss_percent': 3.0,
                'take_profit_percent': 6.0,
                'position_size_multiplier': 1.5,
                'max_positions': 8,
                'max_daily_loss': 8.0,
                'max_drawdown': 25.0,
                'risk_per_trade': 3.0,
                'trade_amount': 50.0
            }
        }
        return presets.get(strategy_type, presets['balanced'])
    
    def get_risk_level(self):
        levels = {
            'conservative': 'Low',
            'balanced': 'Medium',
            'aggressive': 'High'
        }
        return levels.get(self.strategy_type, 'Medium')
    
    def __repr__(self):
        return f"<AISettings user_id={self.user_id} strategy={self.strategy_type} trade_amount=${self.trade_amount}>"