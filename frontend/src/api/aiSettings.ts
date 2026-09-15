import { apiClient } from './client';

export interface AISettings {
  id: string;
  user_id: string;
  confidence_threshold: number;
  strategy_type: 'conservative' | 'balanced' | 'aggressive';
  trade_amount: number;  // 🔥 ADD THIS
  stop_loss_percent: number;
  take_profit_percent: number;
  max_daily_loss: number;
  max_drawdown: number;
  max_positions: number;
  risk_per_trade: number;
  position_size_multiplier: number;
  symbols: string[];
  auto_trade_enabled: boolean;
  max_trades_per_day: number;
  total_trades: number;
  winning_trades: number;
  losing_trades: number;
  total_pnl: number;
  best_trade: number;
  worst_trade: number;
  created_at: string;
  updated_at: string;
  win_rate?: number;
  strategy_label?: string;
}

export interface StrategyPreset {
  type: string;
  label: string;
  description: string;
  icon: string;
  risk_level: string;
  settings: {
    confidence_threshold: number;
    stop_loss_percent: number;
    take_profit_percent: number;
    position_size_multiplier: number;
    max_positions: number;
    trade_amount: number;
  };
}

export interface PerformanceStats {
  total_trades: number;
  winning_trades: number;
  losing_trades: number;
  win_rate: number;
  total_pnl: number;
  best_trade: number;
  worst_trade: number;
}

export const aiSettingsApi = {
  getSettings: () => apiClient.get<AISettings>('/ai-settings'),
  updateSettings: (data: Partial<AISettings>) => apiClient.put<AISettings>('/ai-settings', data),
  getPresets: () => apiClient.get<StrategyPreset[]>('/ai-settings/presets'),
  applyPreset: (presetType: string) =>
    apiClient.post<{ message: string; settings: AISettings }>(
      `/ai-settings/apply-preset/${presetType}`
    ),
  getSymbols: () =>
    apiClient.get<{ symbol: string; name: string; icon: string }[]>('/ai-settings/symbols'),
  getPerformance: () =>
    apiClient.get<PerformanceStats>('/ai-settings/performance-stats'),
  toggleAutoTrade: (enabled: boolean) =>
    apiClient.post<{ auto_trade_enabled: boolean; message: string }>(
      '/ai-settings/toggle-auto-trade',
      null,
      { params: { enabled } }
    ),
};