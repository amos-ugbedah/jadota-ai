import React, { useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';

// Layout
import AppLayout from './components/Layout/AppLayout';

// Pages
import Dashboard from './pages/Dashboard';
import Trading from './pages/Trading';
import Positions from './pages/Positions';
import Subscription from './pages/Subscription';
import Settings from './pages/Settings';
import Backtesting from './pages/Backtesting';
import Login from './pages/Login';
import Register from './pages/Register';

// Admin Pages
import AdminDashboard from './pages/Admin/AdminDashboard';
import Users from './pages/Admin/Users';
import Subscriptions from './pages/Admin/Subscriptions';
import System from './pages/Admin/System';

function App() {
  return (
    <BrowserRouter>
      <Toaster position="top-right" />
      <Routes>
        {/* Public Routes */}
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        
        {/* Protected Routes */}
        <Route path="/" element={<AppLayout />}>
          <Route index element={<Navigate to="/dashboard" />} />
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="trading" element={<Trading />} />
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
        
        <Route path="*" element={<Navigate to="/dashboard" />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;