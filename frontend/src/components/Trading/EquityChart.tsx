import React, { useState } from 'react';
import {
  LineChart,
  Line,
  Area,
  AreaChart,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts';
import { TrendingUp, TrendingDown, RefreshCw } from 'lucide-react';

interface EquityChartProps {
  data: { date: string; value: number }[];
  isLoading: boolean;
  timeframe?: '1d' | '1w' | '1m' | '3m' | 'all';
  onTimeframeChange?: (timeframe: '1d' | '1w' | '1m' | '3m' | 'all') => void;
}

const EquityChart: React.FC<EquityChartProps> = ({ 
  data, 
  isLoading,
  timeframe = '1m',
  onTimeframeChange 
}) => {
  const [selectedTimeframe, setSelectedTimeframe] = useState(timeframe);

  const handleTimeframeChange = (tf: '1d' | '1w' | '1m' | '3m' | 'all') => {
    setSelectedTimeframe(tf);
    if (onTimeframeChange) {
      onTimeframeChange(tf);
    }
  };

  const timeframes = [
    { label: '1D', value: '1d' },
    { label: '1W', value: '1w' },
    { label: '1M', value: '1m' },
    { label: '3M', value: '3m' },
    { label: 'ALL', value: 'all' },
  ];

  const formatTooltip = (value: number) => {
    return `$${value.toFixed(2)}`;
  };

  const formatDate = (date: string) => {
    const d = new Date(date);
    return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  };

  const startValue = data.length > 0 ? data[0]?.value || 0 : 0;
  const endValue = data.length > 0 ? data[data.length - 1]?.value || 0 : 0;
  const totalChange = endValue - startValue;
  const percentChange = startValue !== 0 ? (totalChange / startValue) * 100 : 0;
  const isPositive = totalChange >= 0;

  if (isLoading) {
    return (
      <div className="bg-[#1a1a2e] rounded-xl p-6 border border-[#2a2a4a]">
        <div className="flex items-center justify-between mb-4">
          <div className="w-32 h-6 bg-gray-700 rounded animate-pulse"></div>
          <div className="flex gap-2">
            {timeframes.map((tf, i) => (
              <div key={i} className="w-10 h-8 bg-gray-700 rounded animate-pulse"></div>
            ))}
          </div>
        </div>
        <div className="h-[300px] bg-gray-800/30 rounded-lg animate-pulse"></div>
      </div>
    );
  }

  if (data.length === 0) {
    return (
      <div className="bg-[#1a1a2e] rounded-xl p-6 border border-[#2a2a4a]">
        <div className="flex flex-col items-center justify-center h-[300px] text-gray-400">
          <p className="text-lg">No equity data yet</p>
          <p className="text-sm">Start trading to see your performance</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-[#1a1a2e] rounded-xl p-6 border border-[#2a2a4a]">
      {/* Header */}
      <div className="flex flex-col items-start justify-between gap-3 mb-4 sm:flex-row sm:items-center">
        <div>
          <h3 className="text-sm font-medium text-gray-400">Equity Curve</h3>
          <div className="flex items-center gap-3 mt-1">
            <span className="text-2xl font-bold text-white">
              ${endValue.toFixed(2)}
            </span>
            <span className={`text-sm font-medium ${isPositive ? 'text-green-400' : 'text-red-400'}`}>
              {isPositive ? '+' : ''}{totalChange.toFixed(2)} ({isPositive ? '+' : ''}{percentChange.toFixed(2)}%)
            </span>
          </div>
        </div>
        <div className="flex gap-1 bg-[#0a0a1a] rounded-lg p-1">
          {timeframes.map((tf) => (
            <button
              key={tf.value}
              onClick={() => handleTimeframeChange(tf.value as any)}
              className={`px-3 py-1.5 rounded-md text-xs font-medium transition ${
                selectedTimeframe === tf.value
                  ? 'bg-[#6366f1] text-white'
                  : 'text-gray-400 hover:text-white'
              }`}
            >
              {tf.label}
            </button>
          ))}
        </div>
      </div>

      {/* Chart */}
      <div className="h-[300px]">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data}>
            <defs>
              <linearGradient id="equityGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor={isPositive ? "#22c55e" : "#ef4444"} stopOpacity={0.3} />
                <stop offset="95%" stopColor={isPositive ? "#22c55e" : "#ef4444"} stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#2a2a4a" vertical={false} />
            <XAxis
              dataKey="date"
              tickFormatter={formatDate}
              stroke="#4a4a5a"
              fontSize={11}
              tickLine={false}
              axisLine={{ stroke: '#2a2a4a' }}
            />
            <YAxis
              tickFormatter={(v) => `$${v}`}
              stroke="#4a4a5a"
              fontSize={11}
              tickLine={false}
              axisLine={{ stroke: '#2a2a4a' }}
              domain={['auto', 'auto']}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: '#1a1a2e',
                border: '1px solid #2a2a4a',
                borderRadius: '8px',
                padding: '12px',
              }}
              labelStyle={{ color: '#9ca3af', fontSize: '12px' }}
              formatter={(value: any) => [`$${Number(value).toFixed(2)}`, 'Equity']}
              labelFormatter={(label) => formatDate(label)}
            />
            <ReferenceLine
              y={startValue}
              stroke="#4a4a5a"
              strokeDasharray="5 5"
              label={{ value: 'Start', fill: '#4a4a5a', fontSize: 10 }}
            />
            <Area
              type="monotone"
              dataKey="value"
              stroke={isPositive ? "#22c55e" : "#ef4444"}
              strokeWidth={2}
              fill="url(#equityGradient)"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default EquityChart;