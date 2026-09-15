import React, { useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { useAuthStore } from './store/authStore';

// Layout
import AppLayout from './components/Layout/AppLayout';

// Pages
import Dashboard from './pages/Dashboard';
import Trading from './pages/Trading';
import AITrading from './pages/AITrading';
import TradingDashboard from './pages/TradingDashboard';
import AISettingsPage from './pages/AISettingsPage';
import Positions from './pages/Positions';
import Subscription from './pages/Subscription';
import Settings from './pages/Settings';
import Backtesting from './pages/Backtesting';
import MarketChart from './pages/MarketChart';
import Login from './pages/Login';
import Register from './pages/Register';

// Admin Pages
import AdminDashboard from './pages/Admin/AdminDashboard';
import Users from './pages/Admin/Users';
import Subscriptions from './pages/Admin/Subscriptions';
import System from './pages/Admin/System';

function App() {
  const { checkAuth, isLoading, isAuthenticated } = useAuthStore();

  useEffect(() => {
    console.log('🚀 App mounted, checking auth...');
    checkAuth();
  }, []);

  // 🔥 Show loading spinner while checking auth
  if (isLoading) {
    // 🔥 Force loading to resolve after 3 seconds (fallback)
    setTimeout(() => {
      const state = useAuthStore.getState();
      if (state.isLoading) {
        console.warn('⚠️ Loading timeout - forcing auth resolution');
        useAuthStore.setState({ 
          isLoading: false, 
          isAuthenticated: false, 
          user: null 
        });
      }
    }, 3000);

    return (
      <div className="min-h-screen bg-[#0a0a1a] flex items-center justify-center">
        <div className="text-center">
          <img src="/jadota-icon.png" alt="JADOTA AI" className="w-16 h-16 mx-auto mb-4 animate-pulse" />
          <div className="w-12 h-12 border-4 border-[#6366f1] border-t-transparent rounded-full animate-spin mx-auto" />
          <p className="mt-4 text-gray-400">Loading JADOTA...</p>
          <p className="mt-2 text-sm text-gray-500">If this takes too long, check backend is running</p>
        </div>
      </div>
    );
  }

  console.log('✅ App loaded, isAuthenticated:', isAuthenticated);

  return (
    <BrowserRouter>
      <Toaster 
        position="top-right"
        toastOptions={{
          style: {
            background: '#1a1a2e',
            color: '#fff',
            border: '1px solid #2a2a4a',
          },
        }}
      />
      <Routes>
        {/* Public Routes - Redirect to dashboard if already authenticated */}
        <Route path="/login" element={isAuthenticated ? <Navigate to="/dashboard" /> : <Login />} />
        <Route path="/register" element={isAuthenticated ? <Navigate to="/dashboard" /> : <Register />} />
        
        {/* Protected Routes - Redirect to login if not authenticated */}
        <Route path="/" element={!isAuthenticated ? <Navigate to="/login" /> : <AppLayout />}>
          <Route index element={<Navigate to="/dashboard" />} />
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="trading" element={<Trading />} />
          <Route path="market-chart" element={<MarketChart />} />
          <Route path="ai-trading" element={<AITrading />} />
          <Route path="trading-dashboard" element={<TradingDashboard />} />
          <Route path="ai-settings" element={<AISettingsPage />} />
          <Route path="positions" element={<Positions />} />
          <Route path="subscription" element={<Subscription />} />
          <Route path="settings" element={<Settings />} />
          <Route path="backtesting" element={<Backtesting />} />
          
          {/* Admin Routes */}
          <Route path="admin" element={<AdminDashboard />} />
          <Route path="admin/users" element={<Users />} />
          <Route path="admin/subscriptions" element={<Subscriptions />} />
          <Route path="admin/system" element={<System />} />
        </Route>
        
        {/* Catch all - redirect to dashboard */}
        <Route path="*" element={<Navigate to="/dashboard" />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;