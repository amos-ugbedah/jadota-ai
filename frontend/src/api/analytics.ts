import apiClient from '@/api/client';

export interface SummaryStats {
  total_trades: number;
  open_positions: number;
  closed_positions: number;
  win_rate: number;
  avg_win: number;
  avg_loss: number;
  profit_factor: number;
  total_realized_pnl: number;
  total_unrealized_pnl: number;
  total_pnl: number;
  best_trade: number;
  worst_trade: number;
  avg_trade_pnl: number;
  max_win_streak: number;
  max_loss_streak: number;
  current_streak: number;
}

export interface EquityPoint {
  time: string;
  value: number;
  dailyPnl: number;
}

export interface EquityCurve {
  points: EquityPoint[];
  initial_balance: number;
  final_balance: number;
  total_return_pct: number;
}

export interface DrawdownPoint {
  time: string;
  value: number;
  peak: number;
}

export interface Drawdown {
  points: DrawdownPoint[];
  max_drawdown_pct: number;
  max_drawdown_at: string | null;
}

export interface WinLossBucket {
  label: string;
  count: number;
  type: 'win' | 'loss';
}

export interface WinLoss {
  buckets: WinLossBucket[];
  wins: number;
  losses: number;
  breakeven: number;
  total: number;
}

export interface SymbolStat {
  symbol: string;
  trades: number;
  wins: number;
  losses: number;
  win_rate: number;
  pnl: number;
  avg_pnl: number;
  profit_factor: number;
}

export interface BySymbol {
  symbols: SymbolStat[];
  best: SymbolStat | null;
  worst: SymbolStat | null;
}

export interface MonthlyCell {
  year: number;
  month: number;
  label: string;
  pnl: number;
  trades: number;
  win_rate: number;
}

export interface MonthlyHeatmap {
  months: MonthlyCell[];
}

export interface Ratios {
  sharpe: number;
  sortino: number;
  calmar: number;
  max_drawdown_pct: number;
  volatility_annual_pct: number;
  avg_daily_return_pct: number;
  total_return_pct: number;
  sample_days: number;
}

export interface JournalTrade {
  id: string;
  symbol: string;
  side: string;
  size: number;
  entryPrice: number;
  currentPrice: number;
  realizedPnl: number;
  unrealizedPnl: number;
  aiConfidence: number;
  aiReasoning: string;
  openedAt: string;
  closedAt: string | null;
  status: string;
}

export interface TradeJournal {
  trades: JournalTrade[];
  count: number;
}

export const analyticsApi = {
  getSummary: (): Promise<SummaryStats> =>
    apiClient.get('/analytics/summary'),

  getEquityCurve: (days = 30): Promise<EquityCurve> =>
    apiClient.get('/analytics/equity-curve', { params: { days } }),

  getDrawdown: (days = 30): Promise<Drawdown> =>
    apiClient.get('/analytics/drawdown', { params: { days } }),

  getWinLoss: (): Promise<WinLoss> =>
    apiClient.get('/analytics/win-loss'),

  getBySymbol: (): Promise<BySymbol> =>
    apiClient.get('/analytics/by-symbol'),

  getMonthlyHeatmap: (months = 6): Promise<MonthlyHeatmap> =>
    apiClient.get('/analytics/monthly-heatmap', { params: { months } }),

  getRatios: (days = 30): Promise<Ratios> =>
    apiClient.get('/analytics/ratios', { params: { days } }),

  getTradeJournal: (params?: {
    limit?: number;
    symbol?: string;
    status?: string;
  }): Promise<TradeJournal> =>
    apiClient.get('/analytics/trade-journal', { params }),

  seedDemoData: (key: string, count = 60): Promise<{ success: boolean; generated: number }> =>
    apiClient.post('/analytics/seed-demo-data', { key, count }),
};

export default analyticsApi;