import React from 'react';
import { useAuthStore } from '@/store/authStore';
import { TrendingUp, TrendingDown, Wallet, Activity, ArrowUpRight } from 'lucide-react';

const Dashboard: React.FC = () => {
  const { user } = useAuthStore();

  return (
    <div className="p-6 space-y-6">
      {/* Welcome Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white">
            Welcome back, {user?.fullName || 'User'} 👋
          </h1>
          <p className="mt-1 text-gray-400">
            Here's what's happening with your portfolio
          </p>
        </div>
        <button className="px-4 py-2 bg-[#6366f1] text-white rounded-lg hover:bg-[#4f46e5] transition font-medium">
          Start Trading
        </button>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          title="Total Balance"
          value="$0.00"
          icon={<Wallet className="w-5 h-5 text-[#6366f1]" />}
          change="+0%"
        />
        <StatCard
          title="Open Positions"
          value="0"
          icon={<Activity className="w-5 h-5 text-blue-400" />}
          change="No positions"
        />
        <StatCard
          title="Today's P&L"
          value="$0.00"
          icon={<TrendingUp className="w-5 h-5 text-green-400" />}
          change="+0%"
          positive={true}
        />
        <StatCard
          title="AI Status"
          value="Active"
          icon={<div className="w-2.5 h-2.5 bg-green-400 rounded-full animate-pulse" />}
          change="24/7 Monitoring"
        />
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <div className="lg:col-span-2 bg-[#1a1a2e] rounded-xl p-6 border border-[#2a2a4a]">
          <h3 className="mb-4 text-lg font-semibold text-white">Recent Activity</h3>
          <div className="text-sm text-gray-400">
            No recent trades. Start trading to see activity here.
          </div>
        </div>
        <div className="bg-[#1a1a2e] rounded-xl p-6 border border-[#2a2a4a]">
          <h3 className="mb-4 text-lg font-semibold text-white">Quick Stats</h3>
          <div className="space-y-3 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-400">Subscription</span>
              <span className="font-medium text-white">Inactive</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Demo Balance</span>
              <span className="font-medium text-white">$1,000.00</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Role</span>
              <span className="font-medium text-white">{user?.role || 'User'}</span>
            </div>
          </div>
          <button className="mt-4 w-full px-4 py-2 bg-[#6366f1] text-white rounded-lg hover:bg-[#4f46e5] transition font-medium">
            Upgrade Now
          </button>
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