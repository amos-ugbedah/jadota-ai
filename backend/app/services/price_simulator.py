import asyncio
import random
from decimal import Decimal
from datetime import datetime
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class PriceSimulator:
    """Simulates price data for development when WebSocket is unavailable."""
    
    def __init__(self):
        self.prices: Dict[str, Decimal] = {}
        self.base_prices = {
            "BTCUSDT": Decimal("50000"),
            "ETHUSDT": Decimal("3000"),
            "SOLUSDT": Decimal("150"),
            "BNBUSDT": Decimal("500"),
            "XRPUSDT": Decimal("0.50"),
            "DOGEUSDT": Decimal("0.08"),
            "ADAUSDT": Decimal("0.35")
        }
        self.volatilities = {
            "BTCUSDT": 0.002,
            "ETHUSDT": 0.003,
            "SOLUSDT": 0.005,
            "BNBUSDT": 0.003,
            "XRPUSDT": 0.004,
            "DOGEUSDT": 0.006,
            "ADAUSDT": 0.005
        }
        self._running = False
        self._task = None
        
        # Initialize prices
        for symbol, price in self.base_prices.items():
            self.prices[symbol] = price
    
    async def start(self):
        """Start the price simulator."""
        self._running = True
        self._task = asyncio.create_task(self._simulate())
        logger.info("Price simulator started")
    
    async def _simulate(self):
        """Simulate price updates."""
        while self._running:
            for symbol in self.prices:
                # Random walk with mean reversion
                volatility = self.volatilities.get(symbol, 0.002)
                change = random.gauss(0, volatility)
                current_price = self.prices[symbol]
                new_price = current_price * (1 + change)
                
                # Keep price within reasonable range (80% - 120% of base)
                base = self.base_prices[symbol]
                if new_price < base * Decimal("0.8"):
                    new_price = current_price * Decimal("1.01")
                elif new_price > base * Decimal("1.2"):
                    new_price = current_price * Decimal("0.99")
                
                self.prices[symbol] = new_price
            
            await asyncio.sleep(1)  # Update every second
    
    def get_price(self, symbol: str) -> Optional[Decimal]:
        """Get current simulated price."""
        return self.prices.get(symbol)
    
    def get_all_prices(self) -> Dict[str, Decimal]:
        """Get all simulated prices."""
        return self.prices.copy()
    
    def stop(self):
        """Stop the price simulator."""
        self._running = False
        if self._task:
            self._task.cancel()
        logger.info("Price simulator stopped")

# Create singleton
price_simulator = PriceSimulator()
