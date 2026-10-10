/**
 * Exchange (Bitget) API client.
 *
 * Uses the shared `apiClient` (auth, base URL, interceptors).
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

export interface BalanceItem {
  asset: string;
  free: number;
  used: number;
  total: number;
}

export interface BitgetBalanceResponse {
  success: boolean;
  exchange: string;
  testnet: boolean;
  balances: BalanceItem[];
  total_usdt_value: number | null;
}

export interface ManualOrderPayload {
  symbol: string;
  side: 'BUY' | 'SELL';
  size: number;
  type?: 'MARKET' | 'LIMIT';
  stopLoss?: number;
  takeProfit?: number;
}

export interface ManualOrderResponse {
  id: string;
  user_id: string;
  symbol: string;
  side: string;
  size: number;
  entryPrice: number;
  currentPrice: number;
  unrealizedPnl: number;
  realizedPnl: number;
  tradeAmount: number;
  stopLoss?: number;
  takeProfit?: number;
  status: string;
  source: string;
  bitgetOrderId?: string | null;
  openedAt?: string | null;
  [key: string]: any;
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

  getBalance: (asset?: string): Promise<BitgetBalanceResponse> =>
    apiClient.get('/exchange/bitget/balance', {
      params: asset ? { asset } : undefined,
    }),

  placeManualOrder: (payload: ManualOrderPayload): Promise<ManualOrderResponse> =>
    apiClient.post('/trading/manual-order', payload),
};

export default exchangeApi;