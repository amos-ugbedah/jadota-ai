import React, { useEffect, useRef } from 'react';
import {
  createChart,
  ColorType,
  CrosshairMode,
  LineStyle,
  type IChartApi,
  type ISeriesApi,
  type SeriesMarker,
  type Time,
  type UTCTimestamp,
} from 'lightweight-charts';
import type { Candle } from '@/hooks/useOHLCV';

export interface ChartOverlays {
  sma20?: boolean;
  sma50?: boolean;
  ema12?: boolean;
  ema26?: boolean;
  bollingerBands?: boolean;
}

export interface TradeMarker {
  time: number; // UNIX seconds
  position: 'aboveBar' | 'belowBar';
  color: string;
  shape: 'arrowUp' | 'arrowDown' | 'circle';
  text: string;
}

interface CandlestickChartProps {
  candles: Candle[];
  overlays?: ChartOverlays;
  markers?: TradeMarker[];
  height?: number;
  loading?: boolean;
}

/* ────────── indicator math ────────── */

function sma(values: number[], period: number): (number | null)[] {
  const out: (number | null)[] = [];
  let sum = 0;
  for (let i = 0; i < values.length; i++) {
    sum += values[i];
    if (i >= period) sum -= values[i - period];
    out.push(i >= period - 1 ? sum / period : null);
  }
  return out;
}

function ema(values: number[], period: number): (number | null)[] {
  const out: (number | null)[] = [];
  if (values.length < period) return values.map(() => null);
  const k = 2 / (period + 1);
  let prev = 0;
  for (let i = 0; i < period; i++) prev += values[i];
  prev /= period;
  for (let i = 0; i < period - 1; i++) out.push(null);
  out.push(prev);
  for (let i = period; i < values.length; i++) {
    prev = values[i] * k + prev * (1 - k);
    out.push(prev);
  }
  return out;
}

function bollingerBands(values: number[], period = 20, mult = 2) {
  const mid = sma(values, period);
  const upper: (number | null)[] = [];
  const lower: (number | null)[] = [];
  for (let i = 0; i < values.length; i++) {
    const m = mid[i];
    if (m === null) {
      upper.push(null);
      lower.push(null);
      continue;
    }
    let variance = 0;
    for (let j = i - period + 1; j <= i; j++) variance += (values[j] - m) ** 2;
    const std = Math.sqrt(variance / period);
    upper.push(m + mult * std);
    lower.push(m - mult * std);
  }
  return { mid, upper, lower };
}

/* ────────── component ────────── */

