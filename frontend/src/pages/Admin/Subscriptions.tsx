import React, { useState, useEffect } from 'react';
import { adminApi } from '@/api/admin';
import { subscriptionApi } from '@/api/subscription';
import type { Subscription, Plan } from '@/api/subscription';
import { toast } from 'react-hot-toast';
import { 
  Crown, Users, DollarSign, Clock, Loader2,
  CheckCircle, XCircle, RefreshCw, TrendingUp,
  AlertCircle, Calendar, Eye, MoreVertical
} from 'lucide-react';
import { format, formatDistanceToNow } from 'date-fns';

// ... rest of the component stays the same

const Subscriptions: React.FC = () => {
  const [subscriptions, setSubscriptions] = useState<Subscription[]>([]);
  const [plans, setPlans] = useState<Plan[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [stats, setStats] = useState({
    total: 0,
    active: 0,
    pending: 0,
    expired: 0,
    cancelled: 0,
    revenue: 0
  });
  const [selectedSubscription, setSelectedSubscription] = useState<Subscription | null>(null);

  const fetchData = async () => {
    try {
      setIsLoading(true);
      
      // Fetch all subscriptions
      const subs = await adminApi.getSubscriptions({ limit: 100 });
      setSubscriptions(subs);
      
      // Fetch plans
      const plansData = await subscriptionApi.getPlans();
      setPlans(plansData);
      
      // Calculate stats
      const active = subs.filter(s => s.status === 'ACTIVE').length;
      const pending = subs.filter(s => s.status === 'PENDING').length;
      const expired = subs.filter(s => s.status === 'EXPIRED').length;
      const cancelled = subs.filter(s => s.status === 'CANCELLED').length;
      
      // Calculate revenue (simplified)
      const totalRevenue = subs
        .filter(s => s.status === 'ACTIVE')
        .reduce((sum, s) => sum + (s.plan?.price || 0), 0);
      
      setStats({
        total: subs.length,
        active,
        pending,
        expired,
        cancelled,
        revenue: totalRevenue
      });
      
    } catch (error: any) {
      toast.error(error.message || 'Failed to fetch subscriptions');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const getStatusColor = (status: string) => {
    switch(status) {
      case 'ACTIVE': return 'text-green-400 bg-green-500/20';
      case 'PENDING': return 'text-yellow-400 bg-yellow-500/20';
      case 'EXPIRED': return 'text-red-400 bg-red-500/20';
      case 'CANCELLED': return 'text-gray-400 bg-gray-500/20';
      default: return 'text-gray-400 bg-gray-500/20';
    }
  };

  const getStatusIcon = (status: string) => {
    switch(status) {
      case 'ACTIVE': return <CheckCircle className="w-3 h-3" />;
      case 'PENDING': return <Clock className="w-3 h-3" />;
      case 'EXPIRED': return <XCircle className="w-3 h-3" />;
      case 'CANCELLED': return <XCircle className="w-3 h-3" />;
      default: return null;
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <Loader2 className="w-12 h-12 text-[#6366f1] animate-spin mx-auto" />
          <p className="mt-4 text-gray-400">Loading subscriptions...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 mx-auto space-y-6 max-w-7xl">
      {/* Header */}
      <div className="flex flex-col items-start justify-between gap-4 sm:flex-row sm:items-center">
        <div>
          <h1 className="text-3xl font-bold text-white">Subscriptions</h1>
          <p className="mt-1 text-gray-400">Manage user subscriptions and plans</p>
        </div>
        <button
          onClick={fetchData}
          className="flex items-center gap-2 px-4 py-2 bg-[#1a1a2e] border border-[#2a2a4a] rounded-lg text-white hover:bg-[#2a2a4a] transition"
        >
          <RefreshCw className="w-4 h-4" />
          Refresh
        </button>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-5">
        <SubscriptionStatCard
          title="Total"
          value={stats.total.toString()}
          icon={<Crown className="w-5 h-5 text-yellow-400" />}
        />
        <SubscriptionStatCard
          title="Active"
          value={stats.active.toString()}
          icon={<Users className="w-5 h-5 text-green-400" />}
        />
        <SubscriptionStatCard
          title="Pending"
          value={stats.pending.toString()}
          icon={<Clock className="w-5 h-5 text-yellow-400" />}
        />
        <SubscriptionStatCard
          title="Expired"
          value={stats.expired.toString()}
          icon={<AlertCircle className="w-5 h-5 text-red-400" />}
        />
        <SubscriptionStatCard
          title="Revenue"
          value={`$${stats.revenue.toFixed(2)}`}
          icon={<DollarSign className="w-5 h-5 text-blue-400" />}
        />
      </div>

      {/* Plans Section */}
      <div className="bg-[#1a1a2e] rounded-xl p-6 border border-[#2a2a4a]">
        <h3 className="mb-4 text-lg font-semibold text-white">Available Plans</h3>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
          {plans.map((plan) => (
            <div key={plan.id} className="bg-[#0a0a1a] rounded-xl p-4 border border-[#2a2a4a]">
              <div className="flex items-start justify-between">
                <div>
                  <h4 className="font-medium text-white">{plan.name}</h4>
                  <p className="text-2xl font-bold text-[#6366f1]">
                    ${plan.price}
                    <span className="text-sm font-normal text-gray-400">/{plan.duration}mo</span>
                  </p>
                </div>
                {plan.isPopular && (
                  <span className="px-2 py-1 bg-[#6366f1] text-white text-xs rounded-full">
                    Popular
                  </span>
                )}
              </div>
              <ul className="mt-3 space-y-1">
                {plan.features.slice(0, 3).map((feature, i) => (
                  <li key={i} className="flex items-center gap-1 text-xs text-gray-400">
                    <CheckCircle className="w-3 h-3 text-green-400" />
                    {feature}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </div>

      {/* Subscriptions Table */}
      <div className="bg-[#1a1a2e] rounded-xl border border-[#2a2a4a] overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-[#2a2a4a] bg-[#0a0a1a]/50">
                <th className="px-6 py-4 text-xs font-medium tracking-wider text-left text-gray-400 uppercase">User</th>
                <th className="px-6 py-4 text-xs font-medium tracking-wider text-left text-gray-400 uppercase">Plan</th>
                <th className="px-6 py-4 text-xs font-medium tracking-wider text-left text-gray-400 uppercase">Status</th>
                <th className="px-6 py-4 text-xs font-medium tracking-wider text-left text-gray-400 uppercase">Started</th>
                <th className="px-6 py-4 text-xs font-medium tracking-wider text-left text-gray-400 uppercase">Expires</th>
                <th className="px-6 py-4 text-xs font-medium tracking-wider text-right text-gray-400 uppercase">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#2a2a4a]">
              {subscriptions.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-6 py-8 text-center text-gray-400">
                    No subscriptions found
                  </td>
                </tr>
              ) : (
                subscriptions.slice(0, 20).map((sub) => (
                  <tr key={sub.id} className="hover:bg-[#0a0a1a]/50 transition">
                    <td className="px-6 py-4 text-sm text-white">
                      {sub.userId || 'Unknown User'}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-300">
                      {sub.plan?.name || 'Unknown Plan'}
                    </td>
                    <td className="px-6 py-4">
                      <span className={`px-2 py-1 rounded-full text-xs font-medium flex items-center gap-1 w-fit ${getStatusColor(sub.status)}`}>
                        {getStatusIcon(sub.status)}
                        {sub.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-400">
                      {format(new Date(sub.startAt), 'MMM d, yyyy')}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-400">
                      {sub.expiresAt ? (
                        <span className={new Date(sub.expiresAt) < new Date() ? 'text-red-400' : ''}>
                          {format(new Date(sub.expiresAt), 'MMM d, yyyy')}
                          {new Date(sub.expiresAt) > new Date() && (
                            <span className="block text-xs text-gray-500">
                              {formatDistanceToNow(new Date(sub.expiresAt))} remaining
                            </span>
                          )}
                        </span>
                      ) : 'N/A'}
                    </td>
                    <td className="px-6 py-4 text-right">
                      <button
                        onClick={() => setSelectedSubscription(sub)}
                        className="p-1 hover:bg-[#2a2a4a] rounded transition"
                      >
                        <Eye className="w-4 h-4 text-gray-400" />
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Subscription Detail Modal */}
      {selectedSubscription && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80">
          <div className="bg-[#1a1a2e] rounded-xl border border-[#2a2a4a] max-w-md w-full p-6">
            <div className="flex items-start justify-between mb-4">
              <h3 className="text-xl font-bold text-white">Subscription Details</h3>
              <button
                onClick={() => setSelectedSubscription(null)}
                className="text-gray-400 hover:text-white"
              >
                ✕
              </button>
            </div>
            
            <div className="space-y-3">
              <div className="flex justify-between py-2 border-b border-[#2a2a4a]">
                <span className="text-gray-400">Plan</span>
                <span className="font-medium text-white">{selectedSubscription.plan?.name || 'N/A'}</span>
              </div>
              <div className="flex justify-between py-2 border-b border-[#2a2a4a]">
                <span className="text-gray-400">Status</span>
                <span className={`font-medium ${getStatusColor(selectedSubscription.status)}`}>
                  {selectedSubscription.status}
                </span>
              </div>
              <div className="flex justify-between py-2 border-b border-[#2a2a4a]">
                <span className="text-gray-400">Started</span>
                <span className="text-white">
                  {format(new Date(selectedSubscription.startAt), 'MMM d, yyyy HH:mm')}
                </span>
              </div>
              <div className="flex justify-between py-2 border-b border-[#2a2a4a]">
                <span className="text-gray-400">Expires</span>
                <span className="text-white">
                  {selectedSubscription.expiresAt ? 
                    format(new Date(selectedSubscription.expiresAt), 'MMM d, yyyy HH:mm') :
                    'N/A'
                  }
                </span>
              </div>
              <div className="flex justify-between py-2">
                <span className="text-gray-400">Trial</span>
                <span className="text-white">{selectedSubscription.isTrial ? 'Yes' : 'No'}</span>
              </div>
            </div>

            <button
              onClick={() => setSelectedSubscription(null)}
              className="mt-6 w-full py-2 bg-[#2a2a4a] text-gray-300 rounded-lg hover:bg-[#3a3a5a] transition"
            >
              Close
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

const SubscriptionStatCard: React.FC<{
  title: string;
  value: string;
  icon: React.ReactNode;
}> = ({ title, value, icon }) => (
  <div className="bg-[#1a1a2e] rounded-xl p-6 border border-[#2a2a4a]">
    <div className="flex items-start justify-between">
      <div>
        <p className="text-sm font-medium text-gray-400">{title}</p>
        <p className="mt-1 text-2xl font-bold text-white">{value}</p>
      </div>
      <div className="p-2.5 bg-[#6366f1]/10 rounded-lg">
        {icon}
      </div>
    </div>
  </div>
);

export default Subscriptions;