import React, { useState } from 'react';
import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';
import MobileDrawer from './MobileDrawer';
import MobileBottomNav from './MobileBottomNav';
import Header from './Header';

const AppLayout: React.FC = () => {
  const [drawerOpen, setDrawerOpen] = useState(false);

  return (
    <div className="min-h-screen bg-[#0a0a1a]">
      {/* ============================================ */}
      {/* Desktop sidebar — fixed, hidden on mobile */}
      {/* ============================================ */}
      <div className="fixed top-0 left-0 z-40 hidden w-64 h-screen lg:block">
        <Sidebar />
      </div>

      {/* ============================================ */}
      {/* Mobile drawer */}
      {/* ============================================ */}
      <MobileDrawer open={drawerOpen} onClose={() => setDrawerOpen(false)} />

      {/* ============================================ */}
      {/* Main content area */}
      {/* ============================================ */}
      <div className="flex flex-col min-h-screen lg:ml-64">
        {/* Header — pass a handler so it can open the drawer on mobile */}
        <Header onMenuClick={() => setDrawerOpen(true)} />

        {/* Page content — padded bottom on mobile to leave room for bottom nav */}
        <main className="flex-1 pb-20 lg:pb-0">
          <Outlet />
        </main>
      </div>

      {/* ============================================ */}
      {/* Mobile bottom nav */}
      {/* ============================================ */}
      <MobileBottomNav onMoreClick={() => setDrawerOpen(true)} />
    </div>
  );
};

export default AppLayout;