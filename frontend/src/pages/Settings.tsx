import React, { useState, useEffect } from 'react';
import { useAuthStore } from '@/store/authStore';
import { toast } from 'react-hot-toast';
import { 
  User, Mail, Shield, Key, Bell, Moon, Sun, 
  Save, Loader2, CheckCircle, AlertCircle, AlertTriangle,
  RefreshCw, Trash2, ExternalLink
} from 'lucide-react';
import { Link } from 'react-router-dom';
import { exchangeApi } from '@/api/exchange';
import type { BitgetStatus } from '@/api/exchange';

interface SettingsData {
  fullName: string;
  email: string;
  notifications: {
    email: boolean;
    push: boolean;
    tradeAlerts: boolean;
    priceAlerts: boolean;
  };
  appearance: {
    theme: 'light' | 'dark';
    compact: boolean;
  };
  security: {
    twoFactorAuth: boolean;
    sessionTimeout: number;
  };
}

const Settings: React.FC = () => {
  const { user, updateUser } = useAuthStore();
  const [isLoading, setIsLoading] = useState(false);
  const [isSaved, setIsSaved] = useState(false);
  const [activeTab, setActiveTab] = useState<'profile' | 'security' | 'preferences' | 'api'>('profile');
  
  const [settings, setSettings] = useState<SettingsData>({
    fullName: user?.fullName || '',
    email: user?.email || '',
    notifications: {
      email: true,
      push: false,
      tradeAlerts: true,
      priceAlerts: true
    },
    appearance: {
      theme: 'dark',
      compact: false
    },
    security: {
      twoFactorAuth: false,
      sessionTimeout: 30
    }
  });

  // ============================================
  // Bitget API state
  // ============================================
  const [bitgetStatus, setBitgetStatus] = useState<BitgetStatus | null>(null);
  const [isLoadingStatus, setIsLoadingStatus] = useState(false);
  const [apiKey, setApiKey] = useState('');
  const [apiSecret, setApiSecret] = useState('');
  const [passphrase, setPassphrase] = useState('');
  const [isConnecting, setIsConnecting] = useState(false);
  const [isTesting, setIsTesting] = useState(false);
  const [isDisconnecting, setIsDisconnecting] = useState(false);

  const fetchBitgetStatus = async () => {
    setIsLoadingStatus(true);
    try {
      const status = await exchangeApi.getBitgetStatus();
      setBitgetStatus(status);
    } catch (error: any) {
      // A 401 here just means the user isn't logged in yet.
      // For any other failure, surface it so it's not silent.
      const msg = error?.message || 'Failed to fetch Bitget status';
      if (!msg.toLowerCase().includes('not authenticated') &&
          !msg.toLowerCase().includes('missing')) {
        toast.error(msg);
      }
      setBitgetStatus({ connected: false, exchange: 'bitget' });
    } finally {
      setIsLoadingStatus(false);
    }
  };

  // Fetch Bitget status when the API tab is opened
  useEffect(() => {
    if (activeTab === 'api') {
      fetchBitgetStatus();
    }
  }, [activeTab]);

  // ============================================
  // Bitget actions
  // ============================================
  const handleConnectBitget = async () => {
    const trimmedKey = apiKey.trim();
    const trimmedSecret = apiSecret.trim();
    const trimmedPass = passphrase.trim();

    if (!trimmedKey || !trimmedSecret || !trimmedPass) {
      toast.error('All three fields are required');
      return;
    }
    if (trimmedKey.length < 10 || trimmedSecret.length < 10) {
      toast.error('API key and secret look too short — check you copied them fully');
      return;
    }

    setIsConnecting(true);
    try {
      const result = await exchangeApi.connectBitget({
        api_key: trimmedKey,
        api_secret: trimmedSecret,
        passphrase: trimmedPass,
      });
      toast.success(result.message || 'Bitget connected successfully 🎉');
      // Wipe the sensitive fields from local state
      setApiKey('');
      setApiSecret('');
      setPassphrase('');
      setBitgetStatus(result.status);
    } catch (error: any) {
      toast.error(error?.message || 'Failed to connect Bitget');
    } finally {
      setIsConnecting(false);
    }
  };

  const handleTestBitget = async () => {
    setIsTesting(true);
    try {
      const result = await exchangeApi.testBitget();
      toast.success(result.message || 'Credentials are valid ✅');
      setBitgetStatus(result.status);
    } catch (error: any) {
      toast.error(error?.message || 'Credentials test failed');
      // Refresh status so `last_error` from the backend is displayed
      fetchBitgetStatus();
    } finally {
      setIsTesting(false);
    }
  };

  const handleDisconnectBitget = async () => {
    if (!window.confirm(
      'Disconnect Bitget?\n\n' +
      'Your stored API credentials will be deleted from our servers. ' +
      'Any open positions tracked here will no longer be reconciled with Bitget. ' +
      'You can reconnect at any time.'
    )) {
      return;
    }

    setIsDisconnecting(true);
    try {
      const result = await exchangeApi.disconnectBitget();
      toast.success(result.message || 'Bitget disconnected');
      setBitgetStatus({ connected: false, exchange: 'bitget' });
    } catch (error: any) {
      toast.error(error?.message || 'Failed to disconnect Bitget');
    } finally {
      setIsDisconnecting(false);
    }
  };

  // ============================================
  // Existing profile save handler
  // ============================================
  const handleSave = async () => {
    setIsLoading(true);
    try {
      await new Promise(resolve => setTimeout(resolve, 1000));
      setIsSaved(true);
      toast.success('Settings saved successfully!');
      setTimeout(() => setIsSaved(false), 3000);
    } catch (error) {
      toast.error('Failed to save settings');
    } finally {
      setIsLoading(false);
    }
  };

  const handleChange = (section: string, field: string, value: any) => {
    setSettings(prev => ({
      ...prev,
      [section]: {
        ...prev[section as keyof SettingsData],
        [field]: value
      }
    }));
  };

  return (
    <div className="max-w-4xl p-6 mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold text-white">Settings</h1>
          <p className="mt-1 text-gray-400">Manage your account preferences</p>
        </div>
        <button
          onClick={handleSave}
          disabled={isLoading}
          className="flex items-center gap-2 px-4 py-2 bg-[#6366f1] text-white rounded-lg hover:bg-[#4f46e5] transition disabled:opacity-50"
        >
          {isLoading ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : isSaved ? (
            <CheckCircle className="w-4 h-4" />
          ) : (
            <Save className="w-4 h-4" />
          )}
          {isLoading ? 'Saving...' : 'Save Changes'}
        </button>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 mb-6 border-b border-[#2a2a4a] pb-2">
        <TabButton
          active={activeTab === 'profile'}
          onClick={() => setActiveTab('profile')}
          icon={<User className="w-4 h-4" />}
          label="Profile"
        />
        <TabButton
          active={activeTab === 'security'}
          onClick={() => setActiveTab('security')}
          icon={<Shield className="w-4 h-4" />}
          label="Security"
        />
        <TabButton
          active={activeTab === 'preferences'}
          onClick={() => setActiveTab('preferences')}
          icon={<Bell className="w-4 h-4" />}
          label="Preferences"
        />
        <TabButton
          active={activeTab === 'api'}
          onClick={() => setActiveTab('api')}
          icon={<Key className="w-4 h-4" />}
          label="API Keys"
        />
      </div>

      {/* Profile Tab */}
      {activeTab === 'profile' && (
        <div className="space-y-6">
          <div className="bg-[#1a1a2e] rounded-xl p-6 border border-[#2a2a4a]">
            <h3 className="mb-4 text-lg font-semibold text-white">Profile Information</h3>
            <div className="space-y-4">
              <div>
                <label className="block mb-1 text-sm font-medium text-gray-400">
                  Full Name
                </label>
                <input
                  type="text"
                  value={settings.fullName}
                  onChange={(e) => handleChange('', 'fullName', e.target.value)}
                  className="w-full px-4 py-2 bg-[#0a0a1a] border border-[#2a2a4a] rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-[#6366f1]"
                />
              </div>
              <div>
                <label className="block mb-1 text-sm font-medium text-gray-400">
                  Email Address
                </label>
                <div className="flex items-center gap-2">
                  <input
                    type="email"
                    value={settings.email}
                    disabled
                    className="w-full px-4 py-2 bg-[#0a0a1a] border border-[#2a2a4a] rounded-lg text-gray-400 cursor-not-allowed"
                  />
                  <span className="text-sm text-green-400 whitespace-nowrap">✓ Verified</span>
                </div>
              </div>
              <div className="pt-4 border-t border-[#2a2a4a]">
                <p className="text-sm text-gray-400">
                  Member since {user?.createdAt ? new Date(user.createdAt).toLocaleDateString() : 'N/A'}
                </p>
                <p className="text-sm text-gray-400">
                  Role: <span className="font-medium text-white">{user?.role || 'User'}</span>
                </p>
              </div>
            </div>
          </div>

          <div className="bg-[#1a1a2e] rounded-xl p-6 border border-[#2a2a4a]">
            <h3 className="mb-4 text-lg font-semibold text-white">Subscription</h3>
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium text-white">
                  {user?.subscription?.isActive ? '🟢 Active' : '⚪ Free Demo'}
                </p>
                {user?.subscription?.expiresAt && (
                  <p className="text-sm text-gray-400">
                    Expires: {new Date(user.subscription.expiresAt).toLocaleDateString()}
                  </p>
                )}
              </div>
              {!user?.subscription?.isActive && (
                <Link to="/subscription">
                  <button className="px-4 py-2 bg-[#6366f1] text-white rounded-lg hover:bg-[#4f46e5] transition">
                    Upgrade
                  </button>
                </Link>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Security Tab */}
      {activeTab === 'security' && (
        <div className="space-y-6">
          <div className="bg-[#1a1a2e] rounded-xl p-6 border border-[#2a2a4a]">
            <h3 className="mb-4 text-lg font-semibold text-white">Security Settings</h3>
            <div className="space-y-4">
              <div className="flex justify-between items-center py-2 border-b border-[#2a2a4a]">
                <div>
                  <p className="font-medium text-white">Two-Factor Authentication</p>
                  <p className="text-sm text-gray-400">Add an extra layer of security</p>
                </div>
                <button
                  onClick={() => handleChange('security', 'twoFactorAuth', !settings.security.twoFactorAuth)}
                  className={`px-4 py-1.5 rounded-lg text-sm font-medium transition ${
                    settings.security.twoFactorAuth
                      ? 'bg-green-500/20 text-green-400'
                      : 'bg-[#2a2a4a] text-gray-400 hover:bg-[#3a3a5a]'
                  }`}
                >
                  {settings.security.twoFactorAuth ? '✅ Enabled' : 'Enable'}
                </button>
              </div>
              <div className="flex justify-between items-center py-2 border-b border-[#2a2a4a]">
                <div>
                  <p className="font-medium text-white">Session Timeout</p>
                  <p className="text-sm text-gray-400">Auto-logout after inactivity</p>
                </div>
                <select
                  value={settings.security.sessionTimeout}
                  onChange={(e) => handleChange('security', 'sessionTimeout', parseInt(e.target.value))}
                  className="px-3 py-1.5 bg-[#0a0a1a] border border-[#2a2a4a] rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-[#6366f1]"
                >
                  <option value={15}>15 minutes</option>
                  <option value={30}>30 minutes</option>
                  <option value={60}>1 hour</option>
                  <option value={120}>2 hours</option>
                </select>
              </div>
              <button className="w-full py-2 text-red-400 transition rounded-lg bg-red-500/20 hover:bg-red-500/30">
                Change Password
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Preferences Tab */}
      {activeTab === 'preferences' && (
        <div className="space-y-6">
          <div className="bg-[#1a1a2e] rounded-xl p-6 border border-[#2a2a4a]">
            <h3 className="mb-4 text-lg font-semibold text-white">Notifications</h3>
            <div className="space-y-3">
              <ToggleSwitch
                label="Email Notifications"
                description="Receive updates via email"
                checked={settings.notifications.email}
                onChange={(checked) => handleChange('notifications', 'email', checked)}
              />
              <ToggleSwitch
                label="Push Notifications"
                description="Receive push notifications in browser"
                checked={settings.notifications.push}
                onChange={(checked) => handleChange('notifications', 'push', checked)}
              />
              <ToggleSwitch
                label="Trade Alerts"
                description="Get notified when trades are executed"
                checked={settings.notifications.tradeAlerts}
                onChange={(checked) => handleChange('notifications', 'tradeAlerts', checked)}
              />
              <ToggleSwitch
                label="Price Alerts"
                description="Get notified of significant price movements"
                checked={settings.notifications.priceAlerts}
                onChange={(checked) => handleChange('notifications', 'priceAlerts', checked)}
              />
            </div>
          </div>

          <div className="bg-[#1a1a2e] rounded-xl p-6 border border-[#2a2a4a]">
            <h3 className="mb-4 text-lg font-semibold text-white">Appearance</h3>
            <div className="space-y-3">
              <div className="flex justify-between items-center py-2 border-b border-[#2a2a4a]">
                <div>
                  <p className="font-medium text-white">Theme</p>
                  <p className="text-sm text-gray-400">Choose your preferred theme</p>
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => handleChange('appearance', 'theme', 'dark')}
                    className={`p-2 rounded-lg transition ${
                      settings.appearance.theme === 'dark'
                        ? 'bg-[#6366f1]/20 text-[#6366f1] border border-[#6366f1]'
                        : 'bg-[#0a0a1a] text-gray-400 hover:text-white'
                    }`}
                  >
                    <Moon className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => handleChange('appearance', 'theme', 'light')}
                    className={`p-2 rounded-lg transition ${
                      settings.appearance.theme === 'light'
                        ? 'bg-[#6366f1]/20 text-[#6366f1] border border-[#6366f1]'
                        : 'bg-[#0a0a1a] text-gray-400 hover:text-white'
                    }`}
                  >
                    <Sun className="w-4 h-4" />
                  </button>
                </div>
              </div>
              <ToggleSwitch
                label="Compact Mode"
                description="Reduce spacing for more information density"
                checked={settings.appearance.compact}
                onChange={(checked) => handleChange('appearance', 'compact', checked)}
              />
            </div>
          </div>
        </div>
      )}

      {/* API Keys Tab */}
      {activeTab === 'api' && (
        <div className="space-y-6">
          {/* Loading state */}
          {isLoadingStatus && !bitgetStatus && (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="w-8 h-8 text-[#6366f1] animate-spin" />
            </div>
          )}

          {/* Connected state */}
          {bitgetStatus?.connected && (
            <div className="bg-[#1a1a2e] rounded-xl p-6 border border-green-500/30">
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-start gap-3">
                  <div className="p-2 rounded-lg bg-green-500/20">
                    <CheckCircle className="w-5 h-5 text-green-400" />
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-white">
                      Bitget Connected
                    </h3>
                    <p className="text-sm text-gray-400">
                      {bitgetStatus.testnet ? 'Testnet mode' : 'Live account'}
                      {bitgetStatus.connected_at && ` · since ${new Date(bitgetStatus.connected_at).toLocaleDateString()}`}
                    </p>
                  </div>
                </div>
                <button
                  onClick={fetchBitgetStatus}
                  disabled={isLoadingStatus}
                  className="p-2 text-gray-400 transition rounded-lg hover:text-white hover:bg-[#2a2a4a] disabled:opacity-50"
                  title="Refresh status"
                >
                  <RefreshCw className={`w-4 h-4 ${isLoadingStatus ? 'animate-spin' : ''}`} />
                </button>
              </div>

              <div className="p-4 space-y-2 text-sm rounded-lg bg-[#0a0a1a]">
                <div className="flex justify-between">
                  <span className="text-gray-400">API Key</span>
                  <span className="font-mono text-white">{bitgetStatus.api_key_masked || '••••'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Permissions</span>
                  <span className="text-white">{bitgetStatus.permissions || 'Read + Spot Trade'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Status</span>
                  <span className="text-green-400">● Active</span>
                </div>
                {bitgetStatus.last_used_at && (
                  <div className="flex justify-between">
                    <span className="text-gray-400">Last used</span>
                    <span className="text-gray-300">
                      {new Date(bitgetStatus.last_used_at).toLocaleString()}
                    </span>
                  </div>
                )}
                {bitgetStatus.last_error && (
                  <div className="pt-2 mt-2 border-t border-red-500/20">
                    <p className="text-xs text-red-400">
                      ⚠️ Last error: {bitgetStatus.last_error}
                    </p>
                  </div>
                )}
              </div>

              <div className="flex flex-wrap gap-3 mt-4">
                <button
                  onClick={handleTestBitget}
                  disabled={isTesting}
                  className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-white transition rounded-lg bg-[#2a2a4a] hover:bg-[#3a3a5a] disabled:opacity-50"
                >
                  {isTesting ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <RefreshCw className="w-4 h-4" />
                  )}
                  Test Connection
                </button>
                <button
                  onClick={handleDisconnectBitget}
                  disabled={isDisconnecting}
                  className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-red-400 transition rounded-lg bg-red-500/20 hover:bg-red-500/30 disabled:opacity-50"
                >
                  {isDisconnecting ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <Trash2 className="w-4 h-4" />
                  )}
                  Disconnect
                </button>
              </div>
            </div>
          )}

          {/* Not connected — show the form */}
          {bitgetStatus && !bitgetStatus.connected && (
            <div className="bg-[#1a1a2e] rounded-xl p-6 border border-[#2a2a4a]">
              <h3 className="mb-4 text-lg font-semibold text-white">API Keys</h3>
              <div className="space-y-4">

                {/* Security notice */}
                <div className="flex items-start gap-3 p-4 border rounded-lg bg-yellow-500/10 border-yellow-500/30">
                  <AlertCircle className="w-5 h-5 text-yellow-400 flex-shrink-0 mt-0.5" />
                  <div className="text-sm">
                    <p className="font-medium text-yellow-400">
                      Create a trading-only API key
                    </p>
                    <p className="mt-1 text-gray-400">
                      When you create the key on Bitget, enable <strong className="text-white">Read</strong> and <strong className="text-white">Spot Trade</strong> only.
                      Do <strong className="text-red-400">NOT</strong> enable Withdrawal or Transfer.
                    </p>
                    <a
                      href="https://www.bitget.com/account/newapi"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1 mt-2 text-yellow-400 hover:text-yellow-300"
                    >
                      Create API key on Bitget <ExternalLink className="w-3 h-3" />
                    </a>
                  </div>
                </div>

                {/* Key fields */}
                <div>
                  <label className="block mb-1 text-sm font-medium text-gray-400">
                    API Key
                  </label>
                  <input
                    type="text"
                    value={apiKey}
                    onChange={(e) => setApiKey(e.target.value)}
                    placeholder="Enter your Bitget API Key"
                    autoComplete="off"
                    spellCheck={false}
                    className="w-full px-4 py-2 font-mono text-sm bg-[#0a0a1a] border border-[#2a2a4a] rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-[#6366f1] placeholder-gray-500"
                  />
                </div>

                <div>
                  <label className="block mb-1 text-sm font-medium text-gray-400">
                    API Secret
                  </label>
                  <input
                    type="password"
                    value={apiSecret}
                    onChange={(e) => setApiSecret(e.target.value)}
                    placeholder="Enter your Bitget API Secret"
                    autoComplete="new-password"
                    spellCheck={false}
                    className="w-full px-4 py-2 font-mono text-sm bg-[#0a0a1a] border border-[#2a2a4a] rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-[#6366f1] placeholder-gray-500"
                  />
                </div>

                <div>
                  <label className="block mb-1 text-sm font-medium text-gray-400">
                    API Passphrase
                  </label>
                  <input
                    type="password"
                    value={passphrase}
                    onChange={(e) => setPassphrase(e.target.value)}
                    placeholder="Enter your Bitget API Passphrase"
                    autoComplete="new-password"
                    spellCheck={false}
                    className="w-full px-4 py-2 font-mono text-sm bg-[#0a0a1a] border border-[#2a2a4a] rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-[#6366f1] placeholder-gray-500"
                  />
                </div>

                {/* Connect button */}
                <button
                  onClick={handleConnectBitget}
                  disabled={
                    isConnecting ||
                    !apiKey.trim() ||
                    !apiSecret.trim() ||
                    !passphrase.trim()
                  }
                  className="flex items-center justify-center w-full gap-2 py-2 font-medium text-white transition rounded-lg bg-[#6366f1] hover:bg-[#4f46e5] disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isConnecting ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      Verifying with Bitget...
                    </>
                  ) : (
                    <>
                      <Key className="w-4 h-4" />
                      Connect Bitget Account
                    </>
                  )}
                </button>

                <div className="text-sm text-center text-gray-500">
                  <p>⚠️ Never share your API keys with anyone</p>
                  <p className="mt-1 text-xs">
                    Keys are encrypted with AES-256 and stored securely. We never have access to your funds.
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Info callout — always visible */}
          {bitgetStatus?.connected && (
            <div className="p-4 border rounded-lg bg-blue-500/10 border-blue-500/30">
              <div className="flex items-start gap-3">
                <AlertTriangle className="w-5 h-5 text-blue-400 flex-shrink-0 mt-0.5" />
                <div className="text-sm">
                  <p className="font-medium text-blue-400">How live trading works</p>
                  <p className="mt-1 text-gray-400">
                    When AI auto-trade fires, your app places a real spot order on Bitget
                    using these credentials. Funds stay in your Bitget account at all times.
                    Our servers never hold your money.
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

const TabButton: React.FC<{
  active: boolean;
  onClick: () => void;
  icon: React.ReactNode;
  label: string;
}> = ({ active, onClick, icon, label }) => (
  <button
    onClick={onClick}
    className={`flex items-center gap-2 px-4 py-2 rounded-lg transition ${
      active
        ? 'bg-[#6366f1]/20 text-[#6366f1] border border-[#6366f1]/30'
        : 'text-gray-400 hover:text-white hover:bg-[#2a2a4a]'
    }`}
  >
    {icon}
    <span className="text-sm font-medium">{label}</span>
  </button>
);

const ToggleSwitch: React.FC<{
  label: string;
  description: string;
  checked: boolean;
  onChange: (checked: boolean) => void;
}> = ({ label, description, checked, onChange }) => (
  <div className="flex justify-between items-center py-2 border-b border-[#2a2a4a] last:border-0">
    <div>
      <p className="font-medium text-white">{label}</p>
      <p className="text-sm text-gray-400">{description}</p>
    </div>
    <button
      onClick={() => onChange(!checked)}
      className={`w-12 h-6 rounded-full transition ${
        checked ? 'bg-[#6366f1]' : 'bg-[#2a2a4a]'
      }`}
    >
      <div
        className={`w-5 h-5 bg-white rounded-full transition transform ${
          checked ? 'translate-x-6' : 'translate-x-0.5'
        }`}
      />
    </button>
  </div>
);

export default Settings;