import React, { useState } from 'react';
import { Search, MoreVertical, UserPlus } from 'lucide-react';

interface User {
  id: string;
  name: string;
  email: string;
  role: 'USER' | 'ADMIN' | 'SUPER_ADMIN';
  status: 'active' | 'suspended' | 'pending';
  subscription: string;
  joined: string;
}

const Users: React.FC = () => {
  const [searchTerm, setSearchTerm] = useState('');
  
  const users: User[] = [
    {
      id: '1',
      name: 'Test User',
      email: 'test@example.com',
      role: 'USER',
      status: 'active',
      subscription: 'None',
      joined: '2024-01-01'
    },
    {
      id: '2',
      name: 'Admin User',
      email: 'admin@example.com',
      role: 'ADMIN',
      status: 'active',
      subscription: 'Pro',
      joined: '2024-01-01'
    }
  ];

  const getStatusColor = (status: string) => {
    switch(status) {
      case 'active': return 'text-green-400 bg-green-500/20';
      case 'suspended': return 'text-red-400 bg-red-500/20';
      case 'pending': return 'text-yellow-400 bg-yellow-500/20';
      default: return 'text-gray-400 bg-gray-500/20';
    }
  };

  const getRoleColor = (role: string) => {
    switch(role) {
      case 'SUPER_ADMIN': return 'text-purple-400 bg-purple-500/20';
      case 'ADMIN': return 'text-blue-400 bg-blue-500/20';
      default: return 'text-gray-400 bg-gray-500/20';
    }
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col items-start justify-between gap-4 sm:flex-row sm:items-center">
        <div>
          <h1 className="text-3xl font-bold text-white">User Management</h1>
          <p className="mt-1 text-gray-400">Manage all users and their permissions</p>
        </div>
        <button className="flex items-center gap-2 px-4 py-2 bg-[#6366f1] text-white rounded-lg hover:bg-[#4f46e5] transition font-medium">
          <UserPlus className="w-4 h-4" />
          Add User
        </button>
      </div>

      {/* Search & Filter */}
      <div className="flex flex-col gap-4 sm:flex-row">
        <div className="relative flex-1">
          <Search className="absolute w-4 h-4 text-gray-400 -translate-y-1/2 left-3 top-1/2" />
          <input
            type="text"
            placeholder="Search users..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 bg-[#0a0a1a] border border-[#2a2a4a] rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-[#6366f1] placeholder-gray-500"
          />
        </div>
        <select className="px-4 py-2 bg-[#0a0a1a] border border-[#2a2a4a] rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-[#6366f1]">
          <option value="all">All Roles</option>
          <option value="user">User</option>
          <option value="admin">Admin</option>
          <option value="super_admin">Super Admin</option>
        </select>
        <select className="px-4 py-2 bg-[#0a0a1a] border border-[#2a2a4a] rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-[#6366f1]">
          <option value="all">All Status</option>
          <option value="active">Active</option>
          <option value="suspended">Suspended</option>
          <option value="pending">Pending</option>
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
                <th className="px-6 py-4 text-xs font-medium tracking-wider text-left text-gray-400 uppercase">Status</th>
                <th className="px-6 py-4 text-xs font-medium tracking-wider text-left text-gray-400 uppercase">Subscription</th>
                <th className="px-6 py-4 text-xs font-medium tracking-wider text-left text-gray-400 uppercase">Joined</th>
                <th className="px-6 py-4 text-xs font-medium tracking-wider text-right text-gray-400 uppercase">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#2a2a4a]">
              {users.map((user) => (
                <tr key={user.id} className="hover:bg-[#0a0a1a]/50 transition">
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-full bg-[#6366f1]/20 flex items-center justify-center">
                        <span className="text-[#6366f1] font-medium text-sm">
                          {user.name.charAt(0)}
                        </span>
                      </div>
                      <span className="font-medium text-white">{user.name}</span>
                    </div>
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-400">{user.email}</td>
                  <td className="px-6 py-4">
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${getRoleColor(user.role)}`}>
                      {user.role}
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(user.status)}`}>
                      {user.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-400">{user.subscription || 'None'}</td>
                  <td className="px-6 py-4 text-sm text-gray-400">{user.joined}</td>
                  <td className="px-6 py-4 text-right">
                    <button className="p-1 hover:bg-[#2a2a4a] rounded transition">
                      <MoreVertical className="w-4 h-4 text-gray-400" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default Users;