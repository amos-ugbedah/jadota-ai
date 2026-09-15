import { apiClient } from './client';

// ============ Types ============
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
  mode?: 'demo' | 'live';
}

export interface Balance {
  total: number;
  available: number;
  locked: number;
}

export interface OrderResponse extends Trade {
  orderId: string;
  clientOrderId?: string;
}

// ============ API Functions ============
export const tradingApi = {
  // 📊 Positions
  getPositions: () =>
    apiClient.get<Position[]>('/trading/positions'),
  
  getPosition: (id: string) =>
    apiClient.get<Position>(`/trading/positions/${id}`),
  
  closePosition: (id: string) =>
    apiClient.post(`/trading/positions/${id}/close`),
  
  // 📈 Trade History
  getTradeHistory: (params?: { symbol?: string; limit?: number; offset?: number }) =>
    apiClient.get<Trade[]>('/trading/history', { params }),
  
  // 🛒 Orders
  placeOrder: (data: OrderRequest) =>
    apiClient.post<Trade>('/trading/orders', data),
  
  placeDemoOrder: (data: OrderRequest) =>
    apiClient.post<Trade>('/demo/positions', data),
  
  cancelOrder: (id: string) =>
    apiClient.post(`/trading/orders/${id}/cancel`),
  
  getOpenOrders: () =>
    apiClient.get<Trade[]>('/trading/orders/open'),
  
  // 💰 Balance
  getBalance: () =>
    apiClient.get<Balance>('/trading/balance'),
  
  getDemoBalance: () =>
    apiClient.get<Balance>('/demo/balance'),
  
  // 📊 Performance
  getPerformance: () =>
    apiClient.get<{
      totalPnl: number;
      totalReturn: number;
      winRate: number;
      profitFactor: number;
      maxDrawdown: number;
      sharpeRatio: number;
      totalTrades: number;
      winningTrades: number;
      losingTrades: number;
    }>('/trading/performance'),
};

// ============ Explicit Exports ============
export type { Position, Trade, Balance, OrderRequest, OrderResponse };