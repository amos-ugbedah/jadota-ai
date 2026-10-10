/**
 * Exchange (Bitget) API client.
 *
 * Uses the app's auth token from whichever source it lives in.
 * Reads from, in priority order:
 *   1. Zustand auth store (`useAuthStore.getState().accessToken`)
 *   2. localStorage direct keys (accessToken / token / jwt)
 *   3. Zustand-persist envelopes (auth-storage / authStore / etc.)
 *   4. sessionStorage (same shape)
 */

import axios, { AxiosError } from 'axios';
import { useAuthStore } from '@/store/authStore';

const API_BASE =
  import.meta.env.VITE_API_URL ||
  'https://jadota-ai.onrender.com/api/v1';

// ============================================
// Token resolution — try every plausible source
// ============================================
function _tryParsePersist(raw: string | null): string | null {
  if (!raw) return null;
  try {
    const parsed = JSON.parse(raw);
    return (
      parsed?.state?.accessToken ||
      parsed?.state?.token ||
      parsed?.state?.jwt ||
      parsed?.accessToken ||
      parsed?.token ||
      null
    );
  } catch {
    return null;
  }
}

export function getAuthToken(): string | null {
  // 1. Zustand store
  try {
    const state: any = (useAuthStore as any).getState?.();
    const t = state?.accessToken || state?.token || state?.jwt;
    if (t) return t;
  } catch {
    // store not available — fall through
  }

  // 2. Direct localStorage keys
  const direct = ['accessToken', 'token', 'jwt', 'authToken'];
  for (const key of direct) {
    const v = localStorage.getItem(key);
    if (v) return v;
  }

  // 3. Zustand persist envelopes
  const persistKeys = [
    'auth-storage',
    'authStore',
    'jadota-auth',
    'auth',
    'jadota-auth-storage',
  ];
  for (const key of persistKeys) {
    const t = _tryParsePersist(localStorage.getItem(key));
    if (t) return t;
  }

  // 4. Same set of keys in sessionStorage
  for (const key of direct) {
    const v = sessionStorage.getItem(key);
    if (v) return v;
  }
  for (const key of persistKeys) {
    const t = _tryParsePersist(sessionStorage.getItem(key));
    if (t) return t;
  }

  return null;
}

function authHeaders(): Record<string, string> {
  const token = getAuthToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

function normalizeError(error: unknown): Error {
  if (axios.isAxiosError(error)) {
    const axErr = error as AxiosError<{ detail?: string }>;
    const detail =
      axErr.response?.data?.detail ||
      axErr.message ||
      'Request failed';
    return new Error(detail);
  }
  if (error instanceof Error) return error;
  return new Error('Unknown error');
}

// ============================================
// Types
// ============================================
export interface BitgetStatus {
  connected: boolean;
  exchange: string;
  api_key_masked?: string | null;
  permissions?: string | null;
  ip_whitelist?: string | null;
  is_active?: boolean;
  testnet?: boolean;
  last_used_at?: string | null;
  last_error?: string | null;
  connected_at?: string | null;
}

export interface BitgetConnectPayload {
  api_key: string;
  api_secret: string;
  passphrase: string;
}

export interface BitgetConnectResponse {
  success: boolean;
  message: string;
  status: BitgetStatus;
}

// ============================================
// API
// ============================================
export const exchangeApi = {
  async getBitgetStatus(): Promise<BitgetStatus> {
    try {
      const { data } = await axios.get<BitgetStatus>(
        `${API_BASE}/exchange/bitget/status`,
        { headers: authHeaders() }
      );
      return data;
    } catch (error) {
      throw normalizeError(error);
    }
  },

  async connectBitget(payload: BitgetConnectPayload): Promise<BitgetConnectResponse> {
    try {
      const { data } = await axios.post<BitgetConnectResponse>(
        `${API_BASE}/exchange/bitget/connect`,
        payload,
        { headers: authHeaders() }
      );
      return data;
    } catch (error) {
      throw normalizeError(error);
    }
  },

  async testBitget(): Promise<BitgetConnectResponse> {
    try {
      const { data } = await axios.post<BitgetConnectResponse>(
        `${API_BASE}/exchange/bitget/test`,
        {},
        { headers: authHeaders() }
      );
      return data;
    } catch (error) {
      throw normalizeError(error);
    }
  },

  async disconnectBitget(): Promise<{ success: boolean; message: string }> {
    try {
      const { data } = await axios.delete<{ success: boolean; message: string }>(
        `${API_BASE}/exchange/bitget/disconnect`,
        { headers: authHeaders() }
      );
      return data;
    } catch (error) {
      throw normalizeError(error);
    }
  },
};

export default exchangeApi;