export const CandlestickChart: React.FC<CandlestickChartProps> = ({
  candles,
  overlays = {},
  markers = [],
  height = 520,
  loading = false,
}) => {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const candleRef = useRef<ISeriesApi<'Candlestick'> | null>(null);
  const overlayRefs = useRef<Map<string, ISeriesApi<'Line'>>>(new Map());

  /* create chart once */
  useEffect(() => {
    if (!containerRef.current) return;

    const chart = createChart(containerRef.current, {
      width: containerRef.current.clientWidth,
      height,
      layout: {
        background: { type: ColorType.Solid, color: '#0a0a1a' },
        textColor: '#9ca3af',
        fontFamily: 'Inter, system-ui, -apple-system, sans-serif',
      },
      grid: {
        vertLines: { color: 'rgba(42, 42, 74, 0.35)' },
        horzLines: { color: 'rgba(42, 42, 74, 0.35)' },
      },
      crosshair: {
        mode: CrosshairMode.Normal,
        vertLine: { color: '#6366f1', labelBackgroundColor: '#6366f1' },
        horzLine: { color: '#6366f1', labelBackgroundColor: '#6366f1' },
      },
      rightPriceScale: {
        borderColor: '#2a2a4a',
        scaleMargins: { top: 0.08, bottom: 0.08 },
      },
      timeScale: {
        borderColor: '#2a2a4a',
        timeVisible: true,
        secondsVisible: false,
        rightOffset: 5,
        barSpacing: 8,
      },
      handleScale: { axisPressedMouseMove: true },
      handleScroll: { vertTouchDrag: false },
      autoSize: false,
    });

    const candleSeries = chart.addCandlestickSeries({
      upColor: '#10b981',
      downColor: '#ef4444',
      borderUpColor: '#10b981',
      borderDownColor: '#ef4444',
      wickUpColor: '#10b981',
      wickDownColor: '#ef4444',
      priceLineVisible: false,
      lastValueVisible: true,
    });

    chartRef.current = chart;
    candleRef.current = candleSeries;

    // resize
    const ro = new ResizeObserver((entries) => {
      for (const e of entries) {
        const w = Math.floor(e.contentRect.width);
        if (w > 0) chart.applyOptions({ width: w });
      }
    });
    ro.observe(containerRef.current);

    return () => {
      ro.disconnect();
      chart.remove();
      chartRef.current = null;
      candleRef.current = null;
      overlayRefs.current.clear();
    };
  }, [height]);

  /* push candle data */
  useEffect(() => {
    if (!candleRef.current) return;
    const data = candles.map((c) => ({
      time: c.time as UTCTimestamp,
      open: c.open,
      high: c.high,
      low: c.low,
      close: c.close,
    }));
    candleRef.current.setData(data);
    // Only auto-fit when we first get data or the symbol/interval changed
    if (data.length > 0) chartRef.current?.timeScale().fitContent();
  }, [candles]);

  /* markers */
  useEffect(() => {
    if (!candleRef.current) return;
    const sorted: SeriesMarker<Time>[] = markers
      .slice()
      .sort((a, b) => a.time - b.time)
      .map((m) => ({
        time: m.time as UTCTimestamp,
        position: m.position,
        color: m.color,
        shape: m.shape,
        text: m.text,
      }));
    candleRef.current.setMarkers(sorted);
  }, [markers]);

  /* overlays */
  useEffect(() => {
    const chart = chartRef.current;
    if (!chart || candles.length === 0) return;

    const closes = candles.map((c) => c.close);
    const times = candles.map((c) => c.time as UTCTimestamp);

    const setLine = (
      key: string,
      color: string,
      values: (number | null)[],
      width: 1 | 2 | 3 | 4 = 2,
      dashed = false
    ) => {
      let series = overlayRefs.current.get(key);
      if (!series) {
        series = chart.addLineSeries({
          color,
          lineWidth: width,
          lineStyle: dashed ? LineStyle.Dashed : LineStyle.Solid,
          priceLineVisible: false,
          lastValueVisible: false,
          crosshairMarkerVisible: false,
        });
        overlayRefs.current.set(key, series);
      } else {
        series.applyOptions({
          color,
          lineWidth: width,
          lineStyle: dashed ? LineStyle.Dashed : LineStyle.Solid,
        });
      }
      const data = values
        .map((v, i) => (v === null ? null : { time: times[i], value: v }))
        .filter(Boolean) as { time: UTCTimestamp; value: number }[];
      series.setData(data);
    };

    const dropLine = (key: string) => {
      const series = overlayRefs.current.get(key);
      if (series) {
        chart.removeSeries(series);
        overlayRefs.current.delete(key);
      }
    };

    if (overlays.sma20) setLine('sma20', '#3b82f6', sma(closes, 20));
    else dropLine('sma20');

    if (overlays.sma50) setLine('sma50', '#a855f7', sma(closes, 50));
    else dropLine('sma50');

    if (overlays.ema12) setLine('ema12', '#fbbf24', ema(closes, 12));
    else dropLine('ema12');

    if (overlays.ema26) setLine('ema26', '#f97316', ema(closes, 26));
    else dropLine('ema26');

    if (overlays.bollingerBands) {
      const { mid, upper, lower } = bollingerBands(closes, 20, 2);
      setLine('bbUpper', '#94a3b8', upper, 1, true);
      setLine('bbLower', '#94a3b8', lower, 1, true);
      setLine('bbMid', '#64748b', mid, 1);
    } else {
      dropLine('bbUpper');
      dropLine('bbLower');
      dropLine('bbMid');
    }
  }, [candles, overlays]);

  return (
    <div className="relative w-full">
      <div
        ref={containerRef}
        style={{ height }}
        className="w-full rounded-xl overflow-hidden border border-[#2a2a4a]"
      />
      {loading && candles.length === 0 && (
        <div className="absolute inset-0 flex items-center justify-center bg-[#0a0a1a]/70 rounded-xl">
          <div className="text-sm text-gray-400 animate-pulse">Loading chart…</div>
        </div>
      )}
      {!loading && candles.length === 0 && (
        <div className="absolute inset-0 flex items-center justify-center bg-[#0a0a1a] rounded-xl border border-[#2a2a4a]">
          <div className="text-center">
            <p className="text-sm text-gray-400">No data available</p>
            <p className="mt-1 text-xs text-gray-500">Try another symbol or timeframe</p>
          </div>
        </div>
      )}
    </div>
  );
};

export default CandlestickChart;