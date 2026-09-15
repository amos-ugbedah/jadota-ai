import React, { useState, useEffect } from 'react';
import { useAuthStore } from '@/store/authStore';
import { dashboardApi } from '@/api/dashboard';
import { aiApi } from '@/api/ai';
import { marketApi } from '@/api/market';
import { toast } from 'react-hot-toast';
import {
  TrendingUp,
  TrendingDown,
  Wallet,
  Activity,
  Brain,
  RefreshCw,
  Loader2,
  DollarSign,
  Zap,
  Target,
  BarChart3,
  Clock,
  CheckCircle,
  XCircle,
  ArrowUpRight,
  ArrowDownRight,
} from 'lucide-react';
import EquityChart from '@/components/Trading/EquityChart';
import PerformanceMetrics from '@/components/Trading/PerformanceMetrics';

interface DashboardData {
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
  signals: Record<string, any>;
}

const TradingDashboard: React.FC = () => {
  const { user } = useAuthStore();
  const [data, setData] = useState<DashboardData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [equityData, setEquityData] = useState<{ date: string; value: number }[]>([]);
  const [lastUpdate, setLastUpdate] = useState<string>('');

  const fetchDashboardData = async () => {
    try {
      setIsRefreshing(true);
      
      // Fetch portfolio
      const portfolio = await aiApi.getPortfolio();
      
      // Fetch performance
      const performance = await aiApi.getPerformance();
      
      // Fetch trade history
      const tradeHistory = await aiApi.getTradeHistory();
      
      // Fetch market prices
      const marketPrices = await marketApi.getPrices();
      
      // Fetch AI signals
      const signals = await aiApi.analyzeAll();
      
      // Generate equity data from trade history
      const equity = generateEquityData(tradeHistory);
      
      setData({
        portfolio,
        performance,
        trade_history: tradeHistory,
        market_prices: marketPrices,
        signals,
      });
      
      setEquityData(equity);
      setLastUpdate(new Date().toLocaleTimeString());
      
    } catch (error: any) {
      toast.error(error.message || 'Failed to fetch dashboard data');
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  };

  const generateEquityData = (trades: any[]) => {
    if (!trades || trades.length === 0) {
      // Generate mock equity data for demo
      const mockData = [];
      let value = 10000;
      const now = new Date();
      for (let i = 30; i >= 0; i--) {
        const date = new Date(now);
        date.setDate(date.getDate() - i);
        value = value * (1 + (Math.random() - 0.45) * 0.02);
        mockData.push({
          date: date.toISOString().split('T')[0],
          value: Math.round(value * 100) / 100,
        });
      }
      return mockData;
    }
    
    // Build equity curve from actual trades
    const sortedTrades = [...trades].sort((a, b) => 
      new Date(a.closedAt || a.openedAt).getTime() - new Date(b.closedAt || b.openedAt).getTime()
    );
    
    let equity = 10000; // Starting capital
    const equityCurve = [];
    
    // Add starting point
    const startDate = new Date();
    startDate.setDate(startDate.getDate() - 30);
    equityCurve.push({
      date: startDate.toISOString().split('T')[0],
      value: equity,
    });
    
    for (const trade of sortedTrades) {
      equity += trade.pnl || 0;
      const date = new Date(trade.closedAt || trade.openedAt);
      equityCurve.push({
        date: date.toISOString().split('T')[0],
        value: Math.round(equity * 100) / 100,
      });
    }
    
    return equityCurve;
  };

  useEffect(() => {
    fetchDashboardData();
    const interval = setInterval(fetchDashboardData, 60000); // Auto-refresh every 60 seconds
    return () => clearInterval(interval);
  }, []);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <Loader2 className="w-12 h-12 text-[#6366f1] animate-spin mx-auto" />
          <p className="mt-4 text-gray-400">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  const totalValue = data?.portfolio?.total_value || 0;
  const totalPnl = data?.portfolio?.total_pnl || 0;
  const openPositions = data?.portfolio?.positions?.length || 0;
  const winRate = data?.performance?.win_rate || 0;
  const totalTrades = data?.performance?.total_trades || 0;
  const profitFactor = data?.performance?.profit_factor || 0;

  return (
    <div className="p-6 mx-auto space-y-6 max-w-7xl">
      {/* Header */}
      <div className="flex flex-col items-start justify-between gap-4 sm:flex-row sm:items-center">
        <div>
          <h1 className="text-3xl font-bold text-white">📊 Trading Dashboard</h1>
          <p className="mt-1 text-gray-400">
            Real-time overview of your AI trading performance
          </p>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-xs text-gray-500">
            Last update: {lastUpdate || 'N/A'}
          </span>
          <button
            onClick={fetchDashboardData}
            disabled={isRefreshing}
            className="flex items-center gap-2 px-4 py-2 bg-[#1a1a2e] border border-[#2a2a4a] rounded-lg text-white hover:bg-[#2a2a4a] transition disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 ${isRefreshing ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <SummaryCard
          title="Total Value"
          value={`$${totalValue.toFixed(2)}`}
          icon={<Wallet className="w-5 h-5 text-[#6366f1]" />}
          change={totalPnl >= 0 ? '+' : ''}
          subtext={`${totalPnl >= 0 ? '▲' : '▼'} $${Math.abs(totalPnl).toFixed(2)}`}
          positive={totalPnl >= 0}
        />
        <SummaryCard
          title="Open Positions"
          value={openPositions.toString()}
          icon={<Activity className="w-5 h-5 text-blue-400" />}
          change=""
          subtext={openPositions > 0 ? `${openPositions} active` : 'No positions'}
          positive={true}
        />
        <SummaryCard
          title="Win Rate"
          value={`${winRate.toFixed(1)}%`}
          icon={<Target className="w-5 h-5 text-purple-400" />}
          change=""
          subtext={`${totalTrades} total trades`}
          positive={winRate >= 50}
        />
        <SummaryCard
          title="Profit Factor"
          value={profitFactor.toFixed(2)}
          icon={<Zap className="w-5 h-5 text-orange-400" />}
          change=""
          subtext={profitFactor >= 1.5 ? '📈 Good' : '📉 Needs improvement'}
          positive={profitFactor >= 1.5}
        />
      </div>

      {/* Equity Chart */}
      <EquityChart 
        data={equityData} 
        isLoading={isLoading}
        onTimeframeChange={(tf) => {
          // In production, fetch data for different timeframes
          console.log('Timeframe changed:', tf);
        }}
      />

      {/* Performance Metrics */}
      <div className="bg-[#1a1a2e] rounded-xl p-6 border border-[#2a2a4a]">
        <h3 className="mb-4 text-lg font-semibold text-white">📈 Performance Metrics</h3>
        <PerformanceMetrics 
          data={data?.performance || {
            total_trades: 0,
            winning_trades: 0,
            losing_trades: 0,
            win_rate: 0,
            total_pnl: 0,
            avg_win: 0,
            avg_loss: 0,
            profit_factor: 0,
            best_trade: 0,
            worst_trade: 0,
          }}
          isLoading={isLoading}
        />
      </div>

      {/* Recent Trades */}
      <div className="bg-[#1a1a2e] rounded-xl p-6 border border-[#2a2a4a]">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-white">📋 Recent Trades</h3>
          <span className="text-xs text-gray-400">
            {data?.trade_history?.length || 0} total trades
          </span>
        </div>
        {data?.trade_history && data.trade_history.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-[#2a2a4a]">
                  <th className="px-4 py-3 text-xs font-medium tracking-wider text-left text-gray-400 uppercase">Symbol</th>
                  <th className="px-4 py-3 text-xs font-medium tracking-wider text-left text-gray-400 uppercase">Side</th>
                  <th className="px-4 py-3 text-xs font-medium tracking-wider text-left text-gray-400 uppercase">Entry</th>
                  <th className="px-4 py-3 text-xs font-medium tracking-wider text-left text-gray-400 uppercase">Exit</th>
                  <th className="px-4 py-3 text-xs font-medium tracking-wider text-left text-gray-400 uppercase">P&L</th>
                  <th className="px-4 py-3 text-xs font-medium tracking-wider text-left text-gray-400 uppercase">Reason</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#2a2a4a]">
                {data.trade_history.slice(0, 10).map((trade: any, index: number) => (
                  <tr key={index} className="hover:bg-[#0a0a1a]/50 transition">
                    <td className="px-4 py-3 font-medium text-white">{trade.symbol}</td>
                    <td className="px-4 py-3">
                      <span className={`text-xs px-2 py-1 rounded-full ${
                        trade.side === 'BUY' 
                          ? 'bg-green-500/20 text-green-400' 
                          : 'bg-red-500/20 text-red-400'
                      }`}>
                        {trade.side}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-gray-400">${trade.entryPrice?.toFixed(2)}</td>
                    <td className="px-4 py-3 text-gray-400">${trade.exitPrice?.toFixed(2)}</td>
                    <td className="px-4 py-3">
                      <span className={trade.pnl >= 0 ? 'text-green-400' : 'text-red-400'}>
                        ${trade.pnl?.toFixed(2)}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <span className={`text-xs px-2 py-1 rounded-full ${
                        trade.reason === 'TAKE_PROFIT' 
                          ? 'bg-green-500/20 text-green-400' 
                          : trade.reason === 'STOP_LOSS'
                            ? 'bg-red-500/20 text-red-400'
                            : 'bg-yellow-500/20 text-yellow-400'
                      }`}>
                        {trade.reason || 'Manual'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="py-8 text-center text-gray-400">
            <p>No trades yet</p>
            <p className="mt-1 text-sm">Start auto-trading to see your history here</p>
          </div>
        )}
      </div>
    </div>
  );
};

const SummaryCard: React.FC<{
  title: string;
  value: string;
  icon: React.ReactNode;
  change: string;
  subtext: string;
  positive: boolean;
}> = ({ title, value, icon, change, subtext, positive }) => (
  <div className="bg-[#1a1a2e] rounded-xl p-6 border border-[#2a2a4a] hover:border-[#6366f1]/30 transition">
    <div className="flex items-start justify-between">
      <div>
        <p className="text-sm font-medium text-gray-400">{title}</p>
        <p className="mt-1 text-2xl font-bold text-white">{value}</p>
        <p className={`text-xs mt-1 ${positive ? 'text-green-400' : 'text-red-400'}`}>
          {subtext}
        </p>
      </div>
      <div className="p-2.5 bg-[#6366f1]/10 rounded-lg">
        {icon}
      </div>
    </div>
  </div>
);

export default TradingDashboard;