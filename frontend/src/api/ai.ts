import { apiClient } from './client';

export interface AISignal {
  symbol: string;
  signal: 'BUY' | 'SELL' | 'HOLD';
  confidence: number;
  reasoning: string;
  risk_reward: number;
  indicators: {
    close: number;
    sma_7: number;
    sma_25: number;
    sma_99: number;
    ema_12: number;
    ema_26: number;
    rsi: number;
    macd: number;
    macd_signal: number;
    macd_histogram: number;
    bb_upper: number;
    bb_middle: number;
    bb_lower: number;
  };
  timestamp: string;
}

export interface AIStatus {
  status: string;
  symbols_analyzed: number;
  last_update: string;
}

export interface TradeResult {
  id: string;
  symbol: string;
  side: string;
  size: number;
  entryPrice: number;
  status: string;
}

export interface Portfolio {
  total_value: number;
  total_pnl: number;
  positions: any[];
}

export interface PerformanceStats {
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
}

export const aiApi = {
  // 🤖 AI Signals
  analyzeSymbol: (symbol: string, timeframe: string = '1h') =>
    apiClient.get<AISignal>(`/ai/analyze/${symbol}`, { params: { timeframe } }),
  
  analyzeAll: () =>
    apiClient.get<Record<string, AISignal>>('/ai/analyze/all'),
  
  getStatus: () =>
    apiClient.get<AIStatus>('/ai/status'),
  
  // 🔥 Auto-Trading
  startAutoTrading: () =>
    apiClient.post<{ message: string; trades: TradeResult[] }>('/ai/auto-trade'),
  
  getPortfolio: () =>
    apiClient.get<Portfolio>('/ai/portfolio'),
  
  // 📊 Performance & History
  getTradeHistory: () =>
    apiClient.get<any[]>('/ai/trade-history'),
  
  getPerformance: () =>
    apiClient.get<PerformanceStats>('/ai/performance'),
};