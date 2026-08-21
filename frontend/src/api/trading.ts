import { apiClient } from './client';

export interface Position {
  id: string;
  symbol: string;
  side: 'LONG' | 'SHORT';
  size: number;
  entryPrice: number;
  currentPrice: number;
  unrealizedPnl: number;
  realizedPnl: number;
  stopLoss?: number;
  takeProfit?: number;
  openedAt: string;
  status: 'OPEN' | 'CLOSED';
}

export interface Trade {
  id: string;
  symbol: string;
  side: 'BUY' | 'SELL';
  price: number;
  size: number;
  fee: number;
  executedAt: string;
  status: 'PENDING' | 'FILLED' | 'CANCELLED' | 'REJECTED';
}

export interface OrderRequest {
  symbol: string;
  side: 'BUY' | 'SELL';
  type: 'MARKET' | 'LIMIT';
  size: number;
  price?: number;
  stopLoss?: number;
  takeProfit?: number;
}

export interface Balance {
  total: number;
  available: number;
  locked: number;
}

export const tradingApi = {
  getPositions: () =>
    apiClient.get<Position[]>('/trading/positions'),
  
  getPosition: (id: string) =>
    apiClient.get<Position>(`/trading/positions/${id}`),
  
  closePosition: (id: string) =>
    apiClient.post(`/trading/positions/${id}/close`),
  
  getTradeHistory: (params?: { symbol?: string; limit?: number }) =>
    apiClient.get<Trade[]>('/trading/history', { params }),
  
  placeOrder: (data: OrderRequest) =>
    apiClient.post<Trade>('/trading/orders', data),
  
  cancelOrder: (id: string) =>
    apiClient.post(`/trading/orders/${id}/cancel`),
  
  getBalance: () =>
    apiClient.get<Balance>('/trading/balance'),
  
  getOpenOrders: () =>
    apiClient.get<Trade[]>('/trading/orders/open'),
};

// ✅ Make sure Balance is exported
export type { Position, Trade, Balance };