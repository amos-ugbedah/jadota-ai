import asyncio
import json
from datetime import datetime
from decimal import Decimal
from sqlalchemy.orm import Session
import logging

from ..core.database import SessionLocal
from ..models.market_data import CurrentPrice
from .price_simulator import price_simulator
from .websocket_manager import ws_manager

logger = logging.getLogger(__name__)

class PriceUpdater:
    """Background service that updates prices and broadcasts to WebSocket clients."""
    
    def __init__(self):
        self._running = False
        self._task = None
        self._update_interval = 1  # Update every second
    
    async def start(self):
        """Start the price updater."""
        self._running = True
        self._task = asyncio.create_task(self._run())
        logger.info("Price updater started")
    
    async def _run(self):
        """Main update loop."""
        while self._running:
            try:
                await self._update_prices()
                await asyncio.sleep(self._update_interval)
            except Exception as e:
                logger.error(f"Price updater error: {e}")
                await asyncio.sleep(5)
    
    async def _update_prices(self):
        """Update prices in database and broadcast to clients."""
        # Get simulated prices
        prices = price_simulator.get_all_prices()
        
        # Update database
        db = SessionLocal()
        try:
            for symbol, price in prices.items():
                # Update or create price record
                current = db.query(CurrentPrice).filter(
                    CurrentPrice.symbol == symbol
                ).first()
                
                if current:
                    current.price = price
                    current.updated_at = datetime.utcnow()
                else:
                    current = CurrentPrice(
                        symbol=symbol,
                        price=price
                    )
                    db.add(current)
            
            db.commit()
        except Exception as e:
            logger.error(f"Database update error: {e}")
            db.rollback()
        finally:
            db.close()
        
        # Broadcast to WebSocket clients
        for symbol, price in prices.items():
            message = {
                'type': 'price_update',
                'symbol': symbol,
                'price': float(price),
                'timestamp': datetime.utcnow().isoformat()
            }
            await ws_manager.broadcast(message)
    
    def stop(self):
        """Stop the price updater."""
        self._running = False
        if self._task:
            self._task.cancel()
        logger.info("Price updater stopped")

# Create singleton
price_updater = PriceUpdater()
