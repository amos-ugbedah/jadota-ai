import React, { useState, useEffect } from 'react';
import { useAuthStore } from '@/store/authStore';
import { adminApi } from '@/api/admin';
import type { SystemStatus, RevenueStats } from '@/api/admin';
import { Link } from 'react-router-dom';
import { 
  Users, Crown, Activity, TrendingUp, DollarSign, 
  RefreshCw, Loader2, CheckCircle, XCircle, 
  Shield, Server, Database, Cpu, BarChart3
} from 'lucide-react';
import { toast } from 'react-hot-toast';

const AdminDashboard: React.FC = () => {
  const { user } = useAuthStore();
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null);
  const [revenue, setRevenue] = useState<RevenueStats | null>(null);
  const [stats, setStats] = useState({
    totalUsers: 0,
    activeSubscriptions: 0,
    pendingSubscriptions: 0,
    tradesToday: 0,
    winRate: 0,
    totalPnl: 0
  });

  const fetchData = async () => {
    try {
      setIsRefreshing(true);
      
      const status = await adminApi.getSystemStatus();
      setSystemStatus(status);
      
      const revenueData = await adminApi.getRevenue('month');
      setRevenue(revenueData);
      
      const users = await adminApi.getUsers({ limit: 1 });
      setStats(prev => ({
        ...prev,
        totalUsers: users.length || 0
      }));
      
    } catch (error: any) {
      toast.error(error.message || 'Failed to fetch admin data');
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleRefresh = () => {
    fetchData();
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <Loader2 className="w-12 h-12 text-[#6366f1] animate-spin mx-auto" />
          <p className="mt-4 text-gray-400">Loading admin dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 mx-auto space-y-6 max-w-7xl">
      {/* Header */}
      <div className="flex flex-col items-start justify-between gap-4 sm:flex-row sm:items-center">
        <div>
          <h1 className="text-3xl font-bold text-white">Admin Dashboard</h1>
          <p className="mt-1 text-gray-400">
            Welcome back, {user?.fullName || 'Admin'} 👋
          </p>
        </div>
        <div className="flex items-center gap-3">
          <span className={`px-3 py-1 text-sm rounded-full border ${
            systemStatus?.status === 'online' 
              ? 'text-green-400 border-green-500/30 bg-green-500/20'
              : 'text-yellow-400 border-yellow-500/30 bg-yellow-500/20'
          }`}>
            {systemStatus?.status === 'online' ? '● System Online' : '● System Degraded'}
          </span>
          <button
            onClick={handleRefresh}
            disabled={isRefreshing}
            className="flex items-center gap-2 px-4 py-2 bg-[#1a1a2e] border border-[#2a2a4a] rounded-lg text-white hover:bg-[#2a2a4a] transition disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 ${isRefreshing ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <AdminStatCard
          title="Total Users"
          value={stats.totalUsers.toString()}
          icon={<Users className="w-5 h-5 text-blue-400" />}
          change={`+${stats.totalUsers > 0 ? '1' : '0'} this month`}
        />
        <AdminStatCard
          title="Active Subscriptions"
          value={stats.activeSubscriptions.toString()}
          icon={<Crown className="w-5 h-5 text-yellow-400" />}
          change={`${stats.activeSubscriptions > 0 ? 'Active' : 'No active'}`}
        />
        <AdminStatCard
          title="Monthly Revenue"
          value={`$${revenue?.monthly?.toFixed(2) || '0.00'}`}
          icon={<DollarSign className="w-5 h-5 text-green-400" />}
          change={`$${revenue?.pending?.toFixed(2) || '0.00'} pending`}
        />
        <AdminStatCard
          title="AI Status"
          value={systemStatus?.aiStatus === 'active' ? '🟢 Active' : '⏸️ Paused'}
          icon={<Activity className="w-5 h-5 text-purple-400" />}
          change={`${systemStatus?.tradesToday || 0} trades today`}
        />
      </div>

      {/* Performance & Health */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <div className="bg-[#1a1a2e] rounded-xl p-6 border border-[#2a2a4a]">
          <h3 className="mb-4 text-lg font-semibold text-white">Trading Performance</h3>
          <div className="space-y-3 text-sm">
            <div className="flex justify-between items-center py-2 border-b border-[#2a2a4a]">
              <span className="text-gray-400">Today's Trades</span>
              <span className="font-medium text-white">{systemStatus?.tradesToday || 0}</span>
            </div>
            <div className="flex justify-between items-center py-2 border-b border-[#2a2a4a]">
              <span className="text-gray-400">Win Rate</span>
              <span className={`font-medium ${(systemStatus?.winRate || 0) >= 50 ? 'text-green-400' : 'text-red-400'}`}>
                {(systemStatus?.winRate || 0).toFixed(1)}%
              </span>
            </div>
            <div className="flex justify-between items-center py-2 border-b border-[#2a2a4a]">
              <span className="text-gray-400">Total P&L</span>
              <span className={`font-medium ${(systemStatus?.pl || 0) >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                ${(systemStatus?.pl || 0).toFixed(2)}
              </span>
            </div>
            <div className="flex items-center justify-between py-2">
              <span className="text-gray-400">Max Drawdown</span>
              <span className="font-medium text-red-400">
                {(systemStatus?.drawdown || 0).toFixed(2)}%
              </span>
            </div>
          </div>
        </div>
        
        <div className="bg-[#1a1a2e] rounded-xl p-6 border border-[#2a2a4a]">
          <h3 className="mb-4 text-lg font-semibold text-white">System Health</h3>
          <div className="space-y-3 text-sm">
            <SystemHealthItem
              label="API Server"
              status="healthy"
              icon={<Server className="w-4 h-4" />}
            />
            <SystemHealthItem
              label="Database"
              status="healthy"
              icon={<Database className="w-4 h-4" />}
            />
            <SystemHealthItem
              label="AI Engine"
              status={systemStatus?.aiStatus === 'active' ? 'healthy' : 'warning'}
              icon={<Cpu className="w-4 h-4" />}
            />
            <SystemHealthItem
              label="WebSocket"
              status="healthy"
              icon={<Activity className="w-4 h-4" />}
            />
            <SystemHealthItem
              label="Payment Watcher"
              status="healthy"
              icon={<Shield className="w-4 h-4" />}
            />
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="bg-[#1a1a2e] rounded-xl p-6 border border-[#2a2a4a]">
        <h3 className="mb-4 text-lg font-semibold text-white">Quick Actions</h3>
        <div className="flex flex-wrap gap-3">
          <Link to="/admin/users">
            <button className="px-4 py-2 text-blue-400 transition border rounded-lg bg-blue-500/20 border-blue-500/30 hover:bg-blue-500/30">
              👥 View Users
            </button>
          </Link>
          <Link to="/admin/subscriptions">
            <button className="px-4 py-2 text-purple-400 transition border rounded-lg bg-purple-500/20 border-purple-500/30 hover:bg-purple-500/30">
              📋 Manage Subscriptions
            </button>
          </Link>
          <Link to="/admin/system">
            <button className="px-4 py-2 text-green-400 transition border rounded-lg bg-green-500/20 border-green-500/30 hover:bg-green-500/30">
              🖥️ System Status
            </button>
          </Link>
          <button className="px-4 py-2 text-yellow-400 transition border rounded-lg bg-yellow-500/20 border-yellow-500/30 hover:bg-yellow-500/30">
            📊 View Analytics
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

const SystemHealthItem: React.FC<{
  label: string;
  status: 'healthy' | 'warning' | 'error';
  icon: React.ReactNode;
}> = ({ label, status, icon }) => {
  const statusConfig = {
    healthy: { color: 'text-green-400', dot: 'bg-green-400', label: 'Healthy' },
    warning: { color: 'text-yellow-400', dot: 'bg-yellow-400 animate-pulse', label: 'Warning' },
    error: { color: 'text-red-400', dot: 'bg-red-400 animate-pulse', label: 'Error' }
  };
  
  const config = statusConfig[status];
  
  return (
    <div className="flex justify-between items-center py-2 border-b border-[#2a2a4a] last:border-0">
      <div className="flex items-center gap-2">
        <div className="text-gray-400">{icon}</div>
        <span className="text-gray-400">{label}</span>
      </div>
      <div className="flex items-center gap-2">
        <span className={`w-2 h-2 rounded-full ${config.dot}`}></span>
        <span className={`text-sm font-medium ${config.color}`}>{config.label}</span>
      </div>
    </div>
  );
};

export default AdminDashboard;