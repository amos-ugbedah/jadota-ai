"""
AI Trading Engine - Intelligent trading decisions using multiple indicators.

Signal generation is delegated to the active strategy
(see app/ai/strategies/). Each strategy has its own scoring logic.
"""

import logging
import asyncio
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import httpx

from ..ai.strategies import get_strategy, list_strategies, DEFAULT_STRATEGY_NAME

logger = logging.getLogger(__name__)


class AITradingService:
    """AI Trading Engine that analyzes market data and generates signals."""

    GRANULARITY_MAP = {
        "1m": "1min",
        "3m": "3min",
        "5m": "5min",
        "15m": "15min",
        "30m": "30min",
        "1h": "1h",
        "4h": "4h",
        "6h": "6h",
        "12h": "12h",
        "1d": "1day",
        "3d": "3day",
        "1w": "1week",
        "1M": "1M",
    }

    def __init__(self):
        self.signals = {}
        self.last_analysis = {}
        self.confidence_threshold = 65
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=10.0,
                headers={"User-Agent": "JADOTA-AI/1.0"},
            )
        return self._client

    def calculate_trade_amount(self, base_amount: float, confidence: float) -> float:
        """🏆 HYBRID: Scale trade amount by AI confidence."""
        if confidence >= 85:
            multiplier = 1.0
        elif confidence >= 75:
            multiplier = 0.8
        elif confidence >= 65:
            multiplier = 0.6
        elif confidence >= 55:
            multiplier = 0.4
        else:
            multiplier = 0.2
        return round(base_amount * multiplier, 2)

    async def analyze_symbol(
        self,
        symbol: str,
        timeframe: str = "1h",
        limit: int = 100,
        strategy: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Analyze a symbol and generate a trading signal.

        Args:
            strategy: name of the active strategy (conservative/balanced/aggressive/scalping/swing).
                      Defaults to balanced.
        """
        strat = get_strategy(strategy)

        try:
            ohlcv = await self._fetch_ohlcv(symbol, timeframe, limit)

            if not ohlcv or len(ohlcv) < 50:
                logger.warning(
                    f"⚠️ {symbol}: Not enough OHLCV data "
                    f"(got {len(ohlcv) if ohlcv else 0} candles, need 50+)"
                )
                return self._fallback_analysis(symbol, strat.NAME)

            df = pd.DataFrame(ohlcv)
            indicators = await self._calculate_indicators(df)
            signal = await self._generate_signal(symbol, df, indicators, strat)

            self.signals[symbol] = signal
            self.last_analysis[symbol] = datetime.utcnow()

            return signal

        except Exception as e:
            logger.error(f"AI analysis error for {symbol} [{strat.NAME}]: {e}")
            return self._fallback_analysis(symbol, strat.NAME)

    async def _fetch_ohlcv(
        self, symbol: str, timeframe: str, limit: int
    ) -> List[Dict]:
        """Fetch OHLCV from Bitget v2, oldest-first."""
        bitget_symbol = symbol.replace("/", "")
        granularity = self.GRANULARITY_MAP.get(timeframe, "1h")

        url = "https://api.bitget.com/api/v2/spot/market/candles"
        params = {"symbol": bitget_symbol, "granularity": granularity, "limit": limit}

        for attempt in range(2):
            try:
                client = await self._get_client()
                response = await client.get(url, params=params)

                if response.status_code != 200:
                    logger.warning(
                        f"Bitget candles HTTP {response.status_code} for "
                        f"{symbol} ({granularity}): {response.text[:150]}"
                    )
                    if attempt == 0:
                        await asyncio.sleep(0.5)
                        continue
                    return []

                data = response.json()
                if data.get("code") != "00000" or not data.get("data"):
                    logger.warning(
                        f"Bitget candles error for {symbol}: "
                        f"code={data.get('code')} msg={data.get('msg')}"
                    )
                    return []

                candles: List[Dict] = []
                for candle in data["data"]:
                    try:
                        candles.append({
                            "timestamp": int(candle[0]),
                            "open": float(candle[1]),
                            "high": float(candle[2]),
                            "low": float(candle[3]),
                            "close": float(candle[4]),
                            "volume": float(candle[5]),
                        })
                    except (IndexError, ValueError, TypeError) as e:
                        logger.debug(f"Skipping malformed candle: {candle} ({e})")

                candles.reverse()
                return candles

            except httpx.HTTPError as e:
                logger.warning(f"HTTP error fetching {symbol} (attempt {attempt+1}): {e}")
                if attempt == 0:
                    await asyncio.sleep(0.5)
                    continue
                return []
            except Exception as e:
                logger.error(f"Failed to fetch OHLCV for {symbol}: {e}")
                return []

        return []

    async def _calculate_indicators(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Compute technical indicators."""
        close = df["close"].values

        sma_7 = self._sma(close, 7)
        sma_25 = self._sma(close, 25)
        sma_99 = self._sma(close, 99)
        ema_12 = self._ema(close, 12)
        ema_26 = self._ema(close, 26)
        rsi = self._rsi(close, 14)
        macd, signal, histogram = self._macd(close, 12, 26, 9)
        upper, middle, lower = self._bollinger_bands(close, 20, 2)

        return {
            "close": float(close[-1]),
            "sma_7": float(sma_7[-1]) if len(sma_7) > 0 else float(close[-1]),
            "sma_25": float(sma_25[-1]) if len(sma_25) > 0 else float(close[-1]),
            "sma_99": float(sma_99[-1]) if len(sma_99) > 0 else float(close[-1]),
            "ema_12": float(ema_12[-1]) if len(ema_12) > 0 else float(close[-1]),
            "ema_26": float(ema_26[-1]) if len(ema_26) > 0 else float(close[-1]),
            "rsi": float(rsi[-1]) if len(rsi) > 0 else 50.0,
            "macd": float(macd[-1]) if len(macd) > 0 else 0.0,
            "macd_signal": float(signal[-1]) if len(signal) > 0 else 0.0,
            "macd_histogram": float(histogram[-1]) if len(histogram) > 0 else 0.0,
            "bb_upper": float(upper[-1]) if len(upper) > 0 else float(close[-1]) * 1.02,
            "bb_middle": float(middle[-1]) if len(middle) > 0 else float(close[-1]),
            "bb_lower": float(lower[-1]) if len(lower) > 0 else float(close[-1]) * 0.98,
        }

    # ============================================
    # Indicator math
    # ============================================
    def _sma(self, data, period: int):
        result = []
        for i in range(len(data)):
            if i < period - 1:
                result.append(float("nan"))
            else:
                result.append(sum(data[i - period + 1: i + 1]) / period)
        return result

    def _ema(self, data, period: int):
        multiplier = 2 / (period + 1)
        result = []
        ema = data[0] if len(data) > 0 else 0
        for i, price in enumerate(data):
            if i == 0:
                result.append(price)
                ema = price
            else:
                ema = (price - ema) * multiplier + ema
                result.append(ema)
        return result

    def _rsi(self, data, period: int = 14):
        if len(data) < period + 1:
            return [50] * len(data)
        gains, losses = [], []
        for i in range(1, len(data)):
            change = data[i] - data[i - 1]
            gains.append(change if change > 0 else 0)
            losses.append(abs(change) if change < 0 else 0)
        result = []
        avg_gain = sum(gains[:period]) / period
        avg_loss = sum(losses[:period]) / period
        for i in range(len(data)):
            if i < period:
                result.append(50)
            else:
                if i > period:
                    gain = gains[i - 1]
                    loss = losses[i - 1]
                    avg_gain = (avg_gain * (period - 1) + gain) / period
                    avg_loss = (avg_loss * (period - 1) + loss) / period
                rs = avg_gain / avg_loss if avg_loss != 0 else 100
                result.append(100 - (100 / (1 + rs)))
        return result

    def _macd(self, data, fast: int, slow: int, signal: int):
        ema_fast = self._ema(data, fast)
        ema_slow = self._ema(data, slow)
        macd_line = [f - s for f, s in zip(ema_fast, ema_slow)]
        signal_line = self._ema(macd_line, signal)
        histogram = [m - s for m, s in zip(macd_line, signal_line)]
        return macd_line, signal_line, histogram

    def _bollinger_bands(self, data, period: int, std_dev: float):
        sma = self._sma(data, period)
        upper, middle, lower = [], [], []
        for i in range(len(data)):
            if i < period - 1:
                upper.append(float("nan"))
                middle.append(float("nan"))
                lower.append(float("nan"))
            else:
                window = data[i - period + 1: i + 1]
                mean = sum(window) / period
                std = (sum((x - mean) ** 2 for x in window) / period) ** 0.5
                upper.append(mean + std_dev * std)
                middle.append(mean)
                lower.append(mean - std_dev * std)
        return upper, middle, lower

    # ============================================
    # Signal generation — delegates to the strategy
    # ============================================
    async def _generate_signal(
        self, symbol: str, df: pd.DataFrame, indicators: Dict, strategy
    ) -> Dict[str, Any]:
        signal, confidence = strategy.generate_signal(indicators)

        sl_pct = strategy.config.get("stop_loss_percent", 2.0) / 100
        tp_pct = strategy.config.get("take_profit_percent", 4.0) / 100
        risk_reward = round(tp_pct / sl_pct, 2) if sl_pct > 0 else 1.0

        reasoning = self._generate_reasoning(signal, indicators, confidence, strategy)

        return {
            "symbol": symbol,
            "signal": signal,
            "confidence": confidence,
            "reasoning": reasoning,
            "risk_reward": risk_reward,
            "strategy": strategy.NAME,
            "strategy_label": strategy.LABEL,
            "indicators": indicators,
            "timestamp": datetime.utcnow().isoformat(),
        }

    def _generate_reasoning(self, signal, indicators, confidence, strategy):
        reasons = []
        if signal == "BUY":
            if indicators["rsi"] < 30:
                reasons.append("RSI oversold")
            if indicators["close"] <= indicators["bb_lower"] * 1.01:
                reasons.append("Price at lower BB")
            if indicators["macd_histogram"] > 0:
                reasons.append("MACD bullish")
            if indicators["close"] > indicators["sma_25"]:
                reasons.append("Above SMA25")
        elif signal == "SELL":
            if indicators["rsi"] > 70:
                reasons.append("RSI overbought")
            if indicators["close"] >= indicators["bb_upper"] * 0.99:
                reasons.append("Price at upper BB")
            if indicators["macd_histogram"] < 0:
                reasons.append("MACD bearish")
            if indicators["close"] < indicators["sma_25"]:
                reasons.append("Below SMA25")
        else:
            return f"[{strategy.LABEL}] Mixed signals - waiting for clearer setup"

        if not reasons:
            return f"[{strategy.LABEL}] Signal triggered by strategy logic"
        return f"[{strategy.LABEL}] " + ". ".join(reasons)

    def _fallback_analysis(self, symbol: str, strategy_name: str = DEFAULT_STRATEGY_NAME):
        return {
            "symbol": symbol,
            "signal": "HOLD",
            "confidence": 0,
            "reasoning": "Insufficient data for analysis",
            "risk_reward": 1.0,
            "strategy": strategy_name,
            "timestamp": datetime.utcnow().isoformat(),
        }

    # ============================================
    # Public helper — list all strategies
    # ============================================
    def get_all_strategies(self) -> List[Dict[str, Any]]:
        return list_strategies()


# Singleton
ai_trading_service = AITradingService()