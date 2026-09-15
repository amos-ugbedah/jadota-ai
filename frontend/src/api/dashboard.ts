import { apiClient } from './client';

export interface DashboardData {
  portfolio: {
    total_value: number;
    total_pnl: number;
    positions: any[];
  };
  performance: {
    total_trades: number;
    winning_trades: number;
    losing_trades: number;
    win_rate: number;
    total_pnl: number;
    avg_win: number;
    avg_loss: number;
    profit_factor: number;
    best_trade: number;
    worst_trade: number;
  };
  trade_history: any[];
  market_prices: any[];
  signals: any;
}

export const dashboardApi = {
  getDashboardData: () =>
    apiClient.get<DashboardData>('/dashboard/data'),
  
  getEquityData: (days?: number) =>
    apiClient.get<{ date: string; value: number }[]>('/dashboard/equity', { params: { days } }),
  
  getPerformanceSummary: () =>
    apiClient.get('/dashboard/performance-summary'),
};