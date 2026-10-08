import React, { useEffect } from 'react';
import { X } from 'lucide-react';
import Sidebar from './Sidebar';

interface MobileDrawerProps {
  open: boolean;
  onClose: () => void;
}

const MobileDrawer: React.FC<MobileDrawerProps> = ({ open, onClose }) => {
  // Lock body scroll while open
  useEffect(() => {
    if (open) {
      const original = document.body.style.overflow;
      document.body.style.overflow = 'hidden';
      return () => {
        document.body.style.overflow = original;
      };
    }
  }, [open]);

  // Close on Escape key
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [open, onClose]);

  return (
    <>
      {/* Backdrop */}
      <div
        onClick={onClose}
        aria-hidden="true"
        className={`fixed inset-0 z-40 bg-black/60 backdrop-blur-sm transition-opacity duration-300 lg:hidden ${
          open ? 'opacity-100 pointer-events-auto' : 'opacity-0 pointer-events-none'
        }`}
      />

      {/* Drawer */}
      <div
        role="dialog"
        aria-modal="true"
        aria-label="Navigation menu"
        className={`fixed top-0 left-0 h-screen w-72 z-50 bg-[#1a1a2e] border-r border-[#2a2a4a] transform transition-transform duration-300 ease-out lg:hidden ${
          open ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        {/* Close button */}
        <button
          onClick={onClose}
          aria-label="Close menu"
          className="absolute top-4 right-4 z-10 p-2 rounded-lg text-gray-400 hover:text-white hover:bg-[#2a2a4a] transition"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Sidebar content — reuses desktop sidebar but sized for drawer */}
        <div className="h-full overflow-y-auto">
          <Sidebar onNavigate={onClose} />
        </div>
      </div>
    </>
  );
};

export default MobileDrawer;