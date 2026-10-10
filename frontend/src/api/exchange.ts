/**
 * Exchange (Bitget) API client.
 *
 * Mirrors the shape of @/api/aiSettings — same base URL, same auth header,
 * same error surfacing so toasts behave consistently across the app.
 */

import axios, { AxiosError } from 'axios';

const API_BASE =
  import.meta.env.VITE_API_URL ||
  'https://jadota-ai.onrender.com/api/v1';

function getToken(): string | null {
  // Try the common storage keys the app uses for the access token.
  return (
    localStorage.getItem('accessToken') ||
    localStorage.getItem('token') ||
    null
  );
}

function authHeaders() {
  const token = getToken();
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