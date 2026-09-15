import React, { useState, useEffect } from 'react';
import { useTradingStore } from '@/store/tradingStore';
import { useAuthStore } from '@/store/authStore';
import { toast } from 'react-hot-toast';
import { 
  TrendingUp, TrendingDown, X, RefreshCw, 
  ArrowUpRight, ArrowDownRight, Clock, DollarSign 
} from 'lucide-react';
import { format } from 'date-fns';

const Positions: React.FC = () => {
  const { user } = useAuthStore();
  const { positions, fetchPositions, closePosition, isLoading } = useTradingStore();
  const [selectedPosition, setSelectedPosition] = useState<any>(null);
  const [isClosing, setIsClosing] = useState(false);

  useEffect(() => {
    fetchPositions();
  }, []);

  const openPositions = positions.filter(p => p.status === 'OPEN');
  const closedPositions = positions.filter(p => p.status === 'CLOSED');

  const handleClosePosition = async (positionId: string) => {
    setIsClosing(true);
    try {
      await closePosition(positionId);
      toast.success('Position closed successfully!');
      setSelectedPosition(null);
    } catch (error: any) {
      toast.error(error.message || 'Failed to close position');
    } finally {
      setIsClosing(false);
    }
  };

  const totalPnl = openPositions.reduce((sum, p) => sum + (p.unrealizedPnl || 0), 0);
  const totalRealized = closedPositions.reduce((sum, p) => sum + (p.realizedPnl || 0), 0);

  return (
    <div className="p-6 mx-auto space-y-6 max-w-7xl">
      {/* Header */}
      <div className="flex flex-col items-start justify-between gap-4 sm:flex-row sm:items-center">
        <div>
          <h1 className="text-3xl font-bold text-white">Positions</h1>
          <p className="mt-1 text-gray-400">Manage your open and closed positions</p>
        </div>
        <button
          onClick={() => fetchPositions()}
          className="flex items-center gap-2 px-4 py-2 bg-[#1a1a2e] border border-[#2a2a4a] rounded-lg text-white hover:bg-[#2a2a4a] transition"
        >
          <RefreshCw className="w-4 h-4" />
          Refresh
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <PositionStat
          title="Open Positions"
          value={openPositions.length}
          icon={<Clock className="w-5 h-5 text-blue-400" />}
        />
        <PositionStat
          title="Unrealized P&L"
          value={`$${totalPnl.toFixed(2)}`}
          icon={totalPnl >= 0 ? 
            <TrendingUp className="w-5 h-5 text-green-400" /> : 
            <TrendingDown className="w-5 h-5 text-red-400" />
          }
          positive={totalPnl >= 0}
        />
        <PositionStat
          title="Realized P&L"
          value={`$${totalRealized.toFixed(2)}`}
          icon={<DollarSign className="w-5 h-5 text-yellow-400" />}
          positive={totalRealized >= 0}
        />
        <PositionStat
          title="Total Trades"
          value={positions.length}
          icon={<ArrowUpRight className="w-5 h-5 text-purple-400" />}
        />
      </div>

      {/* Open Positions */}
      <div className="bg-[#1a1a2e] rounded-xl border border-[#2a2a4a] overflow-hidden">
        <div className="px-6 py-4 border-b border-[#2a2a4a]">
          <h3 className="text-lg font-semibold text-white">
            Open Positions ({openPositions.length})
          </h3>
        </div>
        {openPositions.length === 0 ? (
          <div className="p-8 text-center">
            <p className="text-gray-400">No open positions</p>
            <p className="mt-2 text-sm text-gray-500">Start trading to see positions here</p>
          </div>
        ) : (
          <div className="divide-y divide-[#2a2a4a]">
            {openPositions.map((position) => (
              <PositionRow
                key={position.id}
                position={position}
                onClose={() => handleClosePosition(position.id)}
                onSelect={() => setSelectedPosition(position)}
                isClosing={isClosing}
              />
            ))}
          </div>
        )}
      </div>

      {/* Closed Positions */}
      {closedPositions.length > 0 && (
        <div className="bg-[#1a1a2e] rounded-xl border border-[#2a2a4a] overflow-hidden">
          <div className="px-6 py-4 border-b border-[#2a2a4a]">
            <h3 className="text-lg font-semibold text-white">
              Closed Positions ({closedPositions.length})
            </h3>
          </div>
          <div className="divide-y divide-[#2a2a4a]">
            {closedPositions.slice(0, 10).map((position) => (
              <ClosedPositionRow key={position.id} position={position} />
            ))}
          </div>
        </div>
      )}

      {/* Position Detail Modal */}
      {selectedPosition && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80">
          <div className="bg-[#1a1a2e] rounded-xl border border-[#2a2a4a] max-w-md w-full p-6">
            <div className="flex items-start justify-between mb-4">
              <h3 className="text-xl font-bold text-white">
                Position Details
              </h3>
              <button
                onClick={() => setSelectedPosition(null)}
                className="text-gray-400 hover:text-white"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="space-y-3 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-400">Symbol</span>
                <span className="font-medium text-white">{selectedPosition.symbol}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Side</span>
                <span className={selectedPosition.side === 'LONG' ? 'text-green-400' : 'text-red-400'}>
                  {selectedPosition.side}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Size</span>
                <span className="text-white">{selectedPosition.size}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Entry Price</span>
                <span className="text-white">${selectedPosition.entryPrice?.toFixed(2)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Current Price</span>
                <span className="text-white">${selectedPosition.currentPrice?.toFixed(2)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Unrealized P&L</span>
                <span className={selectedPosition.unrealizedPnl >= 0 ? 'text-green-400' : 'text-red-400'}>
                  ${selectedPosition.unrealizedPnl?.toFixed(2)}
                </span>
              </div>
              {selectedPosition.stopLoss && (
                <div className="flex justify-between">
                  <span className="text-gray-400">Stop Loss</span>
                  <span className="text-red-400">${selectedPosition.stopLoss}</span>
                </div>
              )}
              {selectedPosition.takeProfit && (
                <div className="flex justify-between">
                  <span className="text-gray-400">Take Profit</span>
                  <span className="text-green-400">${selectedPosition.takeProfit}</span>
                </div>
              )}
              <div className="flex justify-between">
                <span className="text-gray-400">Opened</span>
                <span className="text-xs text-gray-400">
                  {format(new Date(selectedPosition.openedAt), 'MMM d, HH:mm')}
                </span>
              </div>
            </div>
            <button
              onClick={() => handleClosePosition(selectedPosition.id)}
              disabled={isClosing}
              className="w-full py-2 mt-6 font-medium text-white transition bg-red-500 rounded-lg hover:bg-red-600 disabled:opacity-50"
            >
              {isClosing ? 'Closing...' : 'Close Position'}
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

const PositionStat: React.FC<{
  title: string;
  value: number | string;
  icon: React.ReactNode;
  positive?: boolean;
}> = ({ title, value, icon, positive = true }) => (
  <div className="bg-[#1a1a2e] rounded-xl p-6 border border-[#2a2a4a]">
    <div className="flex items-start justify-between">
      <div>
        <p className="text-sm font-medium text-gray-400">{title}</p>
        <p className={`text-2xl font-bold mt-1 ${positive !== undefined ? (positive ? 'text-green-400' : 'text-red-400') : 'text-white'}`}>
          {value}
        </p>
      </div>
      <div className="p-2.5 bg-[#6366f1]/10 rounded-lg">
        {icon}
      </div>
    </div>
  </div>
);

const PositionRow: React.FC<{
  position: any;
  onClose: () => void;
  onSelect: () => void;
  isClosing: boolean;
}> = ({ position, onClose, onSelect, isClosing }) => (
  <div className="px-6 py-4 hover:bg-[#0a0a1a]/50 transition cursor-pointer" onClick={onSelect}>
    <div className="flex flex-col items-start justify-between gap-4 sm:flex-row sm:items-center">
      <div className="flex items-center gap-4">
        <div className={`w-2 h-8 rounded-full ${position.side === 'LONG' ? 'bg-green-400' : 'bg-red-400'}`} />
        <div>
          <p className="font-semibold text-white">{position.symbol}</p>
          <div className="flex items-center gap-3 text-sm">
            <span className={position.side === 'LONG' ? 'text-green-400' : 'text-red-400'}>
              {position.side}
            </span>
            <span className="text-gray-400">× {position.size}</span>
            <span className="text-xs text-gray-500">
              Entry: ${position.entryPrice?.toFixed(2)}
            </span>
          </div>
        </div>
      </div>
      <div className="flex items-center justify-between w-full gap-6 sm:w-auto sm:justify-end">
        <div className="text-right">
          <p className="font-bold">${position.currentPrice?.toFixed(2)}</p>
          <p className={`text-sm font-medium ${position.unrealizedPnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
            ${position.unrealizedPnl?.toFixed(2)}
          </p>
        </div>
        <button
          onClick={(e) => {
            e.stopPropagation();
            onClose();
          }}
          disabled={isClosing}
          className="px-3 py-1 text-sm text-red-400 transition rounded-lg bg-red-500/20 hover:bg-red-500/30 disabled:opacity-50"
        >
          {isClosing ? '...' : 'Close'}
        </button>
      </div>
    </div>
  </div>
);

const ClosedPositionRow: React.FC<{ position: any }> = ({ position }) => (
  <div className="px-6 py-3">
    <div className="flex flex-col items-start justify-between gap-2 sm:flex-row sm:items-center">
      <div className="flex items-center gap-3">
        <span className="font-medium text-white">{position.symbol}</span>
        <span className={`text-sm ${position.side === 'LONG' ? 'text-green-400' : 'text-red-400'}`}>
          {position.side}
        </span>
        <span className="text-xs text-gray-500">× {position.size}</span>
      </div>
      <div className="flex items-center gap-6">
        <span className="text-sm text-gray-400">
          ${position.entryPrice?.toFixed(2)} → ${position.currentPrice?.toFixed(2)}
        </span>
        <span className={`font-medium ${position.realizedPnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
          ${position.realizedPnl?.toFixed(2)}
        </span>
        <span className="text-xs text-gray-500">
          {format(new Date(position.closedAt || position.openedAt), 'MMM d')}
        </span>
      </div>
    </div>
  </div>
);

export default Positions;