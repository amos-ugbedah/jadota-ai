import React, { useState, useEffect } from 'react';
import { useTradingStore } from '@/store/tradingStore';
import { useAuthStore } from '@/store/authStore';
import { toast } from 'react-hot-toast';

const Trading: React.FC = () => {
  const { user } = useAuthStore();
  const { positions, balance, placeOrder, closePosition, fetchPositions, fetchBalance } = useTradingStore();
  
  const [symbol, setSymbol] = useState('BTC/USDT');
  const [side, setSide] = useState<'BUY' | 'SELL'>('BUY');
  const [orderType, setOrderType] = useState<'MARKET' | 'LIMIT'>('MARKET');
  const [size, setSize] = useState(0.001);
  const [price, setPrice] = useState<number | undefined>(undefined);
  const [stopLoss, setStopLoss] = useState<number | undefined>(undefined);
  const [takeProfit, setTakeProfit] = useState<number | undefined>(undefined);

  useEffect(() => {
    fetchPositions();
    fetchBalance();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!user?.subscription?.isActive && !user?.demoBalance) {
      toast.error('Please subscribe to trade live, or use demo trading');
      return;
    }

    try {
      await placeOrder({
        symbol,
        side,
        type: orderType,
        size,
        price,
        stopLoss,
        takeProfit,
      });
      toast.success('Order placed successfully!');
    } catch (error) {
      toast.error('Failed to place order');
    }
  };

  return (
    <div className="p-6 grid grid-cols-1 lg:grid-cols-3 gap-6">
      {/* Trading Panel */}
      <div className="lg:col-span-2 space-y-6">
        <div className="bg-jadota-card rounded-xl p-6 border border-jadota-border">
          <h2 className="text-xl font-bold text-white mb-4">Trading Panel</h2>
          
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Symbol */}
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-1">
                Symbol
              </label>
              <select
                value={symbol}
                onChange={(e) => setSymbol(e.target.value)}
                className="w-full px-3 py-2 bg-jadota-dark border border-jadota-border 
                         rounded-lg text-white focus:outline-none focus:ring-2 
                         focus:ring-primary-500"
              >
                <option value="BTC/USDT">BTC/USDT</option>
                <option value="ETH/USDT">ETH/USDT</option>
                <option value="SOL/USDT">SOL/USDT</option>
                <option value="BNB/USDT">BNB/USDT</option>
              </select>
            </div>

            {/* Side Toggle */}
            <div className="grid grid-cols-2 gap-2">
              <button
                type="button"
                onClick={() => setSide('BUY')}
                className={`py-3 rounded-lg font-semibold transition ${
                  side === 'BUY'
                    ? 'bg-green-500 text-white'
                    : 'bg-jadota-dark text-gray-400 hover:bg-jadota-border'
                }`}
              >
                BUY
              </button>
              <button
                type="button"
                onClick={() => setSide('SELL')}
                className={`py-3 rounded-lg font-semibold transition ${
                  side === 'SELL'
                    ? 'bg-red-500 text-white'
                    : 'bg-jadota-dark text-gray-400 hover:bg-jadota-border'
                }`}
              >
                SELL
              </button>
            </div>

            {/* Order Type */}
            <div className="grid grid-cols-2 gap-2">
              <button
                type="button"
                onClick={() => setOrderType('MARKET')}
                className={`py-2 rounded-lg text-sm transition ${
                  orderType === 'MARKET'
                    ? 'bg-primary-500 text-white'
                    : 'bg-jadota-dark text-gray-400 hover:bg-jadota-border'
                }`}
              >
                Market
              </button>
              <button
                type="button"
                onClick={() => setOrderType('LIMIT')}
                className={`py-2 rounded-lg text-sm transition ${
                  orderType === 'LIMIT'
                    ? 'bg-primary-500 text-white'
                    : 'bg-jadota-dark text-gray-400 hover:bg-jadota-border'
                }`}
              >
                Limit
              </button>
            </div>

            {/* Size */}
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-1">
                Size ({symbol.split('/')[0]})
              </label>
              <input
                type="number"
                value={size}
                onChange={(e) => setSize(parseFloat(e.target.value))}
                step="0.0001"
                min="0.0001"
                className="w-full px-3 py-2 bg-jadota-dark border border-jadota-border 
                         rounded-lg text-white focus:outline-none focus:ring-2 
                         focus:ring-primary-500"
              />
            </div>

            {/* Limit Price */}
            {orderType === 'LIMIT' && (
              <div>
                <label className="block text-sm font-medium text-gray-400 mb-1">
                  Limit Price
                </label>
                <input
                  type="number"
                  value={price || ''}
                  onChange={(e) => setPrice(parseFloat(e.target.value))}
                  step="0.1"
                  className="w-full px-3 py-2 bg-jadota-dark border border-jadota-border 
                           rounded-lg text-white focus:outline-none focus:ring-2 
                           focus:ring-primary-500"
                />
              </div>
            )}

            {/* Stop Loss & Take Profit */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-400 mb-1">
                  Stop Loss
                </label>
                <input
                  type="number"
                  value={stopLoss || ''}
                  onChange={(e) => setStopLoss(parseFloat(e.target.value))}
                  step="0.1"
                  className="w-full px-3 py-2 bg-jadota-dark border border-jadota-border 
                           rounded-lg text-white focus:outline-none focus:ring-2 
                           focus:ring-primary-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-400 mb-1">
                  Take Profit
                </label>
                <input
                  type="number"
                  value={takeProfit || ''}
                  onChange={(e) => setTakeProfit(parseFloat(e.target.value))}
                  step="0.1"
                  className="w-full px-3 py-2 bg-jadota-dark border border-jadota-border 
                           rounded-lg text-white focus:outline-none focus:ring-2 
                           focus:ring-primary-500"
                />
              </div>
            </div>

            {/* Submit */}
            <button
              type="submit"
              className={`w-full py-3 rounded-lg font-bold text-white transition ${
                side === 'BUY'
                  ? 'bg-green-500 hover:bg-green-600'
                  : 'bg-red-500 hover:bg-red-600'
              }`}
            >
              {side === 'BUY' ? 'Buy' : 'Sell'} {symbol}
            </button>
          </form>
        </div>

        {/* Positions */}
        <div className="bg-jadota-card rounded-xl p-6 border border-jadota-border">
          <h3 className="text-lg font-semibold text-white mb-4">Open Positions</h3>
          {positions.filter(p => p.status === 'OPEN').length === 0 ? (
            <p className="text-gray-400 text-sm">No open positions</p>
          ) : (
            <div className="space-y-3">
              {positions.filter(p => p.status === 'OPEN').map((position) => (
                <PositionCard
                  key={position.id}
                  position={position}
                  onClose={closePosition}
                />
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Sidebar Info */}
      <div className="space-y-6">
        <div className="bg-jadota-card rounded-xl p-6 border border-jadota-border">
          <h3 className="text-lg font-semibold text-white mb-4">Account Info</h3>
          <div className="space-y-3 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-400">Available</span>
              <span className="text-white font-medium">
                ${balance?.available?.toFixed(2) || '0.00'}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Locked</span>
              <span className="text-white font-medium">
                ${balance?.locked?.toFixed(2) || '0.00'}
              </span>
            </div>
            <div className="flex justify-between border-t border-jadota-border pt-3">
              <span className="text-gray-400">Total</span>
              <span className="text-white font-bold">
                ${balance?.total?.toFixed(2) || '0.00'}
              </span>
            </div>
          </div>
        </div>

        <div className="bg-jadota-card rounded-xl p-6 border border-jadota-border">
          <h3 className="text-lg font-semibold text-white mb-4">Quick Stats</h3>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-400">Open Positions</span>
              <span className="text-white">
                {positions.filter(p => p.status === 'OPEN').length}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Total P&L</span>
              <span className={`font-medium ${
                positions.reduce((sum, p) => sum + p.unrealizedPnl, 0) >= 0
                  ? 'text-green-400'
                  : 'text-red-400'
              }`}>
                ${positions.reduce((sum, p) => sum + p.unrealizedPnl, 0).toFixed(2)}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

const PositionCard: React.FC<{
  position: any;
  onClose: (id: string) => void;
}> = ({ position, onClose }) => (
  <div className="bg-jadota-dark rounded-lg p-4 border border-jadota-border">
    <div className="flex justify-between items-start">
      <div>
        <p className="font-semibold text-white">{position.symbol}</p>
        <p className={`text-sm ${position.side === 'LONG' ? 'text-green-400' : 'text-red-400'}`}>
          {position.side} × {position.size}
        </p>
        <p className="text-xs text-gray-400">
          Entry: ${position.entryPrice.toFixed(2)}
        </p>
      </div>
      <div className="text-right">
        <p className={`font-bold ${position.unrealizedPnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
          ${position.unrealizedPnl.toFixed(2)}
        </p>
        <button
          onClick={() => onClose(position.id)}
          className="mt-1 text-xs px-3 py-1 bg-red-500/20 text-red-400 
                   rounded hover:bg-red-500/30 transition"
        >
          Close
        </button>
      </div>
    </div>
  </div>
);

export default Trading;