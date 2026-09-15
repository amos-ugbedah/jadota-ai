import React, { useState, useEffect } from 'react';
import { useAuthStore } from '@/store/authStore';
import { aiSettingsApi } from '@/api/aiSettings';
import type { AISettings, StrategyPreset, PerformanceStats } from '@/api/aiSettings';
import { toast } from 'react-hot-toast';
import {
  Brain,
  Shield,
  Target,
  Zap,
  Settings,
  RefreshCw,
  Loader2,
  CheckCircle,
  AlertTriangle,
  Sliders,
  Coins,
  Activity,
  Power,
  PowerOff,
  TrendingUp,
  TrendingDown,
  AlertCircle,
  Scale,
  Sparkles,
  Info,
  Award,
  BarChart3,
  DollarSign,
  Clock,
} from 'lucide-react';

const AISettingsPage: React.FC = () => {
  const { user } = useAuthStore();
  const [settings, setSettings] = useState<AISettings | null>(null);
  const [presets, setPresets] = useState<StrategyPreset[]>([]);
  const [availableSymbols, setAvailableSymbols] = useState<any[]>([]);
  const [performance, setPerformance] = useState<PerformanceStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [isToggling, setIsToggling] = useState(false);
  const [activeTab, setActiveTab] = useState<'general' | 'risk' | 'symbols' | 'performance'>('general');

  const fetchAllData = async () => {
    try {
      setIsLoading(true);
      
      const [settingsData, presetsData, symbolsData, performanceData] = await Promise.all([
        aiSettingsApi.getSettings(),
        aiSettingsApi.getPresets(),
        aiSettingsApi.getSymbols(),
        aiSettingsApi.getPerformance(),
      ]);
      
      setSettings(settingsData);
      setPresets(presetsData);
      setAvailableSymbols(symbolsData);
      setPerformance(performanceData);
    } catch (error: any) {
      toast.error(error.message || 'Failed to load settings');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchAllData();
  }, []);

  const handleSave = async () => {
    if (!settings) return;
    
    setIsSaving(true);
    try {
      const updated = await aiSettingsApi.updateSettings({
        confidence_threshold: settings.confidence_threshold,
        trade_amount: settings.trade_amount,  // 🔥 ADD THIS
        stop_loss_percent: settings.stop_loss_percent,
        take_profit_percent: settings.take_profit_percent,
        position_size_multiplier: settings.position_size_multiplier,
        max_positions: settings.max_positions,
        max_daily_loss: settings.max_daily_loss,
        max_drawdown: settings.max_drawdown,
        strategy_type: settings.strategy_type,
        symbols: settings.symbols,
        risk_per_trade: settings.risk_per_trade,
        max_trades_per_day: settings.max_trades_per_day,
      });
      setSettings(updated);
      toast.success('Settings saved successfully! 🎉');
    } catch (error: any) {
      toast.error(error.message || 'Failed to save settings');
    } finally {
      setIsSaving(false);
    }
  };

  const handleApplyPreset = async (presetType: string) => {
    try {
      const result = await aiSettingsApi.applyPreset(presetType);
      setSettings(result.settings);
      toast.success(`Applied ${presetType} strategy preset! 🚀`);
    } catch (error: any) {
      toast.error(error.message || 'Failed to apply preset');
    }
  };

  const handleToggleAutoTrade = async () => {
    if (!settings) return;
    
    setIsToggling(true);
    try {
      const result = await aiSettingsApi.toggleAutoTrade(!settings.auto_trade_enabled);
      setSettings({ ...settings, auto_trade_enabled: result.auto_trade_enabled });
      toast.success(result.message);
    } catch (error: any) {
      toast.error(error.message || 'Failed to toggle auto-trade');
    } finally {
      setIsToggling(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <Loader2 className="w-12 h-12 text-[#6366f1] animate-spin mx-auto" />
          <p className="mt-4 text-gray-400">Loading AI settings...</p>
        </div>
      </div>
    );
  }

  if (!settings) return null;

  const updateSetting = <K extends keyof AISettings>(key: K, value: AISettings[K]) => {
    setSettings({ ...settings, [key]: value });
  };

  const getStrategyColor = (type: string) => {
    switch(type) {
      case 'conservative': return 'text-green-400 bg-green-500/10 border-green-500/30';
      case 'aggressive': return 'text-red-400 bg-red-500/10 border-red-500/30';
      default: return 'text-blue-400 bg-blue-500/10 border-blue-500/30';
    }
  };

  const getRiskLevelColor = (level: string) => {
    switch(level) {
      case 'Low': return 'text-green-400';
      case 'Medium': return 'text-yellow-400';
      case 'High': return 'text-red-400';
      default: return 'text-gray-400';
    }
  };

  return (
    <div className="max-w-5xl p-6 mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col items-start justify-between gap-4 md:flex-row md:items-center">
        <div>
          <div className="flex items-center gap-3">
            <Brain className="w-8 h-8 text-[#6366f1]" />
            <h1 className="text-3xl font-bold text-white">AI Strategy Settings</h1>
          </div>
          <p className="mt-1 text-gray-400">
            Configure how the AI trades for you
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <button
            onClick={handleToggleAutoTrade}
            disabled={isToggling}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition ${
              settings.auto_trade_enabled
                ? 'bg-green-500/20 text-green-400 border border-green-500/30 hover:bg-green-500/30'
                : 'bg-yellow-500/20 text-yellow-400 border border-yellow-500/30 hover:bg-yellow-500/30'
            }`}
          >
            {isToggling ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : settings.auto_trade_enabled ? (
              <>
                <Power className="w-4 h-4" />
                Auto-Trade ON
              </>
            ) : (
              <>
                <PowerOff className="w-4 h-4" />
                Auto-Trade OFF
              </>
            )}
          </button>
          <button
            onClick={handleSave}
            disabled={isSaving}
            className="flex items-center gap-2 px-4 py-2 bg-[#6366f1] text-white rounded-lg hover:bg-[#4f46e5] transition disabled:opacity-50"
          >
            {isSaving ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <CheckCircle className="w-4 h-4" />
            )}
            Save Changes
          </button>
        </div>
      </div>

      {/* Strategy Presets */}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
        {presets.map((preset) => (
          <button
            key={preset.type}
            onClick={() => handleApplyPreset(preset.type)}
            className={`p-4 rounded-xl border transition text-left ${
              settings.strategy_type === preset.type
                ? `${getStrategyColor(preset.type)} border-2`
                : 'bg-[#1a1a2e] border-[#2a2a4a] hover:border-[#3a3a5a]'
            }`}
          >
            <div className="flex items-center justify-between mb-2">
              <span className="text-lg font-semibold text-white">{preset.label}</span>
              <span className={`text-xs font-medium ${getRiskLevelColor(preset.risk_level)}`}>
                {preset.risk_level} Risk
              </span>
            </div>
            <p className="text-sm text-gray-400">{preset.description}</p>
            {settings.strategy_type === preset.type && (
              <div className="mt-2 text-xs text-[#6366f1]">✓ Currently Active</div>
            )}
          </button>
        ))}
      </div>

      {/* Tabs */}
      <div className="flex gap-2 border-b border-[#2a2a4a] pb-2 overflow-x-auto">
        <TabButton
          active={activeTab === 'general'}
          onClick={() => setActiveTab('general')}
          icon={<Sliders className="w-4 h-4" />}
          label="General"
        />
        <TabButton
          active={activeTab === 'risk'}
          onClick={() => setActiveTab('risk')}
          icon={<Shield className="w-4 h-4" />}
          label="Risk Management"
        />
        <TabButton
          active={activeTab === 'symbols'}
          onClick={() => setActiveTab('symbols')}
          icon={<Coins className="w-4 h-4" />}
          label="Symbols"
        />
        <TabButton
          active={activeTab === 'performance'}
          onClick={() => setActiveTab('performance')}
          icon={<BarChart3 className="w-4 h-4" />}
          label="Performance"
        />
      </div>

      {/* General Tab */}
      {activeTab === 'general' && (
        <div className="space-y-6">
          <div className="bg-[#1a1a2e] rounded-xl p-6 border border-[#2a2a4a]">
            <h3 className="mb-4 text-lg font-semibold text-white">📊 Strategy Settings</h3>
            
            <div className="space-y-6">
              {/* Confidence Threshold */}
              <div>
                <div className="flex items-center justify-between mb-1">
                  <label className="text-sm font-medium text-gray-400">
                    Confidence Threshold
                  </label>
                  <span className="text-lg font-bold text-[#6366f1]">
                    {settings.confidence_threshold}%
                  </span>
                </div>
                <input
                  type="range"
                  min="50"
                  max="90"
                  step="1"
                  value={settings.confidence_threshold}
                  onChange={(e) => updateSetting('confidence_threshold', parseFloat(e.target.value))}
                  className="w-full h-2 bg-[#0a0a1a] rounded-lg appearance-none cursor-pointer accent-[#6366f1]"
                />
                <div className="flex justify-between mt-1 text-xs text-gray-500">
                  <span>🟢 Lower (more trades)</span>
                  <span>🔴 Higher (fewer trades)</span>
                </div>
                <p className="mt-2 text-xs text-gray-500">
                  AI must be at least {settings.confidence_threshold}% confident before trading
                </p>
              </div>

              {/* 🔥 Per-Trade Amount */}
              <div className="pt-4 border-t border-[#2a2a4a]">
                <div className="flex items-center justify-between mb-2">
                  <label className="text-sm font-medium text-gray-400">
                    Per-Trade Amount (Base)
                  </label>
                  <span className="text-2xl font-bold text-[#6366f1]">
                    ${settings.trade_amount.toFixed(0)}
                  </span>
                </div>
                
                {/* Quick amount buttons */}
                <div className="flex flex-wrap gap-2 mb-3">
                  {[2, 5, 10, 25, 50, 100, 500, 1000].map((amount) => (
                    <button
                      key={amount}
                      type="button"
                      onClick={() => updateSetting('trade_amount', amount)}
                      className={`px-3 py-1.5 rounded-lg text-xs font-medium transition ${
                        settings.trade_amount === amount
                          ? 'bg-[#6366f1] text-white'
                          : 'bg-[#0a0a1a] text-gray-400 hover:text-white hover:bg-[#2a2a4a] border border-[#2a2a4a]'
                      }`}
                    >
                      ${amount}
                    </button>
                  ))}
                </div>
                
                {/* Custom amount input */}
                <div className="flex items-center gap-3">
                  <input
                    type="range"
                    min="1"
                    max="1000"
                    step="1"
                    value={Math.min(settings.trade_amount, 1000)}
                    onChange={(e) => updateSetting('trade_amount', parseFloat(e.target.value))}
                    className="flex-1 h-2 bg-[#0a0a1a] rounded-lg appearance-none cursor-pointer accent-[#6366f1]"
                  />
                  <div className="relative">
                    <span className="absolute text-sm text-gray-400 -translate-y-1/2 left-3 top-1/2">
                      $
                    </span>
                    <input
                      type="number"
                      min="1"
                      max="10000"
                      step="1"
                      value={settings.trade_amount}
                      onChange={(e) => updateSetting('trade_amount', parseFloat(e.target.value) || 1)}
                      className="w-28 pl-7 pr-3 py-2 bg-[#0a0a1a] border border-[#2a2a4a] rounded-lg text-white text-center focus:outline-none focus:ring-2 focus:ring-[#6366f1]"
                    />
                  </div>
                </div>
                
                {/* Hybrid scaling info */}
                <div className="mt-3 p-3 bg-[#0a0a1a] rounded-lg border border-[#2a2a4a]">
                  <p className="mb-2 text-xs text-gray-400">
                    <span className="font-medium text-white">🏆 Hybrid Scaling Active:</span>{' '}
                    Amount auto-scales with AI confidence
                  </p>
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <div className="flex justify-between">
                      <span className="text-gray-500">85%+ conf:</span>
                      <span className="text-green-400">100% = ${settings.trade_amount.toFixed(0)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-500">75%+ conf:</span>
                      <span className="text-blue-400">80% = ${(settings.trade_amount * 0.8).toFixed(0)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-500">65%+ conf:</span>
                      <span className="text-yellow-400">60% = ${(settings.trade_amount * 0.6).toFixed(0)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-500">Below 55%:</span>
                      <span className="text-red-400">20-40%</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Position Size */}
              <div>
                <div className="flex items-center justify-between mb-1">
                  <label className="text-sm font-medium text-gray-400">
                    Position Size Multiplier
                  </label>
                  <span className="text-lg font-bold text-[#6366f1]">
                    {settings.position_size_multiplier}x
                  </span>
                </div>
                <input
                  type="range"
                  min="0.1"
                  max="3"
                  step="0.1"
                  value={settings.position_size_multiplier}
                  onChange={(e) => updateSetting('position_size_multiplier', parseFloat(e.target.value))}
                  className="w-full h-2 bg-[#0a0a1a] rounded-lg appearance-none cursor-pointer accent-[#6366f1]"
                />
                <div className="flex justify-between mt-1 text-xs text-gray-500">
                  <span>Smaller positions</span>
                  <span>Larger positions</span>
                </div>
              </div>

              {/* Max Trades Per Day */}
              <div>
                <div className="flex items-center justify-between mb-1">
                  <label className="text-sm font-medium text-gray-400">
                    Max Trades Per Day
                  </label>
                  <span className="text-lg font-bold text-[#6366f1]">
                    {settings.max_trades_per_day}
                  </span>
                </div>
                <input
                  type="range"
                  min="1"
                  max="50"
                  step="1"
                  value={settings.max_trades_per_day}
                  onChange={(e) => updateSetting('max_trades_per_day', parseInt(e.target.value))}
                  className="w-full h-2 bg-[#0a0a1a] rounded-lg appearance-none cursor-pointer accent-[#6366f1]"
                />
                <div className="flex justify-between mt-1 text-xs text-gray-500">
                  <span>Fewer trades</span>
                  <span>More trades</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Risk Tab */}
      {activeTab === 'risk' && (
        <div className="space-y-6">
          <div className="bg-[#1a1a2e] rounded-xl p-6 border border-[#2a2a4a]">
            <h3 className="mb-4 text-lg font-semibold text-white">🛡️ Risk Management</h3>
            
            <div className="space-y-6">
              <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
                {/* Stop Loss */}
                <div>
                  <div className="flex items-center justify-between mb-1">
                    <label className="text-sm font-medium text-gray-400">Stop Loss</label>
                    <span className="text-lg font-bold text-red-400">
                      {settings.stop_loss_percent}%
                    </span>
                  </div>
                  <input
                    type="range"
                    min="0.5"
                    max="10"
                    step="0.5"
                    value={settings.stop_loss_percent}
                    onChange={(e) => updateSetting('stop_loss_percent', parseFloat(e.target.value))}
                    className="w-full h-2 bg-[#0a0a1a] rounded-lg appearance-none cursor-pointer accent-red-500"
                  />
                  <div className="flex justify-between mt-1 text-xs text-gray-500">
                    <span>Tighter</span>
                    <span>Wider</span>
                  </div>
                </div>

                {/* Take Profit */}
                <div>
                  <div className="flex items-center justify-between mb-1">
                    <label className="text-sm font-medium text-gray-400">Take Profit</label>
                    <span className="text-lg font-bold text-green-400">
                      {settings.take_profit_percent}%
                    </span>
                  </div>
                  <input
                    type="range"
                    min="1"
                    max="20"
                    step="0.5"
                    value={settings.take_profit_percent}
                    onChange={(e) => updateSetting('take_profit_percent', parseFloat(e.target.value))}
                    className="w-full h-2 bg-[#0a0a1a] rounded-lg appearance-none cursor-pointer accent-green-500"
                  />
                  <div className="flex justify-between mt-1 text-xs text-gray-500">
                    <span>Take profit early</span>
                    <span>Let profits run</span>
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
                {/* Max Daily Loss */}
                <div>
                  <div className="flex items-center justify-between mb-1">
                    <label className="text-sm font-medium text-gray-400">Max Daily Loss</label>
                    <span className="text-lg font-bold text-yellow-400">
                      {settings.max_daily_loss}%
                    </span>
                  </div>
                  <input
                    type="range"
                    min="0.5"
                    max="30"
                    step="0.5"
                    value={settings.max_daily_loss}
                    onChange={(e) => updateSetting('max_daily_loss', parseFloat(e.target.value))}
                    className="w-full h-2 bg-[#0a0a1a] rounded-lg appearance-none cursor-pointer accent-yellow-500"
                  />
                </div>

                {/* Max Drawdown */}
                <div>
                  <div className="flex items-center justify-between mb-1">
                    <label className="text-sm font-medium text-gray-400">Max Drawdown</label>
                    <span className="text-lg font-bold text-orange-400">
                      {settings.max_drawdown}%
                    </span>
                  </div>
                  <input
                    type="range"
                    min="5"
                    max="50"
                    step="1"
                    value={settings.max_drawdown}
                    onChange={(e) => updateSetting('max_drawdown', parseFloat(e.target.value))}
                    className="w-full h-2 bg-[#0a0a1a] rounded-lg appearance-none cursor-pointer accent-orange-500"
                  />
                </div>
              </div>

              {/* Max Positions */}
              <div>
                <div className="flex items-center justify-between mb-1">
                  <label className="text-sm font-medium text-gray-400">Max Concurrent Positions</label>
                  <span className="text-lg font-bold text-[#6366f1]">
                    {settings.max_positions}
                  </span>
                </div>
                <input
                  type="range"
                  min="1"
                  max="20"
                  step="1"
                  value={settings.max_positions}
                  onChange={(e) => updateSetting('max_positions', parseInt(e.target.value))}
                  className="w-full h-2 bg-[#0a0a1a] rounded-lg appearance-none cursor-pointer accent-[#6366f1]"
                />
                <div className="flex justify-between mt-1 text-xs text-gray-500">
                  <span>Fewer positions</span>
                  <span>More positions</span>
                </div>
              </div>

              {/* Risk Per Trade */}
              <div>
                <div className="flex items-center justify-between mb-1">
                  <label className="text-sm font-medium text-gray-400">Risk Per Trade</label>
                  <span className="text-lg font-bold text-purple-400">
                    {settings.risk_per_trade}%
                  </span>
                </div>
                <input
                  type="range"
                  min="0.5"
                  max="5"
                  step="0.5"
                  value={settings.risk_per_trade}
                  onChange={(e) => updateSetting('risk_per_trade', parseFloat(e.target.value))}
                  className="w-full h-2 bg-[#0a0a1a] rounded-lg appearance-none cursor-pointer accent-purple-500"
                />
                <div className="flex justify-between mt-1 text-xs text-gray-500">
                  <span>Lower risk</span>
                  <span>Higher risk</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Symbols Tab */}
      {activeTab === 'symbols' && (
        <div className="space-y-6">
          <div className="bg-[#1a1a2e] rounded-xl p-6 border border-[#2a2a4a]">
            <h3 className="mb-4 text-lg font-semibold text-white">🪙 Trading Symbols</h3>
            
            <div className="space-y-3">
              <p className="text-sm text-gray-400">Select which symbols the AI should trade</p>
              
              <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-4">
                {availableSymbols.map((item) => (
                  <button
                    key={item.symbol}
                    onClick={() => {
                      const current = settings.symbols || [];
                      const newSymbols = current.includes(item.symbol)
                        ? current.filter(s => s !== item.symbol)
                        : [...current, item.symbol];
                      updateSetting('symbols', newSymbols);
                    }}
                    className={`flex items-center gap-2 px-4 py-3 rounded-lg border transition ${
                      settings.symbols?.includes(item.symbol)
                        ? 'border-[#6366f1] bg-[#6366f1]/10 text-white'
                        : 'border-[#2a2a4a] text-gray-400 hover:border-[#3a3a5a]'
                    }`}
                  >
                    <span className="text-lg">{item.icon}</span>
                    <div className="text-left">
                      <span className="text-sm font-medium">{item.symbol}</span>
                      <span className="block text-xs text-gray-500">{item.name}</span>
                    </div>
                    {settings.symbols?.includes(item.symbol) && (
                      <CheckCircle className="w-4 h-4 text-[#6366f1] ml-auto" />
                    )}
                  </button>
                ))}
              </div>

              <div className="mt-4 p-3 bg-[#0a0a1a] rounded-lg">
                <p className="text-xs text-gray-500">
                  <span className="font-medium">Selected:</span> {settings.symbols?.join(', ') || 'None'}
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Performance Tab */}
      {activeTab === 'performance' && (
        <div className="space-y-6">
          <div className="bg-[#1a1a2e] rounded-xl p-6 border border-[#2a2a4a]">
            <h3 className="mb-4 text-lg font-semibold text-white">📊 AI Performance</h3>
            
            <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
              <PerformanceCard
                label="Total Trades"
                value={performance?.total_trades || 0}
                icon={<Activity className="w-5 h-5 text-blue-400" />}
              />
              <PerformanceCard
                label="Win Rate"
                value={`${performance?.win_rate || 0}%`}
                icon={<Target className="w-5 h-5 text-purple-400" />}
                positive={(performance?.win_rate || 0) >= 50}
              />
              <PerformanceCard
                label="Total P&L"
                value={`$${(performance?.total_pnl || 0).toFixed(2)}`}
                icon={<DollarSign className="w-5 h-5 text-green-400" />}
                positive={(performance?.total_pnl || 0) >= 0}
              />
              <PerformanceCard
                label="Best Trade"
                value={`$${(performance?.best_trade || 0).toFixed(2)}`}
                icon={<Award className="w-5 h-5 text-yellow-400" />}
                positive={true}
              />
            </div>

            <div className="grid grid-cols-2 gap-4 mt-4 md:grid-cols-2">
              <div className="bg-[#0a0a1a] rounded-lg p-4 border border-[#2a2a4a]">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-400">Winning Trades</span>
                  <span className="font-bold text-green-400">{performance?.winning_trades || 0}</span>
                </div>
              </div>
              <div className="bg-[#0a0a1a] rounded-lg p-4 border border-[#2a2a4a]">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-400">Losing Trades</span>
                  <span className="font-bold text-red-400">{performance?.losing_trades || 0}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

const TabButton: React.FC<{
  active: boolean;
  onClick: () => void;
  icon: React.ReactNode;
  label: string;
}> = ({ active, onClick, icon, label }) => (
  <button
    onClick={onClick}
    className={`flex items-center gap-2 px-4 py-2 rounded-lg transition whitespace-nowrap ${
      active
        ? 'bg-[#6366f1]/20 text-[#6366f1] border border-[#6366f1]/30'
        : 'text-gray-400 hover:text-white hover:bg-[#2a2a4a]'
    }`}
  >
    {icon}
    <span className="text-sm font-medium">{label}</span>
  </button>
);

const PerformanceCard: React.FC<{
  label: string;
  value: string | number;
  icon: React.ReactNode;
  positive?: boolean;
}> = ({ label, value, icon, positive }) => (
  <div className="bg-[#0a0a1a] rounded-lg p-4 border border-[#2a2a4a]">
    <div className="flex items-center justify-between mb-1">
      <span className="text-xs text-gray-400">{label}</span>
      <div className="p-1.5 bg-[#6366f1]/10 rounded-lg">
        {icon}
      </div>
    </div>
    <p className={`text-xl font-bold ${positive !== undefined ? (positive ? 'text-green-400' : 'text-red-400') : 'text-white'}`}>
      {value}
    </p>
  </div>
);

export default AISettingsPage;