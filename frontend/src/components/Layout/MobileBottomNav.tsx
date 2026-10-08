import React from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { LayoutDashboard, CandlestickChart, Brain, LineChart, Menu } from 'lucide-react';

interface MobileBottomNavProps {
  onMoreClick: () => void;
}

const MobileBottomNav: React.FC<MobileBottomNavProps> = ({ onMoreClick }) => {
  const location = useLocation();

  const items = [
    { to: '/dashboard', icon: LayoutDashboard, label: 'Home' },
    { to: '/market-chart', icon: CandlestickChart, label: 'Chart' },
    { to: '/ai-trading', icon: Brain, label: 'Signals' },
    { to: '/analytics', icon: LineChart, label: 'Stats' },
  ];

  // Check if current route matches one of the tab items
  const isTabActive = items.some((item) => location.pathname.startsWith(item.to));

  return (
    <nav
      aria-label="Bottom navigation"
      className="fixed bottom-0 left-0 right-0 z-40 lg:hidden bg-[#1a1a2e]/95 backdrop-blur-md border-t border-[#2a2a4a] safe-area-bottom"
    >
      <div className="flex items-center justify-around h-16 px-1">
        {items.map((item) => {
          const Icon = item.icon;
          const active = location.pathname.startsWith(item.to);
          return (
            <NavLink
              key={item.to}
              to={item.to}
              className="flex flex-col items-center justify-center flex-1 h-full gap-0.5 transition"
            >
              <div
                className={`flex items-center justify-center w-10 h-8 rounded-lg transition ${
                  active ? 'bg-[#6366f1]/20' : ''
                }`}
              >
                <Icon
                  className={`w-5 h-5 transition ${
                    active ? 'text-[#6366f1]' : 'text-gray-400'
                  }`}
                />
              </div>
              <span
                className={`text-[10px] font-medium transition ${
                  active ? 'text-[#6366f1]' : 'text-gray-500'
                }`}
              >
                {item.label}
              </span>
            </NavLink>
          );
        })}

        {/* More tab — opens drawer */}
        <button
          onClick={onMoreClick}
          aria-label="More options"
          className="flex flex-col items-center justify-center flex-1 h-full gap-0.5 transition"
        >
          <div
            className={`flex items-center justify-center w-10 h-8 rounded-lg transition ${
              !isTabActive ? 'bg-[#6366f1]/20' : ''
            }`}
          >
            <Menu
              className={`w-5 h-5 transition ${
                !isTabActive ? 'text-[#6366f1]' : 'text-gray-400'
              }`}
            />
          </div>
          <span
            className={`text-[10px] font-medium transition ${
              !isTabActive ? 'text-[#6366f1]' : 'text-gray-500'
            }`}
          >
            More
          </span>
        </button>
      </div>
    </nav>
  );
};

export default MobileBottomNav;