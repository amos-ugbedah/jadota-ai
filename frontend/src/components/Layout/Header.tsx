import React, { useState, useEffect } from 'react';
import { useAuthStore } from '@/store/authStore';
import { useNavigate, Link } from 'react-router-dom';
import { 
  Bell, User, Search, X, 
  Settings, LogOut, HelpCircle, 
  Crown, ChevronDown, CheckCircle, Loader2
} from 'lucide-react';
import { toast } from 'react-hot-toast';

interface Notification {
  id: string;
  message: string;
  createdAt: string;
  read: boolean;
  type: 'trade' | 'price' | 'subscription' | 'system';
}

const Header: React.FC = () => {
  const navigate = useNavigate();
  const { user, logout } = useAuthStore();
  const [searchQuery, setSearchQuery] = useState('');
  const [showNotifications, setShowNotifications] = useState(false);
  const [showUserMenu, setShowUserMenu] = useState(false);
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [isLoadingNotifications, setIsLoadingNotifications] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);

  const fetchNotifications = async () => {
    try {
      setIsLoadingNotifications(true);
      setNotifications([]);
      setUnreadCount(0);
    } catch (error) {
      console.error('Failed to fetch notifications:', error);
    } finally {
      setIsLoadingNotifications(false);
    }
  };

  useEffect(() => {
    fetchNotifications();
  }, []);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      navigate(`/trading?symbol=${searchQuery.toUpperCase()}`);
      setSearchQuery('');
    }
  };

  const handleLogout = async () => {
    try {
      await logout();
      toast.success('Logged out successfully');
      navigate('/login');
    } catch (error) {
      toast.error('Failed to logout');
    }
  };

  const markAllRead = async () => {
    try {
      setNotifications(prev => prev.map(n => ({ ...n, read: true })));
      setUnreadCount(0);
      toast.success('All notifications marked as read');
    } catch (error) {
      toast.error('Failed to mark notifications as read');
    }
  };

  useEffect(() => {
    const handleClickOutside = () => {
      setShowNotifications(false);
      setShowUserMenu(false);
    };
    document.addEventListener('click', handleClickOutside);
    return () => document.removeEventListener('click', handleClickOutside);
  }, []);

  return (
    <header className="fixed left-0 lg:left-64 right-0 top-0 h-16 bg-[#1a1a2e] border-b border-[#2a2a4a] z-30">
      <div className="flex items-center justify-between h-full px-4 lg:px-6">
        <div className="flex items-center flex-1 gap-3">
          <form onSubmit={handleSearch} className="flex-1 max-w-md">
            <div className="relative">
              <Search className="absolute w-4 h-4 text-gray-400 -translate-y-1/2 left-3 top-1/2" />
              <input
                type="text"
                placeholder="Search markets..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-9 pr-4 py-2 bg-[#0a0a1a] border border-[#2a2a4a] 
                         rounded-lg text-white text-sm focus:outline-none focus:ring-2 
                         focus:ring-[#6366f1] placeholder-gray-500"
              />
              {searchQuery && (
                <button
                  type="button"
                  onClick={() => setSearchQuery('')}
                  className="absolute text-gray-400 -translate-y-1/2 right-3 top-1/2 hover:text-white"
                >
                  <X className="w-4 h-4" />
                </button>
              )}
            </div>
          </form>
        </div>

        <div className="flex items-center gap-2">
          {/* Subscription Status */}
          <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 bg-[#0a0a1a] rounded-lg border border-[#2a2a4a]">
            {user?.subscription?.isActive ? (
              <>
                <CheckCircle className="w-3.5 h-3.5 text-green-400" />
                <span className="text-xs font-medium text-green-400">
                  {user.subscription.plan || 'Active'}
                </span>
              </>
            ) : (
              <>
                <Crown className="w-3.5 h-3.5 text-yellow-400" />
                <Link to="/subscription" className="text-xs font-medium text-yellow-400 hover:text-yellow-300">
                  Upgrade
                </Link>
              </>
            )}
          </div>

          {/* Notifications */}
          <div className="relative">
            <button
              onClick={(e) => {
                e.stopPropagation();
                setShowNotifications(!showNotifications);
                setShowUserMenu(false);
                if (!showNotifications) fetchNotifications();
              }}
              className="p-2 rounded-lg hover:bg-[#0a0a1a] transition relative"
            >
              <Bell className="w-5 h-5 text-gray-400" />
              {unreadCount > 0 && (
                <span className="absolute top-1 right-1 w-5 h-5 bg-red-500 text-white text-[10px] font-bold rounded-full flex items-center justify-center">
                  {unreadCount > 9 ? '9+' : unreadCount}
                </span>
              )}
            </button>

            {showNotifications && (
              <div className="absolute right-0 mt-2 w-80 bg-[#1a1a2e] border border-[#2a2a4a] rounded-lg shadow-xl overflow-hidden z-50">
                <div className="px-4 py-3 border-b border-[#2a2a4a] flex justify-between items-center">
                  <span className="text-sm font-medium text-white">Notifications</span>
                  {unreadCount > 0 && (
                    <button
                      onClick={markAllRead}
                      className="text-xs text-[#6366f1] hover:text-[#4f46e5]"
                    >
                      Mark all read
                    </button>
                  )}
                </div>
                <div className="overflow-y-auto max-h-72">
                  {isLoadingNotifications ? (
                    <div className="p-4 text-sm text-center text-gray-400">
                      <Loader2 className="w-5 h-5 mx-auto animate-spin" />
                      Loading...
                    </div>
                  ) : notifications.length === 0 ? (
                    <div className="p-8 text-sm text-center text-gray-400">
                      <Bell className="w-8 h-8 mx-auto mb-2 opacity-50" />
                      No notifications
                    </div>
                  ) : (
                    notifications.map((notif) => (
                      <div
                        key={notif.id}
                        className={`px-4 py-3 border-b border-[#2a2a4a] ${
                          !notif.read ? 'bg-[#6366f1]/5' : ''
                        }`}
                      >
                        <p className={`text-sm ${!notif.read ? 'text-white' : 'text-gray-400'}`}>
                          {notif.message}
                        </p>
                        <p className="mt-1 text-xs text-gray-500">
                          {new Date(notif.createdAt).toLocaleString()}
                        </p>
                      </div>
                    ))
                  )}
                </div>
                <div className="px-4 py-2 border-t border-[#2a2a4a] text-center">
                  <button className="text-xs text-[#6366f1] hover:text-[#4f46e5]">
                    View all
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* User Menu */}
          <div className="relative">
            <button
              onClick={(e) => {
                e.stopPropagation();
                setShowUserMenu(!showUserMenu);
                setShowNotifications(false);
              }}
              className="flex items-center gap-2 p-1.5 rounded-lg hover:bg-[#0a0a1a] transition"
            >
              <div className="w-8 h-8 rounded-full bg-[#6366f1]/20 flex items-center justify-center">
                <User className="w-4 h-4 text-[#6366f1]" />
              </div>
              <ChevronDown className="hidden w-4 h-4 text-gray-400 sm:block" />
            </button>

            {showUserMenu && (
              <div className="absolute right-0 mt-2 w-56 bg-[#1a1a2e] border border-[#2a2a4a] rounded-lg shadow-xl overflow-hidden z-50">
                <div className="px-4 py-3 border-b border-[#2a2a4a]">
                  <p className="text-sm font-medium text-white">{user?.fullName || 'User'}</p>
                  <p className="text-xs text-gray-400">{user?.email || 'No email'}</p>
                  <div className="flex items-center gap-1 mt-1">
                    <span className={`text-xs px-2 py-0.5 rounded-full ${
                      user?.subscription?.isActive 
                        ? 'bg-green-500/20 text-green-400' 
                        : 'bg-yellow-500/20 text-yellow-400'
                    }`}>
                      {user?.subscription?.isActive ? '● Active' : 'Free Demo'}
                    </span>
                  </div>
                </div>
                <div className="py-1">
                  <Link
                    to="/settings"
                    className="flex items-center gap-3 px-4 py-2 text-sm text-gray-400 hover:bg-[#0a0a1a] hover:text-white transition"
                    onClick={() => setShowUserMenu(false)}
                  >
                    <Settings className="w-4 h-4" />
                    Settings
                  </Link>
                  <Link
                    to="/subscription"
                    className="flex items-center gap-3 px-4 py-2 text-sm text-gray-400 hover:bg-[#0a0a1a] hover:text-white transition"
                    onClick={() => setShowUserMenu(false)}
                  >
                    <Crown className="w-4 h-4" />
                    Subscription
                  </Link>
                  <Link
                    to="/help"
                    className="flex items-center gap-3 px-4 py-2 text-sm text-gray-400 hover:bg-[#0a0a1a] hover:text-white transition"
                    onClick={() => setShowUserMenu(false)}
                  >
                    <HelpCircle className="w-4 h-4" />
                    Help & Support
                  </Link>
                  <div className="border-t border-[#2a2a4a] my-1" />
                  <button
                    onClick={handleLogout}
                    className="flex items-center w-full gap-3 px-4 py-2 text-sm text-left text-red-400 transition hover:bg-red-500/10"
                  >
                    <LogOut className="w-4 h-4" />
                    Logout
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;