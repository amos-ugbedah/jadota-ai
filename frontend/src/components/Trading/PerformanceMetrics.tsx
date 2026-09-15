import React from 'react';
import { 
  TrendingUp, TrendingDown, DollarSign, 
  Award, Target, Zap, Activity, BarChart3,
  CheckCircle, XCircle, Percent
} from 'lucide-react';

interface PerformanceMetricsProps {
  data: {
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
  isLoading: boolean;
}

const PerformanceMetrics: React.FC<PerformanceMetricsProps> = ({ data, isLoading }) => {
  if (isLoading) {
    return (
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        {[...Array(8)].map((_, i) => (
          <div key={i} className="bg-[#1a1a2e] rounded-xl p-4 border border-[#2a2a4a] animate-pulse">
            <div className="w-20 h-4 mb-2 bg-gray-700 rounded"></div>
            <div className="w-16 h-6 bg-gray-700 rounded"></div>
          </div>
        ))}
      </div>
    );
  }

  const metrics = [
    {
      label: 'Total P&L',
      value: `$${data.total_pnl.toFixed(2)}`,
      icon: <DollarSign className="w-4 h-4" />,
      color: data.total_pnl >= 0 ? 'text-green-400' : 'text-red-400',
      bg: data.total_pnl >= 0 ? 'bg-green-500/10' : 'bg-red-500/10',
    },
    {
      label: 'Win Rate',
      value: `${data.win_rate.toFixed(1)}%`,
      icon: <Target className="w-4 h-4" />,
      color: data.win_rate >= 60 ? 'text-green-400' : data.win_rate >= 40 ? 'text-yellow-400' : 'text-red-400',
      bg: 'bg-blue-500/10',
    },
    {
      label: 'Total Trades',
      value: data.total_trades.toString(),
      icon: <Activity className="w-4 h-4" />,
      color: 'text-white',
      bg: 'bg-purple-500/10',
    },
    {
      label: 'Profit Factor',
      value: data.profit_factor.toFixed(2),
      icon: <Zap className="w-4 h-4" />,
      color: data.profit_factor >= 1.5 ? 'text-green-400' : 'text-yellow-400',
      bg: 'bg-orange-500/10',
    },
    {
      label: 'Best Trade',
      value: `$${data.best_trade.toFixed(2)}`,
      icon: <TrendingUp className="w-4 h-4" />,
      color: 'text-green-400',
      bg: 'bg-green-500/10',
    },
    {
      label: 'Worst Trade',
      value: `$${data.worst_trade.toFixed(2)}`,
      icon: <TrendingDown className="w-4 h-4" />,
      color: 'text-red-400',
      bg: 'bg-red-500/10',
    },
    {
      label: 'Winning Trades',
      value: `${data.winning_trades} / ${data.total_trades}`,
      icon: <CheckCircle className="w-4 h-4" />,
      color: 'text-green-400',
      bg: 'bg-green-500/10',
    },
    {
      label: 'Avg Win/Loss',
      value: `${data.avg_win.toFixed(2)} / ${data.avg_loss.toFixed(2)}`,
      icon: <BarChart3 className="w-4 h-4" />,
      color: data.avg_win > Math.abs(data.avg_loss) ? 'text-green-400' : 'text-red-400',
      bg: 'bg-cyan-500/10',
    },
  ];

  return (
    <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
      {metrics.map((metric, index) => (
        <div
          key={index}
          className={`${metric.bg} rounded-xl p-4 border border-[#2a2a4a] hover:border-[#6366f1]/30 transition`}
        >
          <div className="flex items-center justify-between mb-1">
            <span className="text-xs text-gray-400">{metric.label}</span>
            <div className={`${metric.bg} p-1 rounded-lg`}>
              {metric.icon}
            </div>
          </div>
          <p className={`text-xl font-bold ${metric.color}`}>{metric.value}</p>
        </div>
      ))}
    </div>
  );
};

export default PerformanceMetrics;