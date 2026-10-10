/**
 * Exchange (Bitget) API client.
 *
 * Uses the shared `apiClient` (which already handles auth token attachment,
 * base URL, and interceptors) — same pattern as analytics.ts, ai.ts, etc.
 */

import apiClient from '@/api/client';

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

export interface BitgetDisconnectResponse {
  success: boolean;
  message: string;
}

// ============================================
// API
// ============================================
export const exchangeApi = {
  getBitgetStatus: (): Promise<BitgetStatus> =>
    apiClient.get('/exchange/bitget/status'),

  connectBitget: (payload: BitgetConnectPayload): Promise<BitgetConnectResponse> =>
    apiClient.post('/exchange/bitget/connect', payload),

  testBitget: (): Promise<BitgetConnectResponse> =>
    apiClient.post('/exchange/bitget/test'),

  disconnectBitget: (): Promise<BitgetDisconnectResponse> =>
    apiClient.delete('/exchange/bitget/disconnect'),
};

export default exchangeApi;