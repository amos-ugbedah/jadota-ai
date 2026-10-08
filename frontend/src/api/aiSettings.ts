import { apiClient } from './client';

// ============================================
// Types
// ============================================
export type StrategyName =
  | 'conservative'
  | 'balanced'
  | 'aggressive'
  | 'scalping'
  | 'swing';

export interface AISettings {
  id: string;
  user_id: string;
  confidence_threshold: number;
  strategy_type: StrategyName;
  trade_amount: number;
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

export interface StrategyDefaults {
  confidence_threshold: number;
  trade_amount: number;
  stop_loss_percent: number;
  take_profit_percent: number;
  position_size_multiplier: number;
  max_positions: number;
  max_trades_per_day: number;
  risk_per_trade: number;
}

export interface StrategyInfo {
  name: StrategyName;
  label: string;
  description: string;
  risk_level: 'Low' | 'Medium' | 'High';
  icon: string;
  color: string;
  timeframe: string;
  defaults: StrategyDefaults;
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

// ============================================
// API Client
// ============================================
export const aiSettingsApi = {
  // ---- Settings ----
  getSettings: () =>
    apiClient.get<AISettings>('/ai-settings'),

  updateSettings: (data: Partial<AISettings>) =>
    apiClient.put<AISettings>('/ai-settings', data),

  // ---- Symbols / Performance ----
  getSymbols: () =>
    apiClient.get<{ symbol: string; name: string; icon: string }[]>(
      '/ai-settings/symbols'
    ),

  getPerformance: () =>
    apiClient.get<PerformanceStats>('/ai-settings/performance-stats'),

  // ---- Auto-trade toggle ----
  toggleAutoTrade: (enabled: boolean) =>
    apiClient.post<{ auto_trade_enabled: boolean; message: string }>(
      '/ai-settings/toggle-auto-trade',
      null,
      { params: { enabled } }
    ),

  // ---- Legacy preset API (kept for backward compatibility) ----
  getPresets: () =>
    apiClient.get<StrategyPreset[]>('/ai-settings/presets'),

  applyPreset: (presetType: string) =>
    apiClient.post<{ message: string; settings: AISettings }>(
      `/ai-settings/apply-preset/${presetType}`
    ),

  // ---- Strategy registry API (new) ----
  getStrategies: () =>
    apiClient.get<{ strategies: StrategyInfo[] }>(
      '/ai-settings/strategies'
    ),

  applyStrategy: (name: StrategyName | string) =>
    apiClient.post<{
      success: boolean;
      message: string;
      strategy: StrategyInfo;
      settings: AISettings;
    }>(`/ai-settings/apply-strategy/${name}`),
};

export default aiSettingsApi;