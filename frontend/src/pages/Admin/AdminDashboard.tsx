import React from 'react';
import { useAuthStore } from '@/store/authStore';
import { Users, Crown, Activity, TrendingUp, DollarSign, BarChart3 } from 'lucide-react';

const AdminDashboard: React.FC = () => {
  const { user } = useAuthStore();

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white">Admin Dashboard</h1>
          <p className="mt-1 text-gray-400">Welcome back, {user?.fullName || 'Admin'} 👋</p>
        </div>
        <div className="flex gap-3">
          <span className="px-3 py-1 text-sm text-green-400 border rounded-full bg-green-500/20 border-green-500/30">
            ● System Online
          </span>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <AdminStatCard
          title="Total Users"
          value="1"
          icon={<Users className="w-5 h-5 text-blue-400" />}
          change="+0%"
        />
        <AdminStatCard
          title="Active Subscriptions"
          value="0"
          icon={<Crown className="w-5 h-5 text-yellow-400" />}
          change="No active"
        />
        <AdminStatCard
          title="Revenue"
          value="$0.00"
          icon={<DollarSign className="w-5 h-5 text-green-400" />}
          change="$0.00"
        />
        <AdminStatCard
          title="AI Status"
          value="Active"
          icon={<Activity className="w-5 h-5 text-purple-400" />}
          change="24/7"
        />
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <div className="bg-[#1a1a2e] rounded-xl p-6 border border-[#2a2a4a]">
          <h3 className="mb-4 text-lg font-semibold text-white">Trading Performance</h3>
          <div className="text-sm text-gray-400">
            <div className="flex justify-between py-2 border-b border-[#2a2a4a]">
              <span>Today's Trades</span>
              <span className="font-medium text-white">47</span>
            </div>
            <div className="flex justify-between py-2 border-b border-[#2a2a4a]">
              <span>Win Rate</span>
              <span className="font-medium text-green-400">65.5%</span>
            </div>
            <div className="flex justify-between py-2 border-b border-[#2a2a4a]">
              <span>Total P&L</span>
              <span className="font-medium text-green-400">+$1,250.00</span>
            </div>
            <div className="flex justify-between py-2">
              <span>Max Drawdown</span>
              <span className="font-medium text-red-400">-2.5%</span>
            </div>
          </div>
        </div>
        <div className="bg-[#1a1a2e] rounded-xl p-6 border border-[#2a2a4a]">
          <h3 className="mb-4 text-lg font-semibold text-white">System Health</h3>
          <div className="text-sm text-gray-400">
            <div className="flex justify-between py-2 border-b border-[#2a2a4a]">
              <span>API Status</span>
              <span className="font-medium text-green-400">● Healthy</span>
            </div>
            <div className="flex justify-between py-2 border-b border-[#2a2a4a]">
              <span>Database</span>
              <span className="font-medium text-green-400">● Connected</span>
            </div>
            <div className="flex justify-between py-2 border-b border-[#2a2a4a]">
              <span>AI Engine</span>
              <span className="font-medium text-green-400">● Running</span>
            </div>
            <div className="flex justify-between py-2">
              <span>WebSocket</span>
              <span className="font-medium text-yellow-400">● Connecting</span>
            </div>
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="bg-[#1a1a2e] rounded-xl p-6 border border-[#2a2a4a]">
        <h3 className="mb-4 text-lg font-semibold text-white">Quick Actions</h3>
        <div className="flex flex-wrap gap-3">
          <button className="px-4 py-2 text-blue-400 transition border rounded-lg bg-blue-500/20 border-blue-500/30 hover:bg-blue-500/30">
            View Users
          </button>
          <button className="px-4 py-2 text-purple-400 transition border rounded-lg bg-purple-500/20 border-purple-500/30 hover:bg-purple-500/30">
            Manage Subscriptions
          </button>
          <button className="px-4 py-2 text-green-400 transition border rounded-lg bg-green-500/20 border-green-500/30 hover:bg-green-500/30">
            System Status
          </button>
          <button className="px-4 py-2 text-red-400 transition border rounded-lg bg-red-500/20 border-red-500/30 hover:bg-red-500/30">
            View Logs
          </button>
        </div>
      </div>
    </div>
  );
};

const AdminStatCard: React.FC<{
  title: string;
  value: string;
  icon: React.ReactNode;
  change: string;
}> = ({ title, value, icon, change }) => (
  <div className="bg-[#1a1a2e] rounded-xl p-6 border border-[#2a2a4a] hover:border-[#6366f1]/30 transition">
    <div className="flex items-start justify-between">
      <div>
        <p className="text-sm font-medium text-gray-400">{title}</p>
        <p className="mt-1 text-2xl font-bold text-white">{value}</p>
        <p className="mt-2 text-xs text-gray-500">{change}</p>
      </div>
      <div className="p-2.5 bg-[#6366f1]/10 rounded-lg">
        {icon}
      </div>
    </div>
  </div>
);

export default AdminDashboard;