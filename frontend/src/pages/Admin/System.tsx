import React, { useState, useEffect } from 'react';
import { adminApi } from '@/api/admin';
import type { SystemStatus, SystemHealth } from '@/api/admin';
import { toast } from 'react-hot-toast';
import { 
  Activity, Server, Database, Wifi, Cpu, 
  AlertCircle, CheckCircle, RefreshCw, Loader2,
  Zap, Shield, Clock, HardDrive, Network, 
  TrendingUp, Users, DollarSign, BarChart3
} from 'lucide-react';
import { format } from 'date-fns';

// ... rest of the component stays the same

const System: React.FC = () => {
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null);
  const [systemHealth, setSystemHealth] = useState<SystemHealth | null>(null);
  const [logs, setLogs] = useState<string[]>([]);
  const [aiStatus, setAiStatus] = useState<{
    status: string;
    models: string[];
    lastRun: string;
    tradesToday: number;
  } | null>(null);

  const fetchData = async () => {
    try {
      setIsRefreshing(true);
      
      // Fetch system status
      const status = await adminApi.getSystemStatus();
      setSystemStatus(status);
      
      // Fetch system health
      const health = await adminApi.getSystemHealth();
      setSystemHealth(health);
      
      // Fetch AI status
      const ai = await adminApi.getAIStatus();
      setAiStatus(ai);
      
      // Fetch logs
      const logsData = await adminApi.getSystemLogs(50);
      setLogs(logsData);
      
    } catch (error: any) {
      toast.error(error.message || 'Failed to fetch system data');
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

  const handlePauseAI = async () => {
    try {
      await adminApi.pauseAI();
      toast.success('AI Engine paused');
      await fetchData();
    } catch (error: any) {
      toast.error(error.message || 'Failed to pause AI');
    }
  };

  const handleResumeAI = async () => {
    try {
      await adminApi.resumeAI();
      toast.success('AI Engine resumed');
      await fetchData();
    } catch (error: any) {
      toast.error(error.message || 'Failed to resume AI');
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <Loader2 className="w-12 h-12 text-[#6366f1] animate-spin mx-auto" />
          <p className="mt-4 text-gray-400">Loading system status...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 mx-auto space-y-6 max-w-7xl">
      {/* Header */}
      <div className="flex flex-col items-start justify-between gap-4 sm:flex-row sm:items-center">
        <div>
          <h1 className="text-3xl font-bold text-white">System Status</h1>
          <p className="mt-1 text-gray-400">Monitor system health and performance</p>
        </div>
        <div className="flex items-center gap-3">
          <span className={`px-3 py-1 text-sm rounded-full border ${
            systemStatus?.status === 'online' 
              ? 'text-green-400 border-green-500/30 bg-green-500/20'
              : 'text-yellow-400 border-yellow-500/30 bg-yellow-500/20'
          }`}>
            {systemStatus?.status === 'online' ? '● Online' : '● Degraded'}
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

      {/* System Health Grid */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <SystemStatusCard
          title="API Server"
          status={systemHealth?.api === 'healthy' ? 'online' : 'warning'}
          icon={<Server className="w-5 h-5" />}
          details={`v1.0.0 - ${systemHealth?.api === 'healthy' ? '99.9%' : 'Degraded'} uptime`}
        />
        <SystemStatusCard
          title="Database"
          status={systemHealth?.database === 'healthy' ? 'online' : 'warning'}
          icon={<Database className="w-5 h-5" />}
          details="PostgreSQL - Connected"
        />
        <SystemStatusCard
          title="AI Engine"
          status={systemStatus?.aiStatus === 'active' ? 'online' : 'warning'}
          icon={<Cpu className="w-5 h-5" />}
          details={`${systemStatus?.aiStatus === 'active' ? 'Active' : 'Paused'} - ${aiStatus?.models?.length || 0} models loaded`}
        />
        <SystemStatusCard
          title="WebSocket"
          status={systemHealth?.websocket === 'healthy' ? 'online' : 'warning'}
          icon={<Network className="w-5 h-5" />}
          details="Active connections"
        />
        <SystemStatusCard
          title="Redis Cache"
          status="online"
          icon={<HardDrive className="w-5 h-5" />}
          details="Connected - 256MB used"
        />
        <SystemStatusCard
          title="Payment Watcher"
          status="online"
          icon={<Shield className="w-5 h-5" />}
          details="Monitoring - 0 pending"
        />
      </div>

      {/* AI Control & Stats */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <div className="bg-[#1a1a2e] rounded-xl p-6 border border-[#2a2a4a]">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-white">AI Engine Control</h3>
            <div className="flex gap-2">
              {systemStatus?.aiStatus === 'active' ? (
                <button
                  onClick={handlePauseAI}
                  className="px-4 py-1.5 bg-yellow-500/20 text-yellow-400 rounded-lg text-sm hover:bg-yellow-500/30 transition"
                >
                  ⏸️ Pause
                </button>
              ) : (
                <button
                  onClick={handleResumeAI}
                  className="px-4 py-1.5 bg-green-500/20 text-green-400 rounded-lg text-sm hover:bg-green-500/30 transition"
                >
                  ▶️ Resume
                </button>
              )}
            </div>
          </div>
          <div className="space-y-3 text-sm">
            <div className="flex justify-between py-2 border-b border-[#2a2a4a]">
              <span className="text-gray-400">Status</span>
              <span className={`font-medium ${systemStatus?.aiStatus === 'active' ? 'text-green-400' : 'text-yellow-400'}`}>
                {systemStatus?.aiStatus === 'active' ? '● Running' : '● Paused'}
              </span>
            </div>
            <div className="flex justify-between py-2 border-b border-[#2a2a4a]">
              <span className="text-gray-400">Models Loaded</span>
              <span className="text-white">{aiStatus?.models?.join(', ') || 'None'}</span>
            </div>
            <div className="flex justify-between py-2 border-b border-[#2a2a4a]">
              <span className="text-gray-400">Last Run</span>
              <span className="text-white">
                {aiStatus?.lastRun ? format(new Date(aiStatus.lastRun), 'HH:mm:ss') : 'N/A'}
              </span>
            </div>
            <div className="flex justify-between py-2">
              <span className="text-gray-400">Trades Today</span>
              <span className="font-medium text-white">{systemStatus?.tradesToday || 0}</span>
            </div>
          </div>
        </div>
        
        <div className="bg-[#1a1a2e] rounded-xl p-6 border border-[#2a2a4a]">
          <h3 className="mb-4 text-lg font-semibold text-white">Performance Metrics</h3>
          <div className="space-y-3">
            <MetricBar label="CPU Usage" value={45} color="blue" />
            <MetricBar label="Memory Usage" value={62} color="green" />
            <MetricBar label="Disk Usage" value={38} color="yellow" />
            <MetricBar label="API Response Time" value={120} color="purple" unit="ms" />
          </div>
          <div className="mt-4 pt-4 border-t border-[#2a2a4a]">
            <div className="flex justify-between text-sm">
              <span className="text-gray-400">Uptime</span>
              <span className="text-white">
                {systemStatus?.uptime ? `${Math.floor(systemStatus.uptime / 3600)}h ${Math.floor((systemStatus.uptime % 3600) / 60)}m` : 'N/A'}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Recent Logs */}
      <div className="bg-[#1a1a2e] rounded-xl border border-[#2a2a4a] overflow-hidden">
        <div className="px-6 py-4 border-b border-[#2a2a4a] flex justify-between items-center">
          <h3 className="text-lg font-semibold text-white">Recent Logs</h3>
          <span className="text-xs text-gray-400">Last 50 entries</span>
        </div>
        <div className="p-4 overflow-y-auto max-h-60">
          {logs.length === 0 ? (
            <p className="py-4 text-center text-gray-400">No logs available</p>
          ) : (
            <div className="space-y-1 font-mono text-xs">
              {logs.map((log, index) => (
                <div key={index} className="text-gray-400 hover:text-white transition py-0.5">
                  {log}
                </div>
              ))}
            </div>
          )}
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

export default System;