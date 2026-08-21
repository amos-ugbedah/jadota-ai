import React from 'react';
import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';
import Header from './Header';

const AppLayout: React.FC = () => {
  return (
    <div className="min-h-screen bg-[#0a0a1a]">
      <Sidebar />
      <div className="ml-64">
        <Header />
        <main className="pt-16">
          <Outlet />
        </main>
      </div>
    </div>
  );
};

export default AppLayout;