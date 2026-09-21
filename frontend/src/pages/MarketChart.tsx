import React, { useState, useMemo } from 'react';
import {
  Activity,
  RefreshCw,
  TrendingUp,
  TrendingDown,
  Zap,
  Brain,
  Sparkles,
} from 'lucide-react';
import { useOHLCV } from '@/hooks/useOHLCV';
import { useAISignals } from '@/hooks/useAISignals';
import CandlestickChart, {
  type TradeMarker,
} from '@/components/Charts/CandlestickChart';
import { RSIPanel, MACDPanel } from '@/components/Charts/TechnicalIndicators';
import ChartToolbar, {
  type ChartOverlayState,
} from '@/components/Charts/ChartToolbar';

const MarketChart: React.FC = () => {
  const [symbol, setSymbol] = useState('BTC/USDT');
  const [interval, setIntervalValue] = useState('1h');
  const [overlays, setOverlays] = useState<ChartOverlayState>({
    sma20: false,
    sma50: false,
    ema12: false,
    ema26: false,
    bollingerBands: false,
  });
  const [showRSI, setShowRSI] = useState(false);
  const [showMACD, setShowMACD] = useState(false);
  const [showAISignals, setShowAISignals] = useState(true);

  const { candles, loading, error, lastUpdate, refresh } = useOHLCV({
    symbol,
    interval,
    limit: 300,
    refreshInterval: 15000,
  });

  const {
    signals,
    loading: signalsLoading,
    lastUpdate: signalsUpdate,
    refresh: refreshSignals,
  } = useAISignals({
    refreshInterval: 60000,
    enabled: showAISignals,
  });

  const toggleOverlay = (key: keyof ChartOverlayState) =>
    setOverlays((prev) => ({ ...prev, [key]: !prev[key] }));

  const handleRefresh = async () => {
    await Promise.all([refresh(), showAISignals ? refreshSignals() : Promise.resolve()]);
  };

  // Header stats from candles
  const stats = useMemo(() => {
    if (candles.length === 0) return null;
    const last = candles[candles.length - 1];
    const prev = candles[candles.length - 2] ?? last;
    const change = last.close - prev.close;
    const changePct = prev.close !== 0 ? (change / prev.close) * 100 : 0;
    const window = candles.slice(-24);
    const high24h = Math.max(...window.map((c) => c.high));
    const low24h = Math.min(...window.map((c) => c.low));
    return { price: last.close, change, changePct, high24h, low24h };
  }, [candles]);

  // Current signal for the selected symbol
  const currentSignal = signals[symbol];

  // 🔥 Build chart markers from the current AI signal
  const markers: TradeMarker[] = useMemo(() => {
    if (!showAISignals || !currentSignal) return [];
    if (currentSignal.signal === 'HOLD') return [];
    if (candles.length === 0) return [];

    const lastCandle = candles[candles.length - 1];
    const isBuy = currentSignal.signal === 'BUY';

    return [
      {
        time: lastCandle.time,
        position: isBuy ? 'belowBar' : 'aboveBar',
        color: isBuy ? '#10b981' : '#ef4444',
        shape: isBuy ? 'arrowUp' : 'arrowDown',
        text: `${currentSignal.signal} ${currentSignal.confidence}%`,
      },
    ];
  }, [candles, currentSignal, showAISignals]);

  const positive = (stats?.changePct ?? 0) >= 0;

  return (
    <div className="p-6 mx-auto space-y-6 max-w-7xl">
      {/* Header */}
      <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <h1 className="flex items-center gap-3 text-3xl font-bold text-white">
            <Activity className="w-8 h-8 text-[#6366f1]" />
            Market Chart
          </h1>
          <p className="mt-1 text-gray-400">
            Live candlestick charts with technical indicators
          </p>
        </div>

        <button
          onClick={handleRefresh}
          disabled={loading || signalsLoading}
          className="flex items-center gap-2 px-4 py-2 bg-[#1a1a2e] border border-[#2a2a4a] rounded-lg text-gray-300 hover:text-white hover:border-[#3a3a5a] transition disabled:opacity-50 self-start"
        >
          <RefreshCw
            className={`w-4 h-4 ${loading || signalsLoading ? 'animate-spin' : ''}`}
          />
          Refresh
        </button>
      </div>

      {/* Live price bar */}
      {stats && (
        <div className="bg-[#1a1a2e] border border-[#2a2a4a] rounded-xl p-5">
          <div className="flex flex-wrap items-center gap-x-8 gap-y-3">
            <div>
              <div className="text-xs tracking-wider text-gray-500 uppercase">
                {symbol}
              </div>
              <div className="mt-1 text-3xl font-bold text-white">
                $
                {stats.price.toLocaleString(undefined, {
                  maximumFractionDigits: 2,
                })}
              </div>
            </div>

            <div
              className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-semibold ${
                positive
                  ? 'bg-green-500/10 text-green-400'
                  : 'bg-red-500/10 text-red-400'
              }`}
            >
              {positive ? (
                <TrendingUp className="w-4 h-4" />
              ) : (
                <TrendingDown className="w-4 h-4" />
              )}
              {positive ? '+' : ''}
              {stats.change.toFixed(2)} ({positive ? '+' : ''}
              {stats.changePct.toFixed(2)}%)
            </div>

            {/* 🔥 AI Signal badge */}
            {showAISignals && currentSignal && currentSignal.signal !== 'HOLD' && (
              <div
                className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-semibold border ${
                  currentSignal.signal === 'BUY'
                    ? 'bg-green-500/10 text-green-400 border-green-500/30'
                    : 'bg-red-500/10 text-red-400 border-red-500/30'
                }`}
                title={currentSignal.reasoning}
              >
                <Brain className="w-4 h-4" />
                AI: {currentSignal.signal} ({currentSignal.confidence}%)
              </div>
            )}

            {showAISignals && currentSignal && currentSignal.signal === 'HOLD' && (
              <div className="flex items-center gap-2 px-3 py-2 text-sm font-semibold text-gray-400 border rounded-lg bg-gray-500/10 border-gray-500/30">
                <Brain className="w-4 h-4" />
                AI: HOLD
              </div>
            )}

            <div className="grid grid-cols-2 ml-auto text-sm gap-x-8 gap-y-1">
              <div className="text-gray-500">24h High</div>
              <div className="font-medium text-right text-white">
                $
                {stats.high24h.toLocaleString(undefined, {
                  maximumFractionDigits: 2,
                })}
              </div>
              <div className="text-gray-500">24h Low</div>
              <div className="font-medium text-right text-white">
                $
                {stats.low24h.toLocaleString(undefined, {
                  maximumFractionDigits: 2,
                })}
              </div>
            </div>

            {lastUpdate && (
              <div className="w-full text-xs text-gray-500 lg:w-auto">
                Updated {lastUpdate.toLocaleTimeString()}
                {signalsUpdate && showAISignals && (
                  <span className="ml-2 text-gray-600">
                    · AI: {signalsUpdate.toLocaleTimeString()}
                  </span>
                )}
              </div>
            )}
          </div>

          {/* AI reasoning strip */}
          {showAISignals && currentSignal && currentSignal.signal !== 'HOLD' && (
            <div className="mt-4 pt-4 border-t border-[#2a2a4a] flex items-start gap-2">
              <Sparkles className="w-4 h-4 text-[#6366f1] flex-shrink-0 mt-0.5" />
              <div className="text-xs text-gray-400">
                <span className="font-medium text-white">AI reasoning: </span>
                {currentSignal.reasoning || 'No specific reasoning provided'}
                {currentSignal.risk_reward > 0 && (
                  <span className="ml-2 text-gray-500">
                    · R:R {currentSignal.risk_reward.toFixed(2)}
                  </span>
                )}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Toolbar */}
      <ChartToolbar
        symbol={symbol}
        interval={interval}
        onSymbolChange={setSymbol}
        onIntervalChange={setIntervalValue}
        overlays={overlays}
        onToggleOverlay={toggleOverlay}
        showRSI={showRSI}
        showMACD={showMACD}
        onToggleRSI={() => setShowRSI((v) => !v)}
        onToggleMACD={() => setShowMACD((v) => !v)}
        showAISignals={showAISignals}
        onToggleAISignals={() => setShowAISignals((v) => !v)}
      />

      {/* Error */}
      {error && (
        <div className="p-4 text-sm text-red-400 border bg-red-500/10 border-red-500/30 rounded-xl">
          {error}
        </div>
      )}

      {/* Main chart */}
      <CandlestickChart
        candles={candles}
        overlays={overlays}
        markers={markers}
        height={520}
        loading={loading}
      />

      {/* Subcharts */}
      {(showRSI || showMACD) && (
        <div className="space-y-4">
          {showRSI && <RSIPanel candles={candles} height={140} />}
          {showMACD && <MACDPanel candles={candles} height={160} />}
        </div>
      )}

      {/* Empty fallback */}
      {!loading && !error && candles.length === 0 && (
        <div className="bg-[#1a1a2e] border border-[#2a2a4a] rounded-xl p-12 text-center">
          <Zap className="w-12 h-12 text-[#6366f1] mx-auto mb-4 opacity-50" />
          <p className="text-gray-400">
            No chart data available for {symbol} at {interval}
          </p>
          <button
            onClick={handleRefresh}
            className="mt-4 text-[#6366f1] hover:underline text-sm"
          >
            Try again
          </button>
        </div>
      )}
    </div>
  );
};

export default MarketChart;