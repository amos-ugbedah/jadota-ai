import { useState, useEffect, useCallback, useRef } from 'react';
import apiClient from '@/api/client';

export interface AISignal {
  symbol: string;
  signal: 'BUY' | 'SELL' | 'HOLD';
  confidence: number;
  reasoning: string;
  risk_reward: number;
  timestamp: string;
}

export interface UseAISignalsOptions {
  refreshInterval?: number; // ms between auto-refreshes (0 = disabled)
  enabled?: boolean;
}

export interface UseAISignalsResult {
  signals: Record<string, AISignal>;
  loading: boolean;
  error: string | null;
  lastUpdate: Date | null;
  refresh: () => Promise<void>;
}

export function useAISignals({
  refreshInterval = 60000, // 60s default — AI analysis is expensive
  enabled = true,
}: UseAISignalsOptions = {}): UseAISignalsResult {
  const [signals, setSignals] = useState<Record<string, AISignal>>({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);

  const abortRef = useRef<AbortController | null>(null);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const fetchSignals = useCallback(
    async (silent = false) => {
      if (!enabled) return;

      abortRef.current?.abort();
      const controller = new AbortController();
      abortRef.current = controller;

      try {
        if (!silent) setLoading(true);
        setError(null);

        // 🔥 apiClient baseURL already includes /api/v1, so use relative path
        const raw: any = await apiClient.get('/ai/analyze/all', {
          signal: controller.signal,
        });

        // Response shape: { "BTC/USDT": {signal, confidence, ...}, ... }
        const normalized: Record<string, AISignal> = {};
        if (raw && typeof raw === 'object') {
          for (const [sym, val] of Object.entries(raw)) {
            const v = val as any;
            if (!v || typeof v !== 'object') continue;
            normalized[sym] = {
              symbol: sym,
              signal: (v.signal || 'HOLD') as AISignal['signal'],
              confidence: Number(v.confidence ?? 0),
              reasoning: String(v.reasoning ?? ''),
              risk_reward: Number(v.risk_reward ?? 1),
              timestamp: String(v.timestamp ?? new Date().toISOString()),
            };
          }
        }

        setSignals(normalized);
        setLastUpdate(new Date());
      } catch (err: any) {
        if (err?.name === 'CanceledError' || err?.name === 'AbortError') return;
        const msg =
          err?.response?.data?.detail || err?.message || 'Failed to load AI signals';
        setError(msg);
      } finally {
        if (!silent) setLoading(false);
      }
    },
    [enabled]
  );

  // Initial fetch + auto-refresh
  useEffect(() => {
    if (!enabled) return;

    fetchSignals(false);

    if (refreshInterval > 0) {
      timerRef.current = setInterval(() => fetchSignals(true), refreshInterval);
    }

    return () => {
      abortRef.current?.abort();
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [enabled, refreshInterval, fetchSignals]);

  return {
    signals,
    loading,
    error,
    lastUpdate,
    refresh: () => fetchSignals(false),
  };
}

export default useAISignals;