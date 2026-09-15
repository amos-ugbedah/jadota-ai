import React, { useEffect, useRef } from 'react';
import {
  createChart,
  ColorType,
  CrosshairMode,
  LineStyle,
  type IChartApi,
  type ISeriesApi,
  type UTCTimestamp,
} from 'lightweight-charts';
import type { Candle } from '@/hooks/useOHLCV';

/* ────────── indicator math ────────── */

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

function rsi(values: number[], period = 14): (number | null)[] {
  const out: (number | null)[] = [];
  if (values.length < period + 1) return values.map(() => null);
  let gain = 0;
  let loss = 0;
  for (let i = 1; i <= period; i++) {
    const d = values[i] - values[i - 1];
    if (d >= 0) gain += d;
    else loss -= d;
  }
  let avgGain = gain / period;
  let avgLoss = loss / period;
  for (let i = 0; i < period; i++) out.push(null);
  out.push(avgLoss === 0 ? 100 : 100 - 100 / (1 + avgGain / avgLoss));
  for (let i = period + 1; i < values.length; i++) {
    const d = values[i] - values[i - 1];
    const g = d > 0 ? d : 0;
    const l = d < 0 ? -d : 0;
    avgGain = (avgGain * (period - 1) + g) / period;
    avgLoss = (avgLoss * (period - 1) + l) / period;
    out.push(avgLoss === 0 ? 100 : 100 - 100 / (1 + avgGain / avgLoss));
  }
  return out;
}

function macd(values: number[]) {
  const e12 = ema(values, 12);
  const e26 = ema(values, 26);
  const macdLine = e12.map((v, i) =>
    v !== null && e26[i] !== null ? v - (e26[i] as number) : null
  );
  const sig = ema(
    macdLine.map((v) => v ?? 0),
    9
  );
  const hist = macdLine.map((v, i) =>
    v !== null && sig[i] !== null ? v - (sig[i] as number) : null
  );
  return { macdLine, signal: sig, hist };
}

/* ────────── shared chart options ────────── */

const baseChartOptions = (height: number) =>
  ({
    width: 0, // set on mount
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
    crosshair: { mode: CrosshairMode.Normal },
    rightPriceScale: {
      borderColor: '#2a2a4a',
      scaleMargins: { top: 0.2, bottom: 0.15 },
    },
    timeScale: {
      borderColor: '#2a2a4a',
      timeVisible: true,
      secondsVisible: false,
    },
    handleScale: { axisPressedMouseMove: false },
    handleScroll: { vertTouchDrag: false, pressedMouseMove: true, mouseWheel: true },
  }) as const;

/* ────────── RSI ────────── */

interface SubchartProps {
  candles: Candle[];
  height?: number;
}

export const RSIPanel: React.FC<SubchartProps> = ({ candles, height = 140 }) => {
  const ref = useRef<HTMLDivElement | null>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const seriesRef = useRef<ISeriesApi<'Line'> | null>(null);

  useEffect(() => {
    if (!ref.current) return;
    const chart = createChart(ref.current, {
      ...baseChartOptions(height),
      width: ref.current.clientWidth,
    });
    const series = chart.addLineSeries({
      color: '#6366f1',
      lineWidth: 2,
      priceLineVisible: false,
      lastValueVisible: true,
    });
    series.createPriceLine({
      price: 70,
      color: 'rgba(239, 68, 68, 0.6)',
      lineWidth: 1,
      lineStyle: LineStyle.Dashed,
      axisLabelVisible: true,
      title: '70',
    });
    series.createPriceLine({
      price: 30,
      color: 'rgba(16, 185, 129, 0.6)',
      lineWidth: 1,
      lineStyle: LineStyle.Dashed,
      axisLabelVisible: true,
      title: '30',
    });
    chartRef.current = chart;
    seriesRef.current = series;

    const ro = new ResizeObserver((entries) => {
      for (const e of entries) {
        const w = Math.floor(e.contentRect.width);
        if (w > 0) chart.applyOptions({ width: w });
      }
    });
    ro.observe(ref.current);

    return () => {
      ro.disconnect();
      chart.remove();
      chartRef.current = null;
      seriesRef.current = null;
    };
  }, [height]);

  useEffect(() => {
    if (!seriesRef.current) return;
    const closes = candles.map((c) => c.close);
    const times = candles.map((c) => c.time as UTCTimestamp);
    const vals = rsi(closes, 14);
    const data = vals
      .map((v, i) => (v === null ? null : { time: times[i], value: v }))
      .filter(Boolean) as { time: UTCTimestamp; value: number }[];
    seriesRef.current.setData(data);
    if (data.length > 0) chartRef.current?.timeScale().fitContent();
  }, [candles]);

  return (
    <div className="relative">
      <div className="absolute z-10 text-xs font-medium text-gray-400 pointer-events-none top-2 left-3">
        RSI (14)
      </div>
      <div
        ref={ref}
        className="w-full rounded-xl overflow-hidden border border-[#2a2a4a]"
        style={{ height }}
      />
    </div>
  );
};

