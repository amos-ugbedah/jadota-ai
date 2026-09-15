"""
Market Data Service - Fetches real-time prices from Bitget
"""

import asyncio
import json
import logging
import httpx
import random
from typing import Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class MarketDataService:
    def __init__(self):
        self.prices: Dict[str, float] = {}
        self.last_update: Dict[str, datetime] = {}
        self.is_running = False
        self._task: Optional[asyncio.Task] = None

        # 🔥 Supported symbols in Bitget format (BTCUSDT etc.)
        self.symbols = [
            "BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT",
            "XRPUSDT", "DOGEUSDT", "ADAUSDT"
        ]

        # 🔥 Fallback prices (only used if the live API fails)
        self.fallback_prices = {
            "BTC/USDT": 77000.00,
            "ETH/USDT": 2700.00,
            "SOL/USDT": 130.00,
            "BNB/USDT": 600.00,
            "XRP/USDT": 0.52,
            "DOGE/USDT": 0.16,
            "ADA/USDT": 0.42,
        }

    async def start(self):
        """Start fetching market data"""
        if self.is_running:
            return

        self.is_running = True
        logger.info("🔄 Starting market data service...")

        # 🔥 Fetch prices immediately on startup
        await self._fetch_prices()

        # Start background loop
        self._task = asyncio.create_task(self._fetch_loop())
        logger.info("✅ Market Data Service started")

    async def stop(self):
        self.is_running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        logger.info("Market Data Service stopped")

    async def _fetch_loop(self):
        """Main loop to fetch prices"""
        while self.is_running:
            try:
                await self._fetch_prices()
            except Exception as e:
                logger.error(f"Error fetching prices: {e}")

            await asyncio.sleep(5)

    async def _fetch_prices(self):
        """
        Fetch all prices from Bitget in ONE call.

        Bitget v2 endpoint: GET /api/v2/spot/market/tickers
        Response shape:
            {
              "code": "00000",
              "msg": "success",
              "data": [
                {"symbol": "BTCUSDT", "lastPr": "77215", ...},
                {"symbol": "ETHUSDT", "lastPr": "2700", ...},
                ...
              ]
            }
        """
        success_count = 0

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # 🔥 PLURAL endpoint — returns ALL tickers at once
                response = await client.get(
                    "https://api.bitget.com/api/v2/spot/market/tickers"
                )

                if response.status_code != 200:
                    logger.warning(
                        f"Bitget tickers returned HTTP {response.status_code}: "
                        f"{response.text[:200]}"
                    )
                else:
                    data = response.json()

                    if data.get("code") == "00000" and data.get("data"):
                        # Build a lookup map: {"BTCUSDT": {...}, "ETHUSDT": {...}}
                        tickers_by_symbol = {
                            item["symbol"]: item
                            for item in data["data"]
                            if "symbol" in item
                        }

                        for symbol in self.symbols:
                            ticker = tickers_by_symbol.get(symbol)
                            formatted_symbol = symbol.replace("USDT", "/USDT")

                            if ticker:
                                # 🔥 Correct field is "lastPr", not "last"
                                try:
                                    price = float(ticker.get("lastPr", 0))
                                except (ValueError, TypeError):
                                    price = 0.0

                                if price > 0:
                                    self.prices[formatted_symbol] = price
                                    self.last_update[formatted_symbol] = datetime.utcnow()
                                    success_count += 1
                                else:
                                    self._apply_fallback(formatted_symbol)
                            else:
                                self._apply_fallback(formatted_symbol)
                    else:
                        logger.warning(f"Bitget error payload: {data}")
                        for symbol in self.symbols:
                            self._apply_fallback(symbol.replace("USDT", "/USDT"))

        except httpx.HTTPError as e:
            logger.error(f"HTTP error fetching Bitget prices: {e}")
            for symbol in self.symbols:
                self._apply_fallback(symbol.replace("USDT", "/USDT"))
        except Exception as e:
            logger.error(f"Unexpected error fetching Bitget prices: {e}")
            for symbol in self.symbols:
                self._apply_fallback(symbol.replace("USDT", "/USDT"))

        logger.info(
            f"📊 Fetched {success_count} prices "
            f"(using fallback for {len(self.symbols) - success_count})"
        )

    def _apply_fallback(self, formatted_symbol: str):
        """Use the fallback price for a symbol (if available)."""
        if formatted_symbol in self.fallback_prices:
            self.prices[formatted_symbol] = self.fallback_prices[formatted_symbol]
            self.last_update[formatted_symbol] = datetime.utcnow()

    def get_price(self, symbol: str) -> float:
        """Get current price for a symbol"""
        if "/" not in symbol:
            symbol = symbol.replace("USDT", "/USDT")
        return self.prices.get(symbol, 0.0)

    def get_all_prices(self) -> Dict[str, float]:
        return self.prices.copy()

    def get_market_prices(self) -> list:
        """Get formatted market prices for API response"""
        result = []
        now = datetime.utcnow().isoformat()

        # 🔥 If no prices, use fallback prices
        if not self.prices:
            self.prices = self.fallback_prices.copy()
            logger.info("📊 Using fallback prices")

        for symbol, price in self.prices.items():
            # Simulate 24h change (replace with real data if you add it later)
            change_24h = round((random.random() - 0.5) * 4, 2)

            result.append({
                "symbol": symbol,
                "price": round(price, 2),
                "change24h": change_24h,
                "volume24h": round(price * random.randint(50, 500), 0),
                "high24h": round(price * 1.03, 2),
                "low24h": round(price * 0.97, 2),
                "timestamp": now
            })

        return result


# Singleton
market_data_service = MarketDataService()