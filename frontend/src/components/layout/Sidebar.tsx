import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  TrendingUp,
  Wallet,
  BarChart3,
  Settings,
  Users,
  Crown,
  Activity,
  LogOut,
} from 'lucide-react';
import { useAuthStore } from '@/store/authStore';

const Sidebar: React.FC = () => {
  const { user, logout } = useAuthStore();
  const isAdmin = user?.role === 'ADMIN' || user?.role === 'SUPER_ADMIN';

  const navItems = [
    { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
    { to: '/trading', icon: TrendingUp, label: 'Trading' },
    { to: '/positions', icon: Wallet, label: 'Positions' },
    { to: '/backtesting', icon: BarChart3, label: 'Backtesting' },
    { to: '/subscription', icon: Crown, label: 'Subscription' },
  ];

  const adminItems = [
    { to: '/admin', icon: Activity, label: 'Admin Dashboard' },
    { to: '/admin/users', icon: Users, label: 'Users' },
    { to: '/admin/subscriptions', icon: Crown, label: 'Subscriptions' },
    { to: '/admin/system', icon: Settings, label: 'System' },
  ];

  return (
    <aside className="fixed left-0 top-0 h-screen w-64 bg-[#1a1a2e] border-r border-[#2a2a4a]">
      {/* Logo with JADOTA branding */}
      <div className="p-6 border-b border-[#2a2a4a]">
        <div className="flex items-center gap-3">
          <img 
            src="/jadota-icon.png" 
            alt="JADOTA AI" 
            className="w-10 h-10 object-contain"
          />
          <div>
            <h1 className="text-2xl font-bold text-white">
              JADOTA <span className="text-[#6366f1]">AI</span>
            </h1>
            <p className="text-xs text-gray-400">Trading Intelligence</p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="p-4 space-y-1">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) =>
              `flex items-center gap-3 px-4 py-3 rounded-lg transition ${
                isActive
                  ? 'bg-[#6366f1]/20 text-[#6366f1]'
                  : 'text-gray-400 hover:bg-[#0a0a1a] hover:text-white'
              }`
            }
          >
            <item.icon className="w-5 h-5" />
            <span className="text-sm font-medium">{item.label}</span>
          </NavLink>
        ))}

        {isAdmin && (
          <>
            <div className="border-t border-[#2a2a4a] my-4" />
            <p className="text-xs text-gray-500 px-4 py-2 uppercase tracking-wider">
              Admin
            </p>
            {adminItems.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-4 py-3 rounded-lg transition ${
                    isActive
                      ? 'bg-[#6366f1]/20 text-[#6366f1]'
                      : 'text-gray-400 hover:bg-[#0a0a1a] hover:text-white'
                  }`
                }
              >
                <item.icon className="w-5 h-5" />
                <span className="text-sm font-medium">{item.label}</span>
              </NavLink>
            ))}
          </>
        )}
      </nav>

      {/* Bottom */}
      <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-[#2a2a4a]">
        <button
          onClick={logout}
          className="flex items-center gap-3 px-4 py-3 w-full rounded-lg 
                   text-gray-400 hover:bg-[#0a0a1a] hover:text-white transition"
        >
          <LogOut className="w-5 h-5" />
          <span className="text-sm font-medium">Logout</span>
        </button>
      </div>
    </aside>
  );
};

export default Sidebar;