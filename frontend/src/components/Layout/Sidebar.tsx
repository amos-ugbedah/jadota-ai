import React, { useState } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
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
  ChevronDown,
  ChevronRight,
  Brain,
  BarChart2,
  Sliders,
  CandlestickChart,
} from 'lucide-react';
import { useAuthStore } from '@/store/authStore';
import { toast } from 'react-hot-toast';

const Sidebar: React.FC = () => {
  const navigate = useNavigate();
  const { user, logout } = useAuthStore();
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [adminExpanded, setAdminExpanded] = useState(true);
  
  const isAdmin = user?.role === 'ADMIN' || user?.role === 'SUPER_ADMIN';

  const navItems = [
    { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
    { to: '/trading', icon: TrendingUp, label: 'Trading' },
    { to: '/market-chart', icon: CandlestickChart, label: 'Market Chart' },
    { to: '/ai-trading', icon: Brain, label: 'AI Signals' },
    { to: '/trading-dashboard', icon: BarChart2, label: 'Performance' },
    { to: '/ai-settings', icon: Sliders, label: 'AI Settings' },
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

  const handleLogout = async () => {
    try {
      await logout();
      toast.success('Logged out successfully');
      navigate('/login');
    } catch (error) {
      toast.error('Failed to logout');
    }
  };

  return (
    <aside className="fixed left-0 top-0 h-screen w-64 bg-[#1a1a2e] border-r border-[#2a2a4a] z-40 flex flex-col">
      {/* Logo */}
      <div className="p-4 border-b border-[#2a2a4a] flex-shrink-0">
        <div className="flex items-center gap-3">
          <img
            src="/jadota-icon.png"
            alt="JADOTA AI"
            className="flex-shrink-0 object-contain w-8 h-8"
          />
          <div>
            <h1 className="text-xl font-bold text-white whitespace-nowrap">
              JADOTA <span className="text-[#6366f1]">AI</span>
            </h1>
            <p className="text-[10px] text-gray-400">Trading Intelligence</p>
          </div>
        </div>
      </div>

      {/* Navigation - Scrollable */}
      <nav className="flex-1 p-3 space-y-1 overflow-y-auto">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-lg transition ${
                isActive
                  ? 'bg-[#6366f1]/20 text-[#6366f1]'
                  : 'text-gray-400 hover:bg-[#0a0a1a] hover:text-white'
              }`
            }
          >
            <item.icon className="flex-shrink-0 w-5 h-5" />
            <span className="text-sm font-medium">{item.label}</span>
          </NavLink>
        ))}

        {isAdmin && (
          <>
            <div className="border-t border-[#2a2a4a] my-3" />
            <button
              onClick={() => setAdminExpanded(!adminExpanded)}
              className="flex items-center justify-between w-full px-3 py-2 text-xs tracking-wider text-gray-500 uppercase transition hover:text-gray-300"
            >
              <span>Admin</span>
              {adminExpanded ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
            </button>
            {adminExpanded && (
              <div className="space-y-1">
                {adminItems.map((item) => (
                  <NavLink
                    key={item.to}
                    to={item.to}
                    className={({ isActive }) =>
                      `flex items-center gap-3 px-3 py-2.5 rounded-lg transition ${
                        isActive
                          ? 'bg-[#6366f1]/20 text-[#6366f1]'
                          : 'text-gray-400 hover:bg-[#0a0a1a] hover:text-white'
                      }`
                    }
                  >
                    <item.icon className="flex-shrink-0 w-5 h-5" />
                    <span className="text-sm font-medium">{item.label}</span>
                  </NavLink>
                ))}
              </div>
            )}
          </>
        )}
      </nav>

      {/* Bottom - Fixed at bottom */}
      <div className="border-t border-[#2a2a4a] p-3 flex-shrink-0">
        {/* User Info */}
        <div className="px-3 py-2 mb-2">
          <p className="text-sm font-medium text-white truncate">{user?.fullName || 'User'}</p>
          <p className="text-xs text-gray-400 truncate">{user?.email || 'No email'}</p>
          <div className="mt-1">
            <span className={`text-xs px-2 py-0.5 rounded-full ${
              user?.subscription?.isActive 
                ? 'bg-green-500/20 text-green-400' 
                : 'bg-yellow-500/20 text-yellow-400'
            }`}>
              {user?.subscription?.isActive ? '● Active' : 'Free Demo'}
            </span>
          </div>
        </div>

        {/* Logout */}
        <button
          onClick={handleLogout}
          className="flex items-center gap-3 px-3 py-2.5 w-full rounded-lg text-gray-400 hover:bg-red-500/20 hover:text-red-400 transition"
        >
          <LogOut className="flex-shrink-0 w-5 h-5" />
          <span className="text-sm font-medium">Logout</span>
        </button>
      </div>
    </aside>
  );
};

export default Sidebar;