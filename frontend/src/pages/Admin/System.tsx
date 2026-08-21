import React, { useState } from 'react';
import { Activity, Server, Database, Wifi, Cpu, AlertCircle, CheckCircle, RefreshCw } from 'lucide-react';

const System: React.FC = () => {
  const [isRefreshing, setIsRefreshing] = useState(false);

  const handleRefresh = () => {
    setIsRefreshing(true);
    setTimeout(() => setIsRefreshing(false), 1000);
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white">System Status</h1>
          <p className="mt-1 text-gray-400">Monitor system health and performance</p>
        </div>
        <button 
          onClick={handleRefresh}
          className="flex items-center gap-2 px-4 py-2 bg-[#1a1a2e] border border-[#2a2a4a] rounded-lg text-white hover:bg-[#2a2a4a] transition"
        >
          <RefreshCw className={`w-4 h-4 ${isRefreshing ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      {/* Status Grid */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <SystemStatusCard
          title="API Server"
          status="online"
          icon={<Server className="w-5 h-5" />}
          details="v1.0.0 - 99.9% uptime"
        />
        <SystemStatusCard
          title="Database"
          status="online"
          icon={<Database className="w-5 h-5" />}
          details="PostgreSQL - Connected"
        />
        <SystemStatusCard
          title="AI Engine"
          status="online"
          icon={<Cpu className="w-5 h-5" />}
          details="Active - 4 models loaded"
        />
        <SystemStatusCard
          title="WebSocket"
          status="warning"
          icon={<Wifi className="w-5 h-5" />}
          details="Connecting - 0 clients"
        />
        <SystemStatusCard
          title="Redis Cache"
          status="online"
          icon={<Activity className="w-5 h-5" />}
          details="Connected - 256MB used"
        />
        <SystemStatusCard
          title="Payment Watcher"
          status="online"
          icon={<CheckCircle className="w-5 h-5" />}
          details="Monitoring - 0 pending"
        />
      </div>

      {/* System Metrics */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <div className="bg-[#1a1a2e] rounded-xl p-6 border border-[#2a2a4a]">
          <h3 className="mb-4 text-lg font-semibold text-white">Performance Metrics</h3>
          <div className="space-y-3">
            <MetricBar label="CPU Usage" value={45} color="blue" />
            <MetricBar label="Memory Usage" value={62} color="green" />
            <MetricBar label="Disk Usage" value={38} color="yellow" />
            <MetricBar label="API Response Time" value={120} color="purple" unit="ms" />
          </div>
        </div>
        <div className="bg-[#1a1a2e] rounded-xl p-6 border border-[#2a2a4a]">
          <h3 className="mb-4 text-lg font-semibold text-white">Recent Activity</h3>
          <div className="space-y-3">
            <ActivityItem time="5 min ago" message="User login: test@example.com" type="info" />
            <ActivityItem time="15 min ago" message="New subscription purchased" type="success" />
            <ActivityItem time="1 hour ago" message="AI trade executed: BTC/USDT +0.5%" type="success" />
            <ActivityItem time="2 hours ago" message="System backup completed" type="info" />
            <ActivityItem time="4 hours ago" message="WebSocket reconnected" type="warning" />
          </div>
        </div>
      </div>
    </div>
  );
};

const SystemStatusCard: React.FC<{
  title: string;
  status: 'online' | 'offline' | 'warning';
  icon: React.ReactNode;
  details: string;
}> = ({ title, status, icon, details }) => {
  const statusColors = {
    online: 'text-green-400 border-green-500/30 bg-green-500/10',
    offline: 'text-red-400 border-red-500/30 bg-red-500/10',
    warning: 'text-yellow-400 border-yellow-500/30 bg-yellow-500/10',
  };

  const statusDots = {
    online: 'bg-green-400',
    offline: 'bg-red-400',
    warning: 'bg-yellow-400 animate-pulse',
  };

  return (
    <div className={`rounded-xl p-6 border ${statusColors[status]}`}>
      <div className="flex items-center gap-3 mb-3">
        <div className="p-2 bg-[#0a0a1a] rounded-lg">
          {icon}
        </div>
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <span className="font-medium text-white">{title}</span>
            <span className={`w-2 h-2 rounded-full ${statusDots[status]}`}></span>
          </div>
          <p className="text-sm text-gray-400">{details}</p>
        </div>
      </div>
    </div>
  );
};

const MetricBar: React.FC<{
  label: string;
  value: number;
  color: 'blue' | 'green' | 'yellow' | 'purple' | 'red';
  unit?: string;
}> = ({ label, value, color, unit = '%' }) => {
  const colors = {
    blue: 'bg-blue-400',
    green: 'bg-green-400',
    yellow: 'bg-yellow-400',
    purple: 'bg-purple-400',
    red: 'bg-red-400',
  };

  return (
    <div>
      <div className="flex justify-between mb-1 text-sm">
        <span className="text-gray-400">{label}</span>
        <span className="font-medium text-white">{value}{unit}</span>
      </div>
      <div className="w-full bg-[#0a0a1a] rounded-full h-2">
        <div 
          className={`${colors[color]} rounded-full h-2 transition-all duration-500`}
          style={{ width: `${Math.min(value, 100)}%` }}
        ></div>
      </div>
    </div>
  );
};

const ActivityItem: React.FC<{
  time: string;
  message: string;
  type: 'info' | 'success' | 'warning' | 'error';
}> = ({ time, message, type }) => {
  const icons = {
    info: <AlertCircle className="w-4 h-4 text-blue-400" />,
    success: <CheckCircle className="w-4 h-4 text-green-400" />,
    warning: <AlertCircle className="w-4 h-4 text-yellow-400" />,
    error: <AlertCircle className="w-4 h-4 text-red-400" />,
  };

  return (
    <div className="flex items-center gap-3 py-2 border-b border-[#2a2a4a] last:border-0">
      {icons[type]}
      <div className="flex-1">
        <p className="text-sm text-gray-300">{message}</p>
        <p className="text-xs text-gray-500">{time}</p>
      </div>
    </div>
  );
};

export default System;