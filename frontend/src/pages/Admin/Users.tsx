import React, { useState, useEffect } from 'react';
import { adminApi } from '@/api/admin';
import type { User } from '@/api/auth';
import { toast } from 'react-hot-toast';
import { 
  Search, MoreVertical, UserPlus, Loader2, 
  CheckCircle, XCircle, Shield, Mail, Calendar,
  Edit, Ban, UserCheck, Trash2, RefreshCw
} from 'lucide-react';
import { format } from 'date-fns';

// ... rest of the component stays the same

const Users: React.FC = () => {
  const [users, setUsers] = useState<User[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [roleFilter, setRoleFilter] = useState('all');
  const [statusFilter, setStatusFilter] = useState('all');
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [isActionLoading, setIsActionLoading] = useState(false);

  const fetchUsers = async () => {
    try {
      setIsLoading(true);
      const data = await adminApi.getUsers({ limit: 100 });
      setUsers(data);
    } catch (error: any) {
      toast.error(error.message || 'Failed to fetch users');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, []);

  const handleSuspendUser = async (userId: string) => {
    if (!confirm('Are you sure you want to suspend this user?')) return;
    
    setIsActionLoading(true);
    try {
      await adminApi.suspendUser(userId, 'Suspended by admin');
      toast.success('User suspended successfully');
      await fetchUsers();
    } catch (error: any) {
      toast.error(error.message || 'Failed to suspend user');
    } finally {
      setIsActionLoading(false);
      setSelectedUser(null);
    }
  };

  const handleRestoreUser = async (userId: string) => {
    setIsActionLoading(true);
    try {
      await adminApi.restoreUser(userId);
      toast.success('User restored successfully');
      await fetchUsers();
    } catch (error: any) {
      toast.error(error.message || 'Failed to restore user');
    } finally {
      setIsActionLoading(false);
      setSelectedUser(null);
    }
  };

  const filteredUsers = users.filter(user => {
    const matchesSearch = user.fullName.toLowerCase().includes(searchTerm.toLowerCase()) ||
                          user.email.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesRole = roleFilter === 'all' || user.role === roleFilter.toUpperCase();
    const matchesStatus = statusFilter === 'all' || 
                          (statusFilter === 'active' && user.subscription?.isActive) ||
                          (statusFilter === 'inactive' && !user.subscription?.isActive);
    return matchesSearch && matchesRole && matchesStatus;
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <Loader2 className="w-12 h-12 text-[#6366f1] animate-spin mx-auto" />
          <p className="mt-4 text-gray-400">Loading users...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 mx-auto space-y-6 max-w-7xl">
      {/* Header */}
      <div className="flex flex-col items-start justify-between gap-4 sm:flex-row sm:items-center">
        <div>
          <h1 className="text-3xl font-bold text-white">User Management</h1>
          <p className="mt-1 text-gray-400">Manage all users and their permissions</p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={fetchUsers}
            className="flex items-center gap-2 px-4 py-2 bg-[#1a1a2e] border border-[#2a2a4a] rounded-lg text-white hover:bg-[#2a2a4a] transition"
          >
            <RefreshCw className="w-4 h-4" />
            Refresh
          </button>
          <button className="flex items-center gap-2 px-4 py-2 bg-[#6366f1] text-white rounded-lg hover:bg-[#4f46e5] transition font-medium">
            <UserPlus className="w-4 h-4" />
            Add User
          </button>
        </div>
      </div>

      {/* Search & Filter */}
      <div className="flex flex-col gap-4 sm:flex-row">
        <div className="relative flex-1">
          <Search className="absolute w-4 h-4 text-gray-400 -translate-y-1/2 left-3 top-1/2" />
          <input
            type="text"
            placeholder="Search by name or email..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 bg-[#0a0a1a] border border-[#2a2a4a] rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-[#6366f1] placeholder-gray-500"
          />
        </div>
        <select
          value={roleFilter}
          onChange={(e) => setRoleFilter(e.target.value)}
          className="px-4 py-2 bg-[#0a0a1a] border border-[#2a2a4a] rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-[#6366f1]"
        >
          <option value="all">All Roles</option>
          <option value="user">User</option>
          <option value="admin">Admin</option>
          <option value="super_admin">Super Admin</option>
        </select>
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="px-4 py-2 bg-[#0a0a1a] border border-[#2a2a4a] rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-[#6366f1]"
        >
          <option value="all">All Status</option>
          <option value="active">Active</option>
          <option value="inactive">Inactive</option>
        </select>
      </div>

      {/* Users Table */}
      <div className="bg-[#1a1a2e] rounded-xl border border-[#2a2a4a] overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-[#2a2a4a] bg-[#0a0a1a]/50">
                <th className="px-6 py-4 text-xs font-medium tracking-wider text-left text-gray-400 uppercase">User</th>
                <th className="px-6 py-4 text-xs font-medium tracking-wider text-left text-gray-400 uppercase">Email</th>
                <th className="px-6 py-4 text-xs font-medium tracking-wider text-left text-gray-400 uppercase">Role</th>
                <th className="px-6 py-4 text-xs font-medium tracking-wider text-left text-gray-400 uppercase">Subscription</th>
                <th className="px-6 py-4 text-xs font-medium tracking-wider text-left text-gray-400 uppercase">Joined</th>
                <th className="px-6 py-4 text-xs font-medium tracking-wider text-right text-gray-400 uppercase">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#2a2a4a]">
              {filteredUsers.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-6 py-8 text-center text-gray-400">
                    No users found
                  </td>
                </tr>
              ) : (
                filteredUsers.map((user) => (
                  <tr key={user.id} className="hover:bg-[#0a0a1a]/50 transition">
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-full bg-[#6366f1]/20 flex items-center justify-center">
                          <span className="text-[#6366f1] font-medium text-sm">
                            {user.fullName.charAt(0).toUpperCase()}
                          </span>
                        </div>
                        <span className="font-medium text-white">{user.fullName}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-400">{user.email}</td>
                    <td className="px-6 py-4">
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                        user.role === 'SUPER_ADMIN' 
                          ? 'text-purple-400 bg-purple-500/20' 
                          : user.role === 'ADMIN'
                            ? 'text-blue-400 bg-blue-500/20'
                            : 'text-gray-400 bg-gray-500/20'
                      }`}>
                        {user.role}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      {user.subscription?.isActive ? (
                        <span className="flex items-center gap-1 text-sm text-green-400">
                          <CheckCircle className="w-3 h-3" />
                          {user.subscription.plan || 'Active'}
                        </span>
                      ) : (
                        <span className="flex items-center gap-1 text-sm text-gray-400">
                          <XCircle className="w-3 h-3" />
                          Inactive
                        </span>
                      )}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-400">
                      {format(new Date(user.createdAt), 'MMM d, yyyy')}
                    </td>
                    <td className="px-6 py-4 text-right">
                      <div className="flex items-center justify-end gap-2">
                        <button
                          onClick={() => setSelectedUser(user)}
                          className="p-1 hover:bg-[#2a2a4a] rounded transition"
                        >
                          <MoreVertical className="w-4 h-4 text-gray-400" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* User Action Modal */}
      {selectedUser && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80">
          <div className="bg-[#1a1a2e] rounded-xl border border-[#2a2a4a] max-w-md w-full p-6">
            <div className="flex items-start justify-between mb-4">
              <div>
                <h3 className="text-xl font-bold text-white">User Actions</h3>
                <p className="text-sm text-gray-400">{selectedUser.fullName}</p>
              </div>
              <button
                onClick={() => setSelectedUser(null)}
                className="text-gray-400 hover:text-white"
              >
                ✕
              </button>
            </div>
            
            <div className="space-y-3">
              <div className="flex items-center gap-3 py-2 border-b border-[#2a2a4a]">
                <Mail className="w-4 h-4 text-gray-400" />
                <span className="text-sm text-gray-400">{selectedUser.email}</span>
              </div>
              <div className="flex items-center gap-3 py-2 border-b border-[#2a2a4a]">
                <Shield className="w-4 h-4 text-gray-400" />
                <span className="text-sm text-gray-400">Role: {selectedUser.role}</span>
              </div>
              <div className="flex items-center gap-3 py-2 border-b border-[#2a2a4a]">
                <Calendar className="w-4 h-4 text-gray-400" />
                <span className="text-sm text-gray-400">
                  Joined: {format(new Date(selectedUser.createdAt), 'MMM d, yyyy')}
                </span>
              </div>
            </div>

            <div className="mt-6 space-y-2">
              {selectedUser.role !== 'SUPER_ADMIN' && (
                <>
                  <button
                    onClick={() => handleSuspendUser(selectedUser.id)}
                    disabled={isActionLoading}
                    className="flex items-center justify-center w-full gap-2 py-2 text-red-400 transition rounded-lg bg-red-500/20 hover:bg-red-500/30 disabled:opacity-50"
                  >
                    <Ban className="w-4 h-4" />
                    Suspend User
                  </button>
                  <button
                    onClick={() => handleRestoreUser(selectedUser.id)}
                    disabled={isActionLoading}
                    className="flex items-center justify-center w-full gap-2 py-2 text-green-400 transition rounded-lg bg-green-500/20 hover:bg-green-500/30 disabled:opacity-50"
                  >
                    <UserCheck className="w-4 h-4" />
                    Restore User
                  </button>
                </>
              )}
              <button
                onClick={() => setSelectedUser(null)}
                className="w-full py-2 bg-[#2a2a4a] text-gray-300 rounded-lg hover:bg-[#3a3a5a] transition"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Users;