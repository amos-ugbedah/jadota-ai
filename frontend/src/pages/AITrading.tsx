import React, { useState, useEffect } from 'react';
import { aiApi } from '@/api/ai';
import type { AISignal } from '@/api/ai';
import { marketApi } from '@/api/market';
import { useAuthStore } from '@/store/authStore';
import { toast } from 'react-hot-toast';
import { 
  TrendingUp, TrendingDown, Minus, 
  RefreshCw, Brain, Activity, 
  Loader2, Sparkles, Play, Wallet
} from 'lucide-react';

const AITrading: React.FC = () => {
  const { user } = useAuthStore();
  const [signals, setSignals] = useState<Record<string, AISignal>>({});
  const [marketPrices, setMarketPrices] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [selectedSymbol, setSelectedSymbol] = useState<string | null>(null);
  const [aiStatus, setAiStatus] = useState<any>(null);
  const [isAutoTrading, setIsAutoTrading] = useState(false);
  const [portfolio, setPortfolio] = useState<any>(null);

  const symbols = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'BNB/USDT'];

  const fetchData = async () => {
    try {
      setIsRefreshing(true);
      
      const signalsData = await aiApi.analyzeAll();
      setSignals(signalsData);
      
      const prices = await marketApi.getPrices();
      setMarketPrices(prices);
      
      const status = await aiApi.getStatus();
      setAiStatus(status);
      
      // Fetch portfolio
      await fetchPortfolio();
      
    } catch (error: any) {
      toast.error(error.message || 'Failed to fetch AI signals');
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  };

  const fetchPortfolio = async () => {
    try {
      const data = await aiApi.getPortfolio();
      setPortfolio(data);
    } catch (error) {
      console.error('Failed to fetch portfolio:', error);
    }
  };

  const startAutoTrading = async () => {
    setIsAutoTrading(true);
    try {
      const response = await aiApi.startAutoTrading();
      toast.success(`✅ Executed ${response.trades?.length || 0} trades`);
      await fetchData();
    } catch (error: any) {
      toast.error(error.message || 'Failed to start auto-trading');
    } finally {
      setIsAutoTrading(false);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, []);

  const getSignalColor = (signal: string) => {
    switch(signal) {
      case 'BUY': return 'text-green-400';
      case 'SELL': return 'text-red-400';
      default: return 'text-yellow-400';
    }
  };

  const getSignalIcon = (signal: string) => {
    switch(signal) {
      case 'BUY': return <TrendingUp className="w-5 h-5 text-green-400" />;
      case 'SELL': return <TrendingDown className="w-5 h-5 text-red-400" />;
      default: return <Minus className="w-5 h-5 text-yellow-400" />;
    }
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 70) return 'text-green-400';
    if (confidence >= 50) return 'text-yellow-400';
    return 'text-red-400';
  };

  const getConfidenceBar = (confidence: number) => {
    const color = confidence >= 70 ? 'bg-green-400' : confidence >= 50 ? 'bg-yellow-400' : 'bg-red-400';
    return (
      <div className="w-full bg-[#0a0a1a] rounded-full h-1.5">
        <div 
          className={`${color} rounded-full h-1.5 transition-all duration-500`}
          style={{ width: `${confidence}%` }}
        />
      </div>
    );
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <Loader2 className="w-12 h-12 text-[#6366f1] animate-spin mx-auto" />
          <p className="mt-4 text-gray-400">Loading AI signals...</p>
        </div>
      </div>
    );
  }

  const hasPositions = portfolio?.positions?.length > 0;

  return (
    <div className="p-6 mx-auto space-y-6 max-w-7xl">
      {/* Header */}
      <div className="flex flex-col items-start justify-between gap-4 sm:flex-row sm:items-center">
        <div>
          <div className="flex items-center gap-3">
            <Brain className="w-8 h-8 text-[#6366f1]" />
            <h1 className="text-3xl font-bold text-white">AI Trading Intelligence</h1>
          </div>
          <p className="mt-1 text-gray-400">
            Real-time AI trading signals based on technical analysis
          </p>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 px-3 py-1.5 bg-[#1a1a2e] rounded-lg border border-[#2a2a4a]">
            <Activity className="w-4 h-4 text-green-400" />
            <span className="text-xs text-gray-400">
              {aiStatus?.symbols_analyzed || 0} symbols analyzed
            </span>
          </div>
          <button
            onClick={startAutoTrading}
            disabled={isAutoTrading}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg transition ${
              isAutoTrading 
                ? 'bg-yellow-500/20 text-yellow-400 border border-yellow-500/30 cursor-not-allowed'
                : 'bg-green-500/20 text-green-400 border border-green-500/30 hover:bg-green-500/30'
            }`}
          >
            {isAutoTrading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Trading...
              </>
            ) : (
              <>
                <Play className="w-4 h-4" />
                Auto-Trade
              </>
            )}
          </button>
          <button
            onClick={fetchData}
            disabled={isRefreshing}
            className="flex items-center gap-2 px-4 py-2 bg-[#1a1a2e] border border-[#2a2a4a] rounded-lg text-white hover:bg-[#2a2a4a] transition disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 ${isRefreshing ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        </div>
      </div>

      {/* AI Status */}
      <div className="bg-gradient-to-r from-[#1a1a2e] to-[#2a2a4a]/50 rounded-xl p-4 border border-[#2a2a4a]">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <Sparkles className="w-5 h-5 text-yellow-400" />
            <span className="font-medium text-white">AI Engine Status</span>
            <span className="px-2 py-0.5 bg-green-500/20 text-green-400 rounded-full text-xs">
              ● Active
            </span>
          </div>
          <div className="flex items-center gap-4 text-sm">
            <span className="text-gray-400">
              Last update: {aiStatus?.last_update ? new Date(aiStatus.last_update).toLocaleTimeString() : 'N/A'}
            </span>
            <span className="text-gray-400">
              {Object.keys(signals).length} signals generated
            </span>
          </div>
        </div>
      </div>

      {/* Signals Grid */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        {symbols.map((symbol) => {
          const signal = signals[symbol];
          const price = marketPrices.find(p => p.symbol === symbol);
          
          if (!signal) return null;
          
          return (
            <SignalCard
              key={symbol}
              symbol={symbol}
              signal={signal}
              price={price}
              onSelect={() => setSelectedSymbol(symbol)}
              isSelected={selectedSymbol === symbol}
            />
          );
        })}
      </div>

      {/* Portfolio Section */}
      {(hasPositions || portfolio?.total_value > 0) && (
        <div className="bg-[#1a1a2e] rounded-xl p-6 border border-[#2a2a4a]">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <Wallet className="w-5 h-5 text-[#6366f1]" />
              <h3 className="text-lg font-semibold text-white">💰 AI Portfolio</h3>
            </div>
            <span className={`text-sm font-medium ${portfolio?.total_pnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
              P&L: ${portfolio?.total_pnl?.toFixed(2) || '0.00'}
            </span>
          </div>
          <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
            {portfolio?.positions?.map((pos: any) => (
              <div key={pos.id} className="bg-[#0a0a1a] rounded-lg p-4 border border-[#2a2a4a]">
                <div className="flex items-start justify-between">
                  <div>
                    <p className="font-semibold text-white">{pos.symbol}</p>
                    <p className={`text-sm ${pos.side === 'BUY' ? 'text-green-400' : 'text-red-400'}`}>
                      {pos.side} × {pos.size}
                    </p>
                    <p className="text-xs text-gray-500">
                      Entry: ${pos.entryPrice?.toFixed(2)}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="font-medium text-white">${pos.currentPrice?.toFixed(2)}</p>
                    <p className={`text-sm ${pos.unrealizedPnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                      ${pos.unrealizedPnl?.toFixed(2)}
                    </p>
                    <p className="text-xs text-gray-500">
                      Conf: {pos.aiConfidence}%
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Selected Symbol Detail */}
      {selectedSymbol && signals[selectedSymbol] && (
        <div className="bg-[#1a1a2e] rounded-xl p-6 border border-[#2a2a4a]">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-white">
              {selectedSymbol} - Detailed Analysis
            </h3>
            <button
              onClick={() => setSelectedSymbol(null)}
              className="text-gray-400 hover:text-white"
            >
              ✕
            </button>
          </div>
          
          <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
            <div>
              <h4 className="mb-3 text-sm font-medium text-gray-400">Technical Indicators</h4>
              <div className="space-y-2 text-sm">
                <IndicatorRow label="Close Price" value={`$${signal.indicators.close.toFixed(2)}`} />
                <IndicatorRow label="SMA (7)" value={`$${signal.indicators.sma_7.toFixed(2)}`} />
                <IndicatorRow label="SMA (25)" value={`$${signal.indicators.sma_25.toFixed(2)}`} />
                <IndicatorRow label="SMA (99)" value={`$${signal.indicators.sma_99.toFixed(2)}`} />
                <IndicatorRow label="EMA (12)" value={`$${signal.indicators.ema_12.toFixed(2)}`} />
                <IndicatorRow label="EMA (26)" value={`$${signal.indicators.ema_26.toFixed(2)}`} />
                <IndicatorRow label="RSI" value={signal.indicators.rsi.toFixed(2)} />
                <IndicatorRow label="MACD" value={signal.indicators.macd.toFixed(4)} />
                <IndicatorRow label="MACD Signal" value={signal.indicators.macd_signal.toFixed(4)} />
              </div>
            </div>
            
            <div>
              <h4 className="mb-3 text-sm font-medium text-gray-400">Bollinger Bands</h4>
              <div className="space-y-2 text-sm">
                <IndicatorRow label="Upper Band" value={`$${signal.indicators.bb_upper.toFixed(2)}`} />
                <IndicatorRow label="Middle Band" value={`$${signal.indicators.bb_middle.toFixed(2)}`} />
                <IndicatorRow label="Lower Band" value={`$${signal.indicators.bb_lower.toFixed(2)}`} />
                <div className="mt-4 p-3 bg-[#0a0a1a] rounded-lg">
                  <p className="text-xs text-gray-400">
                    <span className="font-medium">AI Reasoning:</span> {signal.reasoning}
                  </p>
                  <p className="mt-2 text-xs text-gray-400">
                    <span className="font-medium">Risk/Reward:</span> {signal.risk_reward}:1
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

const SignalCard: React.FC<{
  symbol: string;
  signal: AISignal;
  price?: any;
  onSelect: () => void;
  isSelected: boolean;
}> = ({ symbol, signal, price, onSelect, isSelected }) => {
  const getSignalBg = (signal: string) => {
    switch(signal) {
      case 'BUY': return 'border-green-500/30 bg-green-500/5';
      case 'SELL': return 'border-red-500/30 bg-red-500/5';
      default: return 'border-yellow-500/30 bg-yellow-500/5';
    }
  };

  return (
    <div 
      className={`bg-[#1a1a2e] rounded-xl p-6 border transition cursor-pointer hover:border-[#6366f1]/50 ${
        isSelected ? 'border-[#6366f1]' : 'border-[#2a2a4a]'
      } ${getSignalBg(signal.signal)}`}
      onClick={onSelect}
    >
      <div className="flex items-start justify-between">
        <div>
          <p className="text-lg font-bold text-white">{symbol}</p>
          <p className="text-2xl font-bold text-white">
            ${price?.price?.toFixed(2) || signal.indicators.close.toFixed(2)}
          </p>
          <div className="flex items-center gap-2 mt-1">
            <span className="text-xs text-gray-400">
              {price?.change24h ? `${price.change24h >= 0 ? '+' : ''}${price.change24h.toFixed(2)}%` : '--'}
            </span>
          </div>
        </div>
        <div className="text-right">
          <div className="flex items-center justify-end gap-2">
            {getSignalIcon(signal.signal)}
            <span className={`text-xl font-bold ${getSignalColor(signal.signal)}`}>
              {signal.signal}
            </span>
          </div>
          <div className="mt-2">
            <span className={`text-sm font-medium ${getConfidenceColor(signal.confidence)}`}>
              {signal.confidence}% confidence
            </span>
          </div>
          <div className="w-24 mt-1 ml-auto">
            {getConfidenceBar(signal.confidence)}
          </div>
        </div>
      </div>
      
      <div className="mt-3 pt-3 border-t border-[#2a2a4a]">
        <p className="text-xs text-gray-400 line-clamp-2">
          {signal.reasoning}
        </p>
        <div className="flex items-center gap-4 mt-2 text-xs text-gray-500">
          <span>Risk/Reward: {signal.risk_reward}:1</span>
          <span>•</span>
          <span>RSI: {signal.indicators.rsi.toFixed(2)}</span>
        </div>
      </div>
    </div>
  );
};

const IndicatorRow: React.FC<{ label: string; value: string }> = ({ label, value }) => (
  <div className="flex justify-between py-1 border-b border-[#2a2a4a] last:border-0">
    <span className="text-gray-400">{label}</span>
    <span className="font-mono text-white">{value}</span>
  </div>
);

export default AITrading;