/* ────────── MACD ────────── */

export const MACDPanel: React.FC<SubchartProps> = ({ candles, height = 160 }) => {
  const ref = useRef<HTMLDivElement | null>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const macdRef = useRef<ISeriesApi<'Line'> | null>(null);
  const sigRef = useRef<ISeriesApi<'Line'> | null>(null);
  const histRef = useRef<ISeriesApi<'Histogram'> | null>(null);

  useEffect(() => {
    if (!ref.current) return;
    const chart = createChart(ref.current, {
      ...baseChartOptions(height),
      width: ref.current.clientWidth,
    });
    const macdSeries = chart.addLineSeries({
      color: '#6366f1',
      lineWidth: 2,
      priceLineVisible: false,
      lastValueVisible: false,
    });
    const sigSeries = chart.addLineSeries({
      color: '#fbbf24',
      lineWidth: 2,
      priceLineVisible: false,
      lastValueVisible: false,
    });
    const histSeries = chart.addHistogramSeries({
      priceLineVisible: false,
      lastValueVisible: false,
    });
    chartRef.current = chart;
    macdRef.current = macdSeries;
    sigRef.current = sigSeries;
    histRef.current = histSeries;

    const ro = new ResizeObserver((entries) => {
      for (const e of entries) {
        const w = Math.floor(e.contentRect.width);
        if (w > 0) chart.applyOptions({ width: w });
      }
    });
    ro.observe(ref.current);

    return () => {
      ro.disconnect();
      chart.remove();
      chartRef.current = null;
      macdRef.current = null;
      sigRef.current = null;
      histRef.current = null;
    };
  }, [height]);

  useEffect(() => {
    if (!macdRef.current || !sigRef.current || !histRef.current) return;
    const closes = candles.map((c) => c.close);
    const times = candles.map((c) => c.time as UTCTimestamp);
    const { macdLine, signal, hist } = macd(closes);

    macdRef.current.setData(
      macdLine
        .map((v, i) => (v === null ? null : { time: times[i], value: v }))
        .filter(Boolean) as { time: UTCTimestamp; value: number }[]
    );
    sigRef.current.setData(
      signal
        .map((v, i) => (v === null ? null : { time: times[i], value: v }))
        .filter(Boolean) as { time: UTCTimestamp; value: number }[]
    );
    histRef.current.setData(
      hist
        .map((v, i) =>
          v === null
            ? null
            : {
                time: times[i],
                value: v,
                color: v >= 0 ? 'rgba(16, 185, 129, 0.65)' : 'rgba(239, 68, 68, 0.65)',
              }
        )
        .filter(Boolean) as { time: UTCTimestamp; value: number; color: string }[]
    );
    chartRef.current?.timeScale().fitContent();
  }, [candles]);

  return (
    <div className="relative">
      <div className="absolute z-10 text-xs font-medium text-gray-400 pointer-events-none top-2 left-3">
        MACD (12, 26, 9)
      </div>
      <div
        ref={ref}
        className="w-full rounded-xl overflow-hidden border border-[#2a2a4a]"
        style={{ height }}
      />
    </div>
  );
};