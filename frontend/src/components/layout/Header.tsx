import React from 'react';
import { useAuthStore } from '@/store/authStore';
import { Bell, User, Search } from 'lucide-react';

const Header: React.FC = () => {
  const { user } = useAuthStore();

  return (
    <header className="fixed left-64 right-0 top-0 h-16 bg-[#1a1a2e] border-b border-[#2a2a4a] z-10">
      <div className="flex items-center justify-between h-full px-6">
        {/* Search Bar */}
        <div className="flex-1 max-w-md">
          <div className="relative">
            <Search className="absolute w-4 h-4 text-gray-400 -translate-y-1/2 left-3 top-1/2" />
            <input
              type="text"
              placeholder="Search markets..."
              className="w-full pl-10 pr-4 py-2 bg-[#0a0a1a] border border-[#2a2a4a] 
                       rounded-lg text-white text-sm focus:outline-none focus:ring-2 
                       focus:ring-[#6366f1] placeholder-gray-500"
            />
          </div>
        </div>

        {/* Right Side */}
        <div className="flex items-center gap-4">
          {/* Notification */}
          <button className="p-2 rounded-lg hover:bg-[#0a0a1a] transition relative">
            <Bell className="w-5 h-5 text-gray-400" />
            <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-red-500 rounded-full"></span>
          </button>

          {/* User Info */}
          <div className="flex items-center gap-3">
            <div className="hidden text-right sm:block">
              <p className="text-sm font-medium text-white">{user?.fullName || 'User'}</p>
              <p className="text-xs text-gray-400">{user?.role || 'User'}</p>
            </div>
            <div className="w-9 h-9 rounded-full bg-[#6366f1]/20 flex items-center justify-center">
              <User className="w-5 h-5 text-[#6366f1]" />
            </div>
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;