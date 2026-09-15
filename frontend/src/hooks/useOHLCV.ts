import { useState, useEffect, useCallback, useRef } from 'react';
import apiClient from '@/api/client';

export interface Candle {
  /** UNIX timestamp in SECONDS — what lightweight-charts expects */
  time: number;
  /** Original timestamp in ms — kept for reference/debugging */
  timestamp: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface UseOHLCVOptions {
  symbol: string;
  interval: string;
  limit?: number;
  refreshInterval?: number;   // ms between auto-refreshes (0 = disabled)
  enabled?: boolean;
}

export interface UseOHLCVResult {
  candles: Candle[];
  loading: boolean;
  error: string | null;
  lastUpdate: Date | null;
  refresh: () => Promise<void>;
}

export function useOHLCV({
  symbol,
  interval,
  limit = 300,
  refreshInterval = 15000,
  enabled = true,
}: UseOHLCVOptions): UseOHLCVResult {
  const [candles, setCandles] = useState<Candle[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);

  const abortRef = useRef<AbortController | null>(null);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const fetchCandles = useCallback(
    async (silent = false) => {
      if (!enabled || !symbol || !interval) return;

      // Cancel previous request
      abortRef.current?.abort();
      const controller = new AbortController();
      abortRef.current = controller;

      try {
        if (!silent) setLoading(true);
        setError(null);

        // 🔥 FIX: apiClient's baseURL already includes /api/v1, so use
        // a relative path WITHOUT the prefix. Also send the raw symbol
        // (BTC/USDT) — the backend route uses {symbol:path} to accept it.
        const raw = await apiClient.get(
          `/market/ohlcv/${symbol}`,
          {
            params: { interval, limit },
            signal: controller.signal,
          }
        );

        // apiClient's response interceptor returns response.data directly
        const list: any[] = Array.isArray(raw) ? raw : [];

        // Normalize → filter bad rows → sort oldest-first → dedupe
        const seen = new Set<number>();
        const normalized: Candle[] = list
          .map((c) => {
            const timestamp = Number(c?.timestamp);
            const time = Math.floor(timestamp / 1000);
            return {
              timestamp,
              time,
              open: Number(c?.open),
              high: Number(c?.high),
              low: Number(c?.low),
              close: Number(c?.close),
              volume: Number(c?.volume),
            };
          })
          .filter(
            (c) =>
              Number.isFinite(c.time) &&
              Number.isFinite(c.open) &&
              Number.isFinite(c.high) &&
              Number.isFinite(c.low) &&
              Number.isFinite(c.close) &&
              c.high >= c.low &&
              c.open > 0
          )
          .sort((a, b) => a.time - b.time)
          .filter((c) => {
            if (seen.has(c.time)) return false;
            seen.add(c.time);
            return true;
          });

        setCandles(normalized);
        setLastUpdate(new Date());
      } catch (err: any) {
        if (err?.name === 'CanceledError' || err?.name === 'AbortError') return;
        const msg =
          err?.response?.data?.detail ||
          err?.message ||
          'Failed to load candles';
        setError(msg);
      } finally {
        if (!silent) setLoading(false);
      }
    },
    [symbol, interval, limit, enabled]
  );

  // Fetch on symbol/interval change
  useEffect(() => {
    fetchCandles(false);
  }, [fetchCandles]);

  // Auto-refresh loop
  useEffect(() => {
    if (!enabled || refreshInterval <= 0) return;
    timerRef.current = setInterval(() => fetchCandles(true), refreshInterval);
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [enabled, refreshInterval, fetchCandles]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      abortRef.current?.abort();
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, []);

  return {
    candles,
    loading,
    error,
    lastUpdate,
    refresh: () => fetchCandles(false),
  };
}

export default useOHLCV;