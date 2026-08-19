import ccxt
import asyncio
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_
from typing import List, Optional, Dict, Any
from ..models.market_data import OHLCV, CurrentPrice
from ..schemas.market import PriceHistoryRequest

class MarketService:
    # Supported symbols
    SUPPORTED_SYMBOLS = [
        "BTC/USDT", "ETH/USDT", "SOL/USDT", 
        "BNB/USDT", "XRP/USDT", "DOGE/USDT", 
        "ADA/USDT"
    ]
    
    def __init__(self):
        # Initialize exchange
        self.exchange = ccxt.bitget({
            'enableRateLimit': True,
            'options': {
                'defaultType': 'spot'
            }
        })
        self._running = False
        self._websocket_url = "wss://ws.bitget.com/v1/stream"
    
    def get_symbol(self, symbol: str) -> str:
        """Convert symbol to exchange format."""
        # If symbol already has '/', return as is
        if '/' in symbol:
            return symbol
        # Otherwise, add '/USDT'
        return f"{symbol}/USDT"
    
    def get_symbol_from_exchange(self, exchange_symbol: str) -> str:
        """Convert exchange symbol to internal format."""
        return exchange_symbol.replace('/', '')
    
    async def fetch_ohlcv(
        self, 
        symbol: str, 
        interval: str = '1h', 
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Fetch OHLCV data from exchange."""
        try:
            exchange_symbol = self.get_symbol(symbol)
            ohlcv = await asyncio.to_thread(
                self.exchange.fetch_ohlcv,
                exchange_symbol,
                interval,
                limit=limit
            )
            
            return [{
                'timestamp': datetime.fromtimestamp(candle[0] / 1000),
                'open': Decimal(str(candle[1])),
                'high': Decimal(str(candle[2])),
                'low': Decimal(str(candle[3])),
                'close': Decimal(str(candle[4])),
                'volume': Decimal(str(candle[5]))
            } for candle in ohlcv]
        except Exception as e:
            print(f"Error fetching OHLCV for {symbol}: {e}")
            return []
    
    async def get_current_price(self, symbol: str) -> Optional[Decimal]:
        """Get current price from exchange."""
        try:
            exchange_symbol = self.get_symbol(symbol)
            ticker = await asyncio.to_thread(
                self.exchange.fetch_ticker,
                exchange_symbol
            )
            return Decimal(str(ticker['last']))
        except Exception as e:
            print(f"Error fetching price for {symbol}: {e}")
            return None
    
    async def get_order_book(self, symbol: str, limit: int = 10):
        """Get order book for a symbol."""
        try:
            exchange_symbol = self.get_symbol(symbol)
            order_book = await asyncio.to_thread(
                self.exchange.fetch_order_book,
                exchange_symbol,
                limit
            )
            return order_book
        except Exception as e:
            print(f"Error fetching order book for {symbol}: {e}")
            return None
    
    async def fetch_and_store_ohlcv(
        self, 
        db: Session, 
        symbol: str, 
        interval: str = '1h',
        limit: int = 100
    ) -> int:
        """Fetch OHLCV data and store in database."""
        data = await self.fetch_ohlcv(symbol, interval, limit)
        count = 0
        
        for candle in data:
            # Check if data already exists
            existing = db.query(OHLCV).filter(
                OHLCV.symbol == symbol,
                OHLCV.interval == interval,
                OHLCV.timestamp == candle['timestamp']
            ).first()
            
            if not existing:
                ohlcv = OHLCV(
                    symbol=symbol,
                    exchange="BITGET",
                    interval=interval,
                    timestamp=candle['timestamp'],
                    open=candle['open'],
                    high=candle['high'],
                    low=candle['low'],
                    close=candle['close'],
                    volume=candle['volume']
                )
                db.add(ohlcv)
                count += 1
        
        db.commit()
        return count
    
    async def update_current_price(self, db: Session, symbol: str) -> bool:
        """Update current price in database."""
        price = await self.get_current_price(symbol)
        if price is None:
            return False
        
        # Get or create current price record
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
        return True
    
    async def update_all_prices(self, db: Session) -> dict:
        """Update current prices for all supported symbols."""
        results = {}
        for symbol in self.SUPPORTED_SYMBOLS:
            internal_symbol = self.get_symbol_from_exchange(symbol)
            success = await self.update_current_price(db, internal_symbol)
            results[internal_symbol] = success
        return results
    
    def get_historical_ohlcv(
        self, 
        db: Session, 
        request: PriceHistoryRequest
    ) -> List[OHLCV]:
        """Get historical OHLCV data from database."""
        query = db.query(OHLCV).filter(
            OHLCV.symbol == request.symbol,
            OHLCV.interval == request.interval
        )
        
        if request.start_time:
            query = query.filter(OHLCV.timestamp >= request.start_time)
        if request.end_time:
            query = query.filter(OHLCV.timestamp <= request.end_time)
        
        return query.order_by(OHLCV.timestamp.desc()).limit(request.limit).all()
    
    def get_latest_price(self, db: Session, symbol: str) -> Optional[CurrentPrice]:
        """Get latest price from database."""
        return db.query(CurrentPrice).filter(
            CurrentPrice.symbol == symbol
        ).first()

# Singleton instance
market_service = MarketService()
