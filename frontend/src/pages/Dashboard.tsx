import React, { useState, useEffect } from 'react';
import { useAuthStore } from '@/store/authStore';
import { useTradingStore } from '@/store/tradingStore';
import { Link } from 'react-router-dom';
import { TrendingUp, TrendingDown, Wallet, Activity, ArrowUpRight } from 'lucide-react';
import { format } from 'date-fns';

const Dashboard: React.FC = () => {
  const { user } = useAuthStore();
  const { positions, balance, fetchPositions, fetchBalance, isLoading } = useTradingStore();
  const [recentTrades, setRecentTrades] = useState<any[]>([]);
  const [stats, setStats] = useState({
    totalPnl: 0,
    winRate: 0,
    totalTrades: 0
  });

  useEffect(() => {
    fetchPositions();
    fetchBalance();
    fetchPerformance();
    fetchRecentTrades();
  }, []);

  const fetchPerformance = async () => {
    try {
      // In production, fetch from API
      // const response = await tradingApi.getPerformance();
      // setStats(response);
    } catch (error) {
      console.error('Failed to fetch performance:', error);
    }
  };

  const fetchRecentTrades = async () => {
    try {
      // In production, fetch from API
      // const response = await tradingApi.getTradeHistory({ limit: 5 });
      // setRecentTrades(response);
    } catch (error) {
      console.error('Failed to fetch recent trades:', error);
    }
  };

  const totalPnl = positions.reduce((sum, p) => sum + (p.unrealizedPnl || 0), 0);
  const openPositions = positions.filter(p => p.status === 'OPEN');

  return (
    <div className="p-6 mx-auto space-y-6 max-w-7xl">
      {/* Welcome Header */}
      <div className="flex flex-col items-start justify-between gap-4 sm:flex-row sm:items-center">
        <div>
          <h1 className="text-3xl font-bold text-white">
            Welcome back, {user?.fullName || 'User'} 👋
          </h1>
          <p className="mt-1 text-gray-400">
            Here's what's happening with your portfolio
          </p>
        </div>
        <Link to="/trading">
          <button className="px-4 py-2 bg-[#6366f1] text-white rounded-lg hover:bg-[#4f46e5] transition font-medium flex items-center gap-2">
            <ArrowUpRight className="w-4 h-4" />
            Start Trading
          </button>
        </Link>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          title="Total Balance"
          value={`$${balance?.total?.toFixed(2) || '0.00'}`}
          icon={<Wallet className="w-5 h-5 text-[#6366f1]" />}
          change={balance?.total > 0 ? '+0%' : '$0.00'}
        />
        <StatCard
          title="Open Positions"
          value={openPositions.length.toString()}
          icon={<Activity className="w-5 h-5 text-blue-400" />}
          change={openPositions.length > 0 ? `${openPositions.length} active` : 'No positions'}
        />
        <StatCard
          title="Total P&L"
          value={`$${totalPnl.toFixed(2)}`}
          icon={totalPnl >= 0 ? 
            <TrendingUp className="w-5 h-5 text-green-400" /> : 
            <TrendingDown className="w-5 h-5 text-red-400" />
          }
          change={`${totalPnl >= 0 ? '+' : ''}${totalPnl.toFixed(2)}`}
          positive={totalPnl >= 0}
        />
        <StatCard
          title="AI Status"
          value={user?.subscription?.isActive ? '🟢 Active' : '⚪ Inactive'}
          icon={<div className={`w-2.5 h-2.5 ${user?.subscription?.isActive ? 'bg-green-400 animate-pulse' : 'bg-gray-400'} rounded-full`} />}
          change={user?.subscription?.isActive ? '24/7 Monitoring' : 'Subscribe to activate'}
        />
      </div>

      {/* Subscription Alert */}
      {!user?.subscription?.isActive && (
        <div className="flex flex-col items-center justify-between gap-4 p-4 border bg-yellow-500/10 border-yellow-500/30 rounded-xl sm:flex-row">
          <div>
            <p className="font-medium text-yellow-400">⚠️ Free Demo Mode</p>
            <p className="text-sm text-gray-400">You're using demo trading. Subscribe to unlock live trading!</p>
          </div>
          <Link to="/subscription">
            <button className="px-4 py-2 font-medium text-black transition bg-yellow-500 rounded-lg hover:bg-yellow-400">
              Upgrade Now
            </button>
          </Link>
        </div>
      )}

      {/* Quick Actions */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <div className="lg:col-span-2 bg-[#1a1a2e] rounded-xl p-6 border border-[#2a2a4a]">
          <h3 className="mb-4 text-lg font-semibold text-white">Recent Activity</h3>
          {recentTrades.length === 0 ? (
            <div className="py-8 text-center">
              <p className="text-sm text-gray-400">No recent trades</p>
              <Link to="/trading">
                <button className="mt-4 text-[#6366f1] hover:text-[#4f46e5] text-sm font-medium">
                  Start trading →
                </button>
              </Link>
            </div>
          ) : (
            <div className="space-y-3">
              {recentTrades.map((trade, index) => (
                <div key={index} className="flex justify-between items-center py-2 border-b border-[#2a2a4a] last:border-0">
                  <div>
                    <span className="font-medium text-white">{trade.symbol}</span>
                    <span className={`ml-2 text-sm ${trade.side === 'BUY' ? 'text-green-400' : 'text-red-400'}`}>
                      {trade.side}
                    </span>
                  </div>
                  <div className="text-right">
                    <span className="text-white">${trade.price?.toFixed(2)}</span>
                    <span className="ml-2 text-sm text-gray-400">{format(new Date(trade.executedAt), 'HH:mm')}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
        <div className="bg-[#1a1a2e] rounded-xl p-6 border border-[#2a2a4a]">
          <h3 className="mb-4 text-lg font-semibold text-white">Quick Stats</h3>
          <div className="space-y-3 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-400">Subscription</span>
              <span className={`font-medium ${user?.subscription?.isActive ? 'text-green-400' : 'text-yellow-400'}`}>
                {user?.subscription?.isActive ? '✅ Active' : 'Free Demo'}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Demo Balance</span>
              <span className="font-medium text-white">${user?.demoBalance?.toFixed(2) || '0.00'}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Role</span>
              <span className="font-medium text-white">{user?.role || 'User'}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Open Positions</span>
              <span className="font-medium text-white">{openPositions.length}</span>
            </div>
          </div>
          {!user?.subscription?.isActive && (
            <Link to="/subscription">
              <button className="mt-4 w-full px-4 py-2 bg-[#6366f1] text-white rounded-lg hover:bg-[#4f46e5] transition font-medium">
                Upgrade Now
              </button>
            </Link>
          )}
        </div>
      </div>
    </div>
  );
};

const StatCard: React.FC<{
  title: string;
  value: string;
  icon: React.ReactNode;
  change: string;
  positive?: boolean;
}> = ({ title, value, icon, change, positive = true }) => (
  <div className="bg-[#1a1a2e] rounded-xl p-6 border border-[#2a2a4a] hover:border-[#6366f1]/30 transition">
    <div className="flex items-start justify-between">
      <div>
        <p className="text-sm font-medium text-gray-400">{title}</p>
        <p className="mt-1 text-2xl font-bold text-white">{value}</p>
        <p className={`text-xs mt-2 ${positive ? 'text-green-400' : 'text-red-400'}`}>
          {positive ? '↑' : '↓'} {change}
        </p>
      </div>
      <div className="p-2.5 bg-[#6366f1]/10 rounded-lg">
        {icon}
      </div>
    </div>
  </div>
);

export default Dashboard;