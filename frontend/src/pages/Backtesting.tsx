import React, { useState } from 'react';
import { useAuthStore } from '@/store/authStore';
import { toast } from 'react-hot-toast';
import { 
  Play, BarChart3, TrendingUp, TrendingDown, 
  RefreshCw, Download, Calendar, DollarSign,
  Loader2, CheckCircle, XCircle, Clock
} from 'lucide-react';
import { format } from 'date-fns';

interface BacktestResult {
  id: string;
  symbol: string;
  startDate: string;
  endDate: string;
  initialCapital: number;
  finalCapital: number;
  totalReturn: number;
  winRate: number;
  profitFactor: number;
  maxDrawdown: number;
  sharpeRatio: number;
  totalTrades: number;
  winningTrades: number;
  losingTrades: number;
  status: 'PENDING' | 'RUNNING' | 'COMPLETED' | 'FAILED';
}

const Backtesting: React.FC = () => {
  const { user } = useAuthStore();
  const [isRunning, setIsRunning] = useState(false);
  const [selectedStrategy, setSelectedStrategy] = useState('trend');
  const [selectedSymbol, setSelectedSymbol] = useState('BTC/USDT');
  const [startDate, setStartDate] = useState('2024-01-01');
  const [endDate, setEndDate] = useState('2024-12-31');
  const [initialCapital, setInitialCapital] = useState(10000);
  const [results, setResults] = useState<BacktestResult | null>(null);
  const [history, setHistory] = useState<BacktestResult[]>([
    {
      id: '1',
      symbol: 'BTC/USDT',
      startDate: '2024-01-01',
      endDate: '2024-03-31',
      initialCapital: 10000,
      finalCapital: 12450,
      totalReturn: 24.5,
      winRate: 68.2,
      profitFactor: 2.1,
      maxDrawdown: -8.3,
      sharpeRatio: 1.8,
      totalTrades: 142,
      winningTrades: 97,
      losingTrades: 45,
      status: 'COMPLETED'
    },
    {
      id: '2',
      symbol: 'ETH/USDT',
      startDate: '2024-04-01',
      endDate: '2024-06-30',
      initialCapital: 10000,
      finalCapital: 11890,
      totalReturn: 18.9,
      winRate: 61.5,
      profitFactor: 1.9,
      maxDrawdown: -12.1,
      sharpeRatio: 1.5,
      totalTrades: 98,
      winningTrades: 60,
      losingTrades: 38,
      status: 'COMPLETED'
    }
  ]);

  const runBacktest = async () => {
    setIsRunning(true);
    try {
      // In production, call API:
      // const response = await backtestApi.runBacktest({
      //   strategy: selectedStrategy,
      //   symbol: selectedSymbol,
      //   startDate,
      //   endDate,
      //   initialCapital
      // });
      
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      const mockResult: BacktestResult = {
        id: `bt-${Date.now()}`,
        symbol: selectedSymbol,
        startDate,
        endDate,
        initialCapital,
        finalCapital: initialCapital * (1 + (Math.random() * 0.5 - 0.1)),
        totalReturn: (Math.random() * 50) - 10,
        winRate: 50 + Math.random() * 30,
        profitFactor: 1 + Math.random() * 2,
        maxDrawdown: -(Math.random() * 20),
        sharpeRatio: 0.5 + Math.random() * 2,
        totalTrades: Math.floor(Math.random() * 200) + 50,
        winningTrades: 0,
        losingTrades: 0,
        status: 'COMPLETED'
      };
      mockResult.winningTrades = Math.floor(mockResult.totalTrades * (mockResult.winRate / 100));
      mockResult.losingTrades = mockResult.totalTrades - mockResult.winningTrades;
      
      setResults(mockResult);
      setHistory([mockResult, ...history]);
      toast.success('Backtest completed successfully!');
    } catch (error) {
      toast.error('Failed to run backtest');
    } finally {
      setIsRunning(false);
    }
  };

  return (
    <div className="p-6 mx-auto space-y-6 max-w-7xl">
      {/* Header */}
      <div className="flex flex-col items-start justify-between gap-4 sm:flex-row sm:items-center">
        <div>
          <h1 className="text-3xl font-bold text-white">Backtesting</h1>
          <p className="mt-1 text-gray-400">Test your strategies against historical data</p>
        </div>
        {user?.subscription?.isActive && (
          <span className="px-3 py-1 text-sm text-green-400 border rounded-full bg-green-500/20 border-green-500/30">
            ● Live Access
          </span>
        )}
      </div>

      {/* Backtest Configuration */}
      <div className="bg-[#1a1a2e] rounded-xl p-6 border border-[#2a2a4a]">
        <h3 className="mb-4 text-lg font-semibold text-white">Configuration</h3>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
          <div>
            <label className="block mb-1 text-sm font-medium text-gray-400">
              Strategy
            </label>
            <select
              value={selectedStrategy}
              onChange={(e) => setSelectedStrategy(e.target.value)}
              className="w-full px-3 py-2 bg-[#0a0a1a] border border-[#2a2a4a] rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-[#6366f1]"
            >
              <option value="trend">Trend Following</option>
              <option value="momentum">Momentum</option>
              <option value="mean-reversion">Mean Reversion</option>
              <option value="volatility">Volatility Breakout</option>
              <option value="consensus">AI Consensus</option>
            </select>
          </div>
          <div>
            <label className="block mb-1 text-sm font-medium text-gray-400">
              Symbol
            </label>
            <select
              value={selectedSymbol}
              onChange={(e) => setSelectedSymbol(e.target.value)}
              className="w-full px-3 py-2 bg-[#0a0a1a] border border-[#2a2a4a] rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-[#6366f1]"
            >
              <option value="BTC/USDT">BTC/USDT</option>
              <option value="ETH/USDT">ETH/USDT</option>
              <option value="SOL/USDT">SOL/USDT</option>
              <option value="BNB/USDT">BNB/USDT</option>
            </select>
          </div>
          <div>
            <label className="block mb-1 text-sm font-medium text-gray-400">
              Initial Capital ($)
            </label>
            <input
              type="number"
              value={initialCapital}
              onChange={(e) => setInitialCapital(parseFloat(e.target.value))}
              className="w-full px-3 py-2 bg-[#0a0a1a] border border-[#2a2a4a] rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-[#6366f1]"
            />
          </div>
          <div>
            <label className="block mb-1 text-sm font-medium text-gray-400">
              Start Date
            </label>
            <input
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              className="w-full px-3 py-2 bg-[#0a0a1a] border border-[#2a2a4a] rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-[#6366f1]"
            />
          </div>
          <div>
            <label className="block mb-1 text-sm font-medium text-gray-400">
              End Date
            </label>
            <input
              type="date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              className="w-full px-3 py-2 bg-[#0a0a1a] border border-[#2a2a4a] rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-[#6366f1]"
            />
          </div>
          <div className="flex items-end">
            <button
              onClick={runBacktest}
              disabled={isRunning}
              className="w-full px-4 py-2 bg-[#6366f1] text-white rounded-lg font-medium hover:bg-[#4f46e5] transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {isRunning ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Running...
                </>
              ) : (
                <>
                  <Play className="w-4 h-4" />
                  Run Backtest
                </>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Results */}
      {results && (
        <div className="bg-[#1a1a2e] rounded-xl p-6 border border-[#2a2a4a]">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-white">Results</h3>
            <button className="flex items-center gap-2 text-sm text-gray-400 hover:text-white">
              <Download className="w-4 h-4" />
              Export
            </button>
          </div>
          <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
            <MetricCard
              label="Final Capital"
              value={`$${results.finalCapital.toFixed(2)}`}
              icon={<DollarSign className="w-4 h-4 text-green-400" />}
            />
            <MetricCard
              label="Total Return"
              value={`${results.totalReturn.toFixed(2)}%`}
              icon={results.totalReturn >= 0 ? 
                <TrendingUp className="w-4 h-4 text-green-400" /> : 
                <TrendingDown className="w-4 h-4 text-red-400" />
              }
              positive={results.totalReturn >= 0}
            />
            <MetricCard
              label="Win Rate"
              value={`${results.winRate.toFixed(1)}%`}
              icon={<CheckCircle className="w-4 h-4 text-blue-400" />}
            />
            <MetricCard
              label="Sharpe Ratio"
              value={results.sharpeRatio.toFixed(2)}
              icon={<BarChart3 className="w-4 h-4 text-purple-400" />}
            />
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4 pt-4 border-t border-[#2a2a4a]">
            <MetricCard
              label="Total Trades"
              value={results.totalTrades.toString()}
              icon={<RefreshCw className="w-4 h-4 text-gray-400" />}
            />
            <MetricCard
              label="Winning Trades"
              value={results.winningTrades.toString()}
              icon={<CheckCircle className="w-4 h-4 text-green-400" />}
            />
            <MetricCard
              label="Losing Trades"
              value={results.losingTrades.toString()}
              icon={<XCircle className="w-4 h-4 text-red-400" />}
            />
            <MetricCard
              label="Max Drawdown"
              value={`${results.maxDrawdown.toFixed(2)}%`}
              icon={<TrendingDown className="w-4 h-4 text-red-400" />}
            />
          </div>
        </div>
      )}

      {/* History */}
      <div className="bg-[#1a1a2e] rounded-xl border border-[#2a2a4a] overflow-hidden">
        <div className="px-6 py-4 border-b border-[#2a2a4a]">
          <h3 className="text-lg font-semibold text-white">Backtest History</h3>
        </div>
        {history.length === 0 ? (
          <div className="p-8 text-center">
            <p className="text-gray-400">No backtest history</p>
            <p className="mt-2 text-sm text-gray-500">Run your first backtest above</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-[#2a2a4a]">
                  <th className="px-6 py-3 text-xs font-medium tracking-wider text-left text-gray-400 uppercase">Symbol</th>
                  <th className="px-6 py-3 text-xs font-medium tracking-wider text-left text-gray-400 uppercase">Period</th>
                  <th className="px-6 py-3 text-xs font-medium tracking-wider text-left text-gray-400 uppercase">Return</th>
                  <th className="px-6 py-3 text-xs font-medium tracking-wider text-left text-gray-400 uppercase">Win Rate</th>
                  <th className="px-6 py-3 text-xs font-medium tracking-wider text-left text-gray-400 uppercase">Trades</th>
                  <th className="px-6 py-3 text-xs font-medium tracking-wider text-left text-gray-400 uppercase">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#2a2a4a]">
                {history.map((result) => (
                  <tr key={result.id} className="hover:bg-[#0a0a1a]/50 transition">
                    <td className="px-6 py-4 font-medium text-white">{result.symbol}</td>
                    <td className="px-6 py-4 text-sm text-gray-400">
                      {format(new Date(result.startDate), 'MMM d')} - {format(new Date(result.endDate), 'MMM d, yyyy')}
                    </td>
                    <td className={`px-6 py-4 font-medium ${result.totalReturn >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                      {result.totalReturn.toFixed(2)}%
                    </td>
                    <td className="px-6 py-4 text-white">{result.winRate.toFixed(1)}%</td>
                    <td className="px-6 py-4 text-gray-400">{result.totalTrades}</td>
                    <td className="px-6 py-4">
                      <span className="px-2 py-1 text-xs text-green-400 rounded-full bg-green-500/20">
                        ✅ Completed
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

const MetricCard: React.FC<{
  label: string;
  value: string;
  icon: React.ReactNode;
  positive?: boolean;
}> = ({ label, value, icon, positive = true }) => (
  <div className="bg-[#0a0a1a] rounded-lg p-4">
    <div className="flex items-center gap-2">
      {icon}
      <span className="text-sm text-gray-400">{label}</span>
    </div>
    <p className={`text-xl font-bold ${positive !== undefined ? (positive ? 'text-green-400' : 'text-red-400') : 'text-white'}`}>
      {value}
    </p>
  </div>
);

export default Backtesting;