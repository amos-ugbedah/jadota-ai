import React, { useEffect, useState } from 'react';
import { CreditCard, RefreshCw, Loader2, CheckCircle, XCircle, Clock } from 'lucide-react';
import { toast } from 'react-hot-toast';
import { paymentsApi, type Payment, type PaymentStatus } from '@/api/payments';

const statusStyles: Record<PaymentStatus, string> = {
  pending:   'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
  verifying: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
  completed: 'bg-green-500/20 text-green-400 border-green-500/30',
  failed:    'bg-red-500/20 text-red-400 border-red-500/30',
  expired:   'bg-gray-500/20 text-gray-400 border-gray-500/30',
  cancelled: 'bg-gray-500/20 text-gray-400 border-gray-500/30',
};

const AdminPayments: React.FC = () => {
  const [payments, setPayments] = useState<Payment[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [filter, setFilter] = useState<'all' | PaymentStatus>('pending');
  const [busyId, setBusyId] = useState<string | null>(null);

  const load = async (silent = false) => {
    if (!silent) setLoading(true); else setRefreshing(true);
    try {
      const data = await paymentsApi.adminList(filter === 'all' ? undefined : filter);
      setPayments(data);
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || 'Failed to load payments');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filter]);

  const approve = async (p: Payment) => {
    const txHash = window.prompt('Optional: enter the blockchain tx hash (or leave blank):') || undefined;
    setBusyId(p.id);
    try {
      const res = await paymentsApi.adminApprove(p.id, txHash);
      toast.success(res.message);
      await load(true);
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || 'Failed to approve');
    } finally {
      setBusyId(null);
    }
  };

  const reject = async (p: Payment) => {
    const notes = window.prompt('Reason for rejection (optional):') || undefined;
    setBusyId(p.id);
    try {
      await paymentsApi.adminReject(p.id, notes);
      toast.success('Payment rejected');
      await load(true);
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || 'Failed to reject');
    } finally {
      setBusyId(null);
    }
  };

  return (
    <div className="p-6 mx-auto space-y-6 max-w-7xl">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <h1 className="flex items-center gap-3 text-3xl font-bold text-white">
            <CreditCard className="w-8 h-8 text-[#6366f1]" />
            Payments
          </h1>
          <p className="mt-1 text-gray-400">
            Review and approve subscription payments
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

      {/* Filters */}
      <div className="flex flex-wrap gap-2">
        {(['pending', 'completed', 'failed', 'all'] as const).map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`px-3 py-1.5 rounded-lg text-sm font-medium transition border ${
              filter === f
                ? 'bg-[#6366f1] text-white border-[#6366f1]'
                : 'bg-[#0a0a1a] text-gray-400 hover:text-white border-[#2a2a4a]'
            }`}
          >
            {f.charAt(0).toUpperCase() + f.slice(1)}
          </button>
        ))}
      </div>

      {/* List */}
      <div className="bg-[#1a1a2e] border border-[#2a2a4a] rounded-xl overflow-hidden">
        {loading ? (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="w-8 h-8 text-[#6366f1] animate-spin" />
          </div>
        ) : payments.length === 0 ? (
          <div className="py-16 text-center">
            <CreditCard className="w-12 h-12 mx-auto mb-3 text-gray-600" />
            <p className="text-gray-400">No {filter === 'all' ? '' : filter} payments</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-xs text-gray-500 uppercase border-b border-[#2a2a4a]">
                  <th className="px-4 py-3 text-left">User</th>
                  <th className="px-4 py-3 text-left">Plan</th>
                  <th className="px-4 py-3 text-right">Amount</th>
                  <th className="px-4 py-3 text-left">Status</th>
                  <th className="px-4 py-3 text-left">Created</th>
                  <th className="px-4 py-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#2a2a4a]">
                {payments.map((p) => (
                  <tr key={p.id} className="hover:bg-[#0a0a1a]">
                    <td className="px-4 py-3 font-mono text-xs text-gray-400">
                      {p.user_id.slice(0, 8)}…
                    </td>
                    <td className="px-4 py-3">
                      <span className="font-medium text-white">{p.plan}</span>
                      <span className="ml-2 text-xs text-gray-500">{p.months}mo</span>
                    </td>
                    <td className="px-4 py-3 font-mono text-right text-white">
                      ${p.amount_usdt.toFixed(2)}
                    </td>
                    <td className="px-4 py-3">
                      <span className={`text-xs px-2 py-0.5 rounded-full border ${statusStyles[p.status]}`}>
                        {p.status}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-xs text-gray-500">
                      {p.created_at ? new Date(p.created_at).toLocaleString() : '—'}
                    </td>
                    <td className="px-4 py-3 text-right">
                      {p.status === 'pending' || p.status === 'verifying' ? (
                        <div className="flex items-center justify-end gap-2">
                          <button
                            onClick={() => approve(p)}
                            disabled={busyId === p.id}
                            className="flex items-center gap-1 px-2.5 py-1 text-xs bg-green-500/20 hover:bg-green-500/30 text-green-400 border border-green-500/30 rounded transition disabled:opacity-50"
                          >
                            {busyId === p.id ? <Loader2 className="w-3 h-3 animate-spin" /> : <CheckCircle className="w-3 h-3" />}
                            Approve
                          </button>
                          <button
                            onClick={() => reject(p)}
                            disabled={busyId === p.id}
                            className="flex items-center gap-1 px-2.5 py-1 text-xs bg-red-500/20 hover:bg-red-500/30 text-red-400 border border-red-500/30 rounded transition disabled:opacity-50"
                          >
                            <XCircle className="w-3 h-3" />
                            Reject
                          </button>
                        </div>
                      ) : p.tx_hash ? (
                        <a
                          href={`https://bscscan.com/tx/${p.tx_hash}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-xs text-[#6366f1] hover:underline font-mono"
                        >
                          {p.tx_hash.slice(0, 10)}…
                        </a>
                      ) : (
                        <span className="text-xs text-gray-600">—</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

export default AdminPayments;