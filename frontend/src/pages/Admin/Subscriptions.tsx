import React, { useEffect, useState, useMemo } from 'react';
import {
  Crown,
  Users,
  DollarSign,
  TrendingUp,
  RefreshCw,
  Loader2,
  Search,
  CheckCircle,
  XCircle,
  Clock,
  Award,
  Mail,
} from 'lucide-react';
import { toast } from 'react-hot-toast';
import apiClient from '@/api/client';

// ============================================
// Types
// ============================================
interface AdminUser {
  id: string;
  email: string;
  fullName: string;
  role: string;
  subscription: {
    plan: string | null;
    isActive: boolean;
    expiresAt?: string | null;
  };
  demoBalance: number;
  createdAt: string;
}

type PlanFilter = 'all' | 'BASIC' | 'PRO' | 'ENTERPRISE';
type StatusFilter = 'all' | 'active' | 'inactive';

// Plan pricing (mirrors backend)
const PLAN_PRICING: Record<string, number> = {
  BASIC: 0,
  PRO: 29.99,
  ENTERPRISE: 99.99,
};

const PLAN_COLORS: Record<string, string> = {
  BASIC: 'bg-gray-500/20 text-gray-400 border-gray-500/30',
  PRO: 'bg-[#6366f1]/20 text-[#a5b4fc] border-[#6366f1]/40',
  ENTERPRISE: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
};

