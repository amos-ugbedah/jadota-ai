"""
Position Monitor Service - Monitors open positions for Stop-Loss and Take-Profit
"""

import asyncio
import logging
from datetime import datetime
from typing import List, Dict, Any

from .telegram_service import telegram_service
from ..core.database import SessionLocal
from ..models.user import User

logger = logging.getLogger(__name__)

class PositionMonitor:
    """Monitors open positions and triggers Stop-Loss/Take-Profit"""
    
    def __init__(self):
        self.is_running = False
        self._task = None
        self.positions = []
        self.market_service = None
        self.trade_history = []
    
    async def start(self, positions_ref, market_service):
        """Start the position monitor"""
        self.positions = positions_ref
        self.market_service = market_service
        self.is_running = True
        self._task = asyncio.create_task(self._monitor_loop())
        logger.info("✅ Position Monitor started")
    
    async def stop(self):
        """Stop the position monitor"""
        self.is_running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        logger.info("Position Monitor stopped")
    
    async def _monitor_loop(self):
        """Main monitoring loop"""
        while self.is_running:
            try:
                await self._check_positions()
            except Exception as e:
                logger.error(f"Position monitor error: {e}")
            await asyncio.sleep(2)
    
    async def _check_positions(self):
        """Check all open positions for SL/TP triggers"""
        if not self.positions:
            return
        
        for pos in self.positions:
            if pos.get('status') != 'OPEN':
                continue
            
            symbol = pos.get('symbol')
            current_price = self.market_service.get_price(symbol)
            
            if current_price == 0:
                continue
            
            pos['currentPrice'] = current_price
            
            if pos['side'] == 'BUY':
                pos['unrealizedPnl'] = (current_price - pos['entryPrice']) * pos['size']
            else:
                pos['unrealizedPnl'] = (pos['entryPrice'] - current_price) * pos['size']
            
            stop_loss = pos.get('stopLoss')
            if stop_loss and current_price <= stop_loss:
                await self._close_position(pos, 'STOP_LOSS')
                continue
            
            take_profit = pos.get('takeProfit')
            if take_profit and current_price >= take_profit:
                await self._close_position(pos, 'TAKE_PROFIT')
                continue
    
    async def _close_position(self, pos: Dict[str, Any], reason: str):
        """Close a position and record result"""
        current_price = pos['currentPrice']
        
        if pos['side'] == 'BUY':
            pos['realizedPnl'] = (current_price - pos['entryPrice']) * pos['size']
        else:
            pos['realizedPnl'] = (pos['entryPrice'] - current_price) * pos['size']
        
        pos['status'] = 'CLOSED'
        pos['closedAt'] = datetime.utcnow().isoformat()
        pos['closeReason'] = reason
        
        trade_record = {
            'id': pos['id'],
            'symbol': pos['symbol'],
            'side': pos['side'],
            'entryPrice': pos['entryPrice'],
            'exitPrice': current_price,
            'size': pos['size'],
            'pnl': pos['realizedPnl'],
            'reason': reason,
            'aiConfidence': pos.get('aiConfidence', 0),
            'aiReasoning': pos.get('aiReasoning', ''),
            'openedAt': pos['openedAt'],
            'closedAt': pos['closedAt'],
            'user_id': pos.get('user_id')
        }
        self.trade_history.append(trade_record)
        
        logger.info(f"📊 Position CLOSED: {pos['symbol']} {pos['side']} | {reason} | P&L: ${pos['realizedPnl']:.2f}")
        
        # 🔥 Send Telegram alerts
        # 1. Admin alert (always sent)
        await telegram_service.send_trade_alert(pos, reason)
        
        # 2. Public group announcement (with user info if available)
        user_info = None
        if pos.get('user_id'):
            try:
                db = SessionLocal()
                user = db.query(User).filter(User.id == pos['user_id']).first()
                if user:
                    user_info = {
                        'full_name': user.full_name or user.username,
                        'username': user.username,
                        'email': user.email
                    }
                db.close()
            except Exception as e:
                logger.error(f"Error fetching user info: {e}")
        
        # Send to public group
        await telegram_service.send_public_trade_alert(pos, reason, user_info)
    
    def get_trade_history(self, limit: int = 50) -> List[Dict]:
        return self.trade_history[-limit:] if self.trade_history else []
    
    def get_performance_stats(self) -> Dict:
        if not self.trade_history:
            return {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0,
                'total_pnl': 0,
                'avg_win': 0,
                'avg_loss': 0,
                'profit_factor': 0,
                'best_trade': 0,
                'worst_trade': 0
            }
        
        wins = [t for t in self.trade_history if t['pnl'] > 0]
        losses = [t for t in self.trade_history if t['pnl'] < 0]
        
        total_trades = len(self.trade_history)
        winning_trades = len(wins)
        losing_trades = len(losses)
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        
        total_pnl = sum(t['pnl'] for t in self.trade_history)
        
        avg_win = sum(t['pnl'] for t in wins) / winning_trades if winning_trades > 0 else 0
        avg_loss = sum(t['pnl'] for t in losses) / losing_trades if losing_trades > 0 else 0
        
        profit_factor = abs(sum(t['pnl'] for t in wins) / sum(t['pnl'] for t in losses)) if losses and sum(t['pnl'] for t in losses) != 0 else 0
        
        best_trade = max([t['pnl'] for t in self.trade_history]) if self.trade_history else 0
        worst_trade = min([t['pnl'] for t in self.trade_history]) if self.trade_history else 0
        
        return {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': round(win_rate, 2),
            'total_pnl': round(total_pnl, 2),
            'avg_win': round(avg_win, 2),
            'avg_loss': round(avg_loss, 2),
            'profit_factor': round(profit_factor, 2),
            'best_trade': round(best_trade, 2),
            'worst_trade': round(worst_trade, 2)
        }

# Singleton
position_monitor = PositionMonitor()