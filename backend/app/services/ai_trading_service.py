"""
AI Trading Engine - Intelligent trading decisions using multiple indicators
"""

import logging
import asyncio
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import httpx

logger = logging.getLogger(__name__)


class AITradingService:
    """AI Trading Engine that analyzes market data and generates signals"""

    # 🔥 Bitget v2 granularity values — per Bitget API docs and error messages
    # Accepted: 1min, 3min, 5min, 15min, 30min, 1h, 4h, 6h, 12h, 1day, 1week, 1M
    # (Do NOT use 1m, 1H, 1D, 1W — those cause HTTP 400)
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
        """Reuse one HTTP client across calls (faster, fewer connections)."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=10.0,
                headers={"User-Agent": "JADOTA-AI/1.0"},
            )
        return self._client

    def calculate_trade_amount(self, base_amount: float, confidence: float) -> float:
        """
        🏆 HYBRID APPROACH: Scale trade amount by AI confidence

        Args:
            base_amount: User's set per-trade amount (e.g., $50)
            confidence: AI confidence (0-100)

        Returns:
            Final trade amount scaled by confidence
        """
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
        self, symbol: str, timeframe: str = "1h", limit: int = 100
    ) -> Dict[str, Any]:
        """Analyze a symbol and generate trading signal"""
        try:
            ohlcv = await self._fetch_ohlcv(symbol, timeframe, limit)

            if not ohlcv or len(ohlcv) < 50:
                logger.warning(
                    f"⚠️ {symbol}: Not enough OHLCV data "
                    f"(got {len(ohlcv) if ohlcv else 0} candles, need 50+)"
                )
                return self._fallback_analysis(symbol)

            df = pd.DataFrame(ohlcv)
            indicators = await self._calculate_indicators(df)
            signal = await self._generate_signal(symbol, df, indicators)

            self.signals[symbol] = signal
            self.last_analysis[symbol] = datetime.utcnow()

            return signal

        except Exception as e:
            logger.error(f"AI analysis error for {symbol}: {e}")
            return self._fallback_analysis(symbol)

    async def _fetch_ohlcv(
        self, symbol: str, timeframe: str, limit: int
    ) -> List[Dict]:
        """
        Fetch OHLCV data from Bitget v2.

        Endpoint: GET /api/v2/spot/market/candles
        Response: {"code":"00000","data":[[ts,o,h,l,c,vol,quoteVol], ...]}

        NOTE: Bitget returns candles newest-first, so we reverse to get
        oldest-first, which is what indicators expect.
        """
        bitget_symbol = symbol.replace("/", "")
        granularity = self.GRANULARITY_MAP.get(timeframe, "1h")

        url = "https://api.bitget.com/api/v2/spot/market/candles"
        params = {
            "symbol": bitget_symbol,
            "granularity": granularity,
            "limit": limit,
        }

        # 🔥 Retry once on transient failure
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

                # 🔥 Bitget returns newest-first; indicators expect oldest-first
                candles.reverse()

                logger.debug(
                    f"✅ Fetched {len(candles)} candles for {symbol} ({granularity})"
                )
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
        """Calculate technical indicators"""
        close = df["close"].values
        high = df["high"].values
        low = df["low"].values

        sma_7 = self._sma(close, 7)
        sma_25 = self._sma(close, 25)
        sma_99 = self._sma(close, 99)
        ema_12 = self._ema(close, 12)
        ema_26 = self._ema(close, 26)
        rsi = self._rsi(close, 14)
        macd, signal, histogram = self._macd(close, 12, 26, 9)
        upper, middle, lower = self._bollinger_bands(close, 20, 2)

        return {
            "close": close[-1],
            "sma_7": sma_7[-1] if len(sma_7) > 0 else close[-1],
            "sma_25": sma_25[-1] if len(sma_25) > 0 else close[-1],
            "sma_99": sma_99[-1] if len(sma_99) > 0 else close[-1],
            "ema_12": ema_12[-1] if len(ema_12) > 0 else close[-1],
            "ema_26": ema_26[-1] if len(ema_26) > 0 else close[-1],
            "rsi": rsi[-1] if len(rsi) > 0 else 50,
            "macd": macd[-1] if len(macd) > 0 else 0,
            "macd_signal": signal[-1] if len(signal) > 0 else 0,
            "macd_histogram": histogram[-1] if len(histogram) > 0 else 0,
            "bb_upper": upper[-1] if len(upper) > 0 else close[-1] * 1.02,
            "bb_middle": middle[-1] if len(middle) > 0 else close[-1],
            "bb_lower": lower[-1] if len(lower) > 0 else close[-1] * 0.98,
        }

    def _sma(self, data: List[float], period: int) -> List[float]:
        result = []
        for i in range(len(data)):
            if i < period - 1:
                result.append(float("nan"))
            else:
                result.append(sum(data[i - period + 1 : i + 1]) / period)
        return result

    def _ema(self, data: List[float], period: int) -> List[float]:
        multiplier = 2 / (period + 1)
        result = []
        ema = data[0] if data else 0
        for i, price in enumerate(data):
            if i == 0:
                result.append(price)
                ema = price
            else:
                ema = (price - ema) * multiplier + ema
                result.append(ema)
        return result

    def _rsi(self, data: List[float], period: int = 14) -> List[float]:
        if len(data) < period + 1:
            return [50] * len(data)
        gains = []
        losses = []
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
                rsi = 100 - (100 / (1 + rs))
                result.append(rsi)
        return result

    def _macd(
        self, data: List[float], fast: int, slow: int, signal: int
    ) -> tuple:
        ema_fast = self._ema(data, fast)
        ema_slow = self._ema(data, slow)
        macd_line = [f - s for f, s in zip(ema_fast, ema_slow)]
        signal_line = self._ema(macd_line, signal)
        histogram = [m - s for m, s in zip(macd_line, signal_line)]
        return macd_line, signal_line, histogram

    def _bollinger_bands(
        self, data: List[float], period: int, std_dev: float
    ) -> tuple:
        sma = self._sma(data, period)
        upper = []
        middle = []
        lower = []
        for i in range(len(data)):
            if i < period - 1:
                upper.append(float("nan"))
                middle.append(float("nan"))
                lower.append(float("nan"))
            else:
                window = data[i - period + 1 : i + 1]
                mean = sum(window) / period
                std = (sum((x - mean) ** 2 for x in window) / period) ** 0.5
                upper.append(mean + std_dev * std)
                middle.append(mean)
                lower.append(mean - std_dev * std)
        return upper, middle, lower

    async def _generate_signal(
        self, symbol: str, df: pd.DataFrame, indicators: Dict
    ) -> Dict[str, Any]:
        close = indicators["close"]
        trend_bullish = close > indicators["sma_7"] > indicators["sma_25"]
        trend_bearish = close < indicators["sma_7"] < indicators["sma_25"]
        rsi_bullish = indicators["rsi"] < 30
        rsi_bearish = indicators["rsi"] > 70
        macd_bullish = (
            indicators["macd_histogram"] > 0
            and indicators["macd"] > indicators["macd_signal"]
        )
        macd_bearish = (
            indicators["macd_histogram"] < 0
            and indicators["macd"] < indicators["macd_signal"]
        )
        bb_bullish = close <= indicators["bb_lower"] * 1.01
        bb_bearish = close >= indicators["bb_upper"] * 0.99

        bullish_score = 0
        bearish_score = 0

        if trend_bullish:
            bullish_score += 20
        elif trend_bearish:
            bearish_score += 20
        if rsi_bullish:
            bullish_score += 15
        elif rsi_bearish:
            bearish_score += 15
        if macd_bullish:
            bullish_score += 25
        elif macd_bearish:
            bearish_score += 25
        if bb_bullish:
            bullish_score += 10
        elif bb_bearish:
            bearish_score += 10

        total = bullish_score + bearish_score
        if total == 0:
            signal = "HOLD"
            confidence = 0
        else:
            if bullish_score > bearish_score:
                signal = "BUY"
                confidence = min(95, int((bullish_score / total) * 80 + 20))
            elif bearish_score > bullish_score:
                signal = "SELL"
                confidence = min(95, int((bearish_score / total) * 80 + 20))
            else:
                signal = "HOLD"
                confidence = 50

        risk_reward = await self._calculate_risk_reward(indicators, signal)
        reasoning = self._generate_reasoning(signal, indicators, confidence)

        return {
            "symbol": symbol,
            "signal": signal,
            "confidence": confidence,
            "reasoning": reasoning,
            "risk_reward": risk_reward,
            "indicators": indicators,
            "timestamp": datetime.utcnow().isoformat(),
        }

    async def _calculate_risk_reward(
        self, indicators: Dict, signal: str
    ) -> float:
        close = indicators["close"]
        atr = (indicators["bb_upper"] - indicators["bb_lower"]) / 4
        if signal == "BUY":
            stop_loss = close - atr * 1.5
            take_profit = close + atr * 3
        elif signal == "SELL":
            stop_loss = close + atr * 1.5
            take_profit = close - atr * 3
        else:
            return 1.0
        risk = abs(close - stop_loss)
        reward = abs(take_profit - close)
        return round(reward / risk, 2) if risk > 0 else 1.0

    def _generate_reasoning(
        self, signal: str, indicators: Dict, confidence: int
    ) -> str:
        reasons = []
        if signal == "BUY":
            if indicators["rsi"] < 30:
                reasons.append("RSI indicates oversold condition")
            if indicators["close"] <= indicators["bb_lower"] * 1.01:
                reasons.append("Price near lower Bollinger Band")
            if indicators["macd_histogram"] > 0:
                reasons.append("MACD turning bullish")
        elif signal == "SELL":
            if indicators["rsi"] > 70:
                reasons.append("RSI indicates overbought condition")
            if indicators["close"] >= indicators["bb_upper"] * 0.99:
                reasons.append("Price near upper Bollinger Band")
            if indicators["macd_histogram"] < 0:
                reasons.append("MACD turning bearish")
        else:
            return "Mixed signals - waiting for clearer direction"

        if not reasons:
            return "No clear signals - holding position"

        prefix = "Bullish" if signal == "BUY" else "Bearish"
        return f"{prefix} signals: " + ". ".join(reasons)

    def _fallback_analysis(self, symbol: str) -> Dict[str, Any]:
        return {
            "symbol": symbol,
            "signal": "HOLD",
            "confidence": 0,
            "reasoning": "Insufficient data for analysis",
            "risk_reward": 1.0,
            "timestamp": datetime.utcnow().isoformat(),
        }


# Singleton
ai_trading_service = AITradingService()