// ============================================
// Page
// ============================================
const AdminSubscriptions: React.FC = () => {
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [planFilter, setPlanFilter] = useState<PlanFilter>('all');
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('all');
  const [search, setSearch] = useState('');

  const load = async (silent = false) => {
    if (!silent) setLoading(true);
    else setRefreshing(true);
    try {
      const data = await apiClient.get<AdminUser[]>('/admin/users');
      setUsers(Array.isArray(data) ? data : []);
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || 'Failed to load subscriptions');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  // ============================================
  // Derived stats (from ALL users, before filters)
  // ============================================
  const stats = useMemo(() => {
    const totalUsers = users.length;

    const activeSubs = users.filter((u) => u.subscription?.isActive);
    const proCount = activeSubs.filter(
      (u) => (u.subscription?.plan || '').toUpperCase() === 'PRO'
    ).length;
    const enterpriseCount = activeSubs.filter(
      (u) => (u.subscription?.plan || '').toUpperCase() === 'ENTERPRISE'
    ).length;

    // Estimated monthly recurring revenue
    let mrr = 0;
    for (const u of activeSubs) {
      const plan = (u.subscription?.plan || '').toUpperCase();
      mrr += PLAN_PRICING[plan] || 0;
    }

    return {
      totalUsers,
      activeSubs: activeSubs.length,
      proCount,
      enterpriseCount,
      mrr,
    };
  }, [users]);

  // ============================================
  // Filtered list
  // ============================================
  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();

    return users
      .filter((u) => {
        // Plan filter (only count users WITH a subscription)
        if (planFilter !== 'all') {
          const plan = (u.subscription?.plan || '').toUpperCase();
          if (plan !== planFilter) return false;
        }

        // Status filter
        if (statusFilter === 'active' && !u.subscription?.isActive) return false;
        if (statusFilter === 'inactive' && u.subscription?.isActive) return false;

        // Search
        if (q) {
          const haystack = `${u.fullName} ${u.email}`.toLowerCase();
          if (!haystack.includes(q)) return false;
        }

        return true;
      })
      .sort((a, b) => {
        // Active subs first, then by creation date (newest first)
        if (a.subscription?.isActive !== b.subscription?.isActive) {
          return a.subscription?.isActive ? -1 : 1;
        }
        return new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime();
      });
  }, [users, planFilter, statusFilter, search]);

  // ============================================
  // Loading
  // ============================================
  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <Loader2 className="w-12 h-12 text-[#6366f1] animate-spin mx-auto" />
          <p className="mt-4 text-gray-400">Loading subscriptions...</p>
        </div>
      </div>
    );
  }

  // ============================================
  // Render
  // ============================================
  return (
    <div className="p-6 mx-auto space-y-6 max-w-7xl">
      {/* Header */}
      <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <h1 className="flex items-center gap-3 text-3xl font-bold text-white">
            <Crown className="w-8 h-8 text-yellow-400" />
            Subscriptions
          </h1>
          <p className="mt-1 text-gray-400">
            All user subscriptions, plans, and revenue
          </p>
        </div>

        <button
          onClick={() => load(true)}
          disabled={refreshing}
          className="flex items-center gap-2 px-4 py-2 bg-[#1a1a2e] border border-[#2a2a4a] rounded-lg text-gray-300 hover:text-white hover:border-[#3a3a5a] transition disabled:opacity-50 self-start"
        >
          <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-5">
        <StatCard
          label="Total Users"
          value={stats.totalUsers}
          icon={<Users className="w-5 h-5 text-blue-400" />}
        />
        <StatCard
          label="Active Subs"
          value={stats.activeSubs}
          icon={<CheckCircle className="w-5 h-5 text-green-400" />}
          tone="positive"
        />
        <StatCard
          label="Pro"
          value={stats.proCount}
          icon={<Award className="w-5 h-5 text-[#6366f1]" />}
        />
        <StatCard
          label="Enterprise"
          value={stats.enterpriseCount}
          icon={<Crown className="w-5 h-5 text-yellow-400" />}
        />
        <StatCard
          label="Est. MRR"
          value={`$${stats.mrr.toFixed(2)}`}
          icon={<DollarSign className="w-5 h-5 text-green-400" />}
          tone={stats.mrr > 0 ? 'positive' : 'neutral'}
        />
      </div>

      {/* Filters */}
      <div className="bg-[#1a1a2e] border border-[#2a2a4a] rounded-xl p-4 space-y-3">
        {/* Search */}
        <div className="relative">
          <Search className="absolute w-4 h-4 text-gray-500 -translate-y-1/2 left-3 top-1/2" />
          <input
            type="text"
            placeholder="Search by name or email…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-4 py-2 bg-[#0a0a1a] border border-[#2a2a4a] rounded-lg text-white text-sm placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-[#6366f1]"
          />
        </div>

        {/* Plan filter */}
        <div className="flex flex-wrap items-center gap-2">
          <span className="mr-1 text-xs tracking-wider text-gray-500 uppercase">
            Plan
          </span>
          {(['all', 'BASIC', 'PRO', 'ENTERPRISE'] as const).map((p) => (
            <button
              key={p}
              onClick={() => setPlanFilter(p)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition border ${
                planFilter === p
                  ? 'bg-[#6366f1] text-white border-[#6366f1]'
                  : 'bg-[#0a0a1a] text-gray-400 hover:text-white border-[#2a2a4a]'
              }`}
            >
              {p === 'all' ? 'All' : p}
            </button>
          ))}
        </div>

        {/* Status filter */}
        <div className="flex flex-wrap items-center gap-2">
          <span className="mr-1 text-xs tracking-wider text-gray-500 uppercase">
            Status
          </span>
          {(['all', 'active', 'inactive'] as const).map((s) => (
            <button
              key={s}
              onClick={() => setStatusFilter(s)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition border ${
                statusFilter === s
                  ? 'bg-[#6366f1] text-white border-[#6366f1]'
                  : 'bg-[#0a0a1a] text-gray-400 hover:text-white border-[#2a2a4a]'
              }`}
            >
              {s === 'all' ? 'All' : s.charAt(0).toUpperCase() + s.slice(1)}
            </button>
          ))}
        </div>
      </div>

      {/* Table */}
      <div className="bg-[#1a1a2e] border border-[#2a2a4a] rounded-xl overflow-hidden">
        {filtered.length === 0 ? (
          <div className="py-16 text-center">
            <Crown className="w-12 h-12 mx-auto mb-3 text-gray-600" />
            <p className="text-gray-400">
              {users.length === 0
                ? 'No users yet'
                : 'No subscriptions match your filters'}
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-xs text-gray-500 uppercase border-b border-[#2a2a4a] bg-[#0a0a1a]">
                  <th className="px-4 py-3 text-left">User</th>
                  <th className="px-4 py-3 text-left">Plan</th>
                  <th className="px-4 py-3 text-left">Status</th>
                  <th className="px-4 py-3 text-right">Monthly</th>
                  <th className="px-4 py-3 text-left">Role</th>
                  <th className="px-4 py-3 text-left">Created</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#2a2a4a]">
                {filtered.map((u) => (
                  <tr key={u.id} className="hover:bg-[#0a0a1a] transition">
                    {/* User */}
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <div className="w-8 h-8 rounded-full bg-[#6366f1]/20 flex items-center justify-center flex-shrink-0">
                          <span className="text-xs font-semibold text-[#6366f1]">
                            {(u.fullName || u.email || 'U')
                              .charAt(0)
                              .toUpperCase()}
                          </span>
                        </div>
                        <div className="min-w-0">
                          <p className="font-medium text-white truncate">
                            {u.fullName || '—'}
                          </p>
                          <p className="flex items-center gap-1 text-xs text-gray-500 truncate">
                            <Mail className="w-3 h-3" />
                            {u.email}
                          </p>
                        </div>
                      </div>
                    </td>

                    {/* Plan */}
                    <td className="px-4 py-3">
                      {u.subscription?.plan ? (
                        <span
                          className={`text-xs font-semibold px-2 py-1 rounded-full border ${
                            PLAN_COLORS[
                              (u.subscription.plan || '').toUpperCase()
                            ] || PLAN_COLORS.BASIC
                          }`}
                        >
                          {u.subscription.plan}
                        </span>
                      ) : (
                        <span className="text-xs text-gray-600">—</span>
                      )}
                    </td>

                    {/* Status */}
                    <td className="px-4 py-3">
                      {u.subscription?.isActive ? (
                        <span className="inline-flex items-center gap-1 text-xs font-medium text-green-400">
                          <CheckCircle className="w-3.5 h-3.5" />
                          Active
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 text-xs font-medium text-gray-500">
                          <XCircle className="w-3.5 h-3.5" />
                          Inactive
                        </span>
                      )}
                    </td>

                    {/* Monthly */}
                    <td className="px-4 py-3 text-right">
                      {u.subscription?.isActive ? (
                        <span className="font-mono text-white">
                          $
                          {(
                            PLAN_PRICING[
                              (u.subscription.plan || '').toUpperCase()
                            ] || 0
                          ).toFixed(2)}
                        </span>
                      ) : (
                        <span className="text-gray-600">—</span>
                      )}
                    </td>

                    {/* Role */}
                    <td className="px-4 py-3">
                      <span
                        className={`text-xs font-medium px-2 py-0.5 rounded-full ${
                          u.role === 'SUPER_ADMIN'
                            ? 'bg-purple-500/20 text-purple-400'
                            : u.role === 'ADMIN'
                            ? 'bg-blue-500/20 text-blue-400'
                            : 'bg-gray-500/20 text-gray-400'
                        }`}
                      >
                        {u.role}
                      </span>
                    </td>

                    {/* Created */}
                    <td className="px-4 py-3 text-xs text-gray-500">
                      <span className="inline-flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        {new Date(u.createdAt).toLocaleDateString()}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Footer info */}
      <p className="text-xs text-center text-gray-600">
        Showing {filtered.length} of {users.length} users
        {stats.mrr > 0 && ` · Est. MRR $${stats.mrr.toFixed(2)}`}
      </p>
    </div>
  );
};

// ============================================
// Sub-components
// ============================================
const StatCard: React.FC<{
  label: string;
  value: string | number;
  icon: React.ReactNode;
  tone?: 'positive' | 'neutral';
}> = ({ label, value, icon, tone = 'neutral' }) => (
  <div className="bg-[#1a1a2e] border border-[#2a2a4a] rounded-xl p-4">
    <div className="flex items-center justify-between mb-2">
      <span className="text-xs tracking-wider text-gray-400 uppercase">
        {label}
      </span>
      <div className="p-1.5 bg-[#6366f1]/10 rounded-lg">{icon}</div>
    </div>
    <p
      className={`text-xl font-bold ${
        tone === 'positive' ? 'text-green-400' : 'text-white'
      }`}
    >
      {value}
    </p>
  </div>
);

export default AdminSubscriptions;