import React, { useState, useEffect } from 'react';
import { useTradingStore } from '@/store/tradingStore';
import { useAuthStore } from '@/store/authStore';
import { marketApi } from '@/api/market';
import { toast } from 'react-hot-toast';
import { Link } from 'react-router-dom';
import { Info, Shield, Sparkles, TrendingUp, TrendingDown } from 'lucide-react';

const Trading: React.FC = () => {
  const { user } = useAuthStore();
  const { 
    positions, 
    balance, 
    demoBalance,
    marketPrices,
    placeOrder, 
    closePosition, 
    fetchPositions, 
    fetchBalance,
    fetchDemoBalance,
    fetchMarketPrices,
    isSubmitting 
  } = useTradingStore();
  
  const [tradingMode] = useState<'demo' | 'live'>('demo');
  const [symbol, setSymbol] = useState('BTC/USDT');
  const [side, setSide] = useState<'BUY' | 'SELL'>('BUY');
  const [orderType, setOrderType] = useState<'MARKET' | 'LIMIT'>('MARKET');
  const [size, setSize] = useState(0.001);
  const [price, setPrice] = useState<number | undefined>(undefined);
  const [stopLoss, setStopLoss] = useState<number | undefined>(undefined);
  const [takeProfit, setTakeProfit] = useState<number | undefined>(undefined);

  // Fetch market prices on load and every 5 seconds
  useEffect(() => {
    fetchPositions();
    fetchBalance();
    fetchDemoBalance();
    fetchMarketPrices();
    
    const interval = setInterval(() => {
      fetchMarketPrices();
      fetchPositions(); // Update positions with latest prices
    }, 5000);
    
    return () => clearInterval(interval);
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    const currentBalance = demoBalance?.available || user?.demoBalance || 0;
    const estimatedCost = size * 45000;
    
    if (currentBalance < estimatedCost) {
      toast.error(`❌ Insufficient demo balance! Available: $${currentBalance.toFixed(2)}`);
      return;
    }

    try {
      const result = await placeOrder({
        symbol,
        side,
        type: orderType,
        size,
        price,
        stopLoss,
        takeProfit,
        mode: 'demo'
      });
      
      if (result) {
        toast.success(`✅ Demo order placed successfully!`);
        await Promise.all([
          fetchPositions(),
          fetchBalance(),
          fetchDemoBalance(),
          fetchMarketPrices()
        ]);
      }
    } catch (error: any) {
      toast.error(error.message || 'Failed to place order');
    }
  };

  const openPositions = positions.filter(p => p.status === 'OPEN');
  const totalPnl = openPositions.reduce((sum, p) => sum + (p.unrealizedPnl || 0), 0);

  return (
    <div className="grid grid-cols-1 gap-6 p-6 mx-auto lg:grid-cols-3 max-w-7xl">
      {/* Left Column */}
      <div className="space-y-6 lg:col-span-2">
        {/* Live Market Prices */}
        <div className="bg-[#1a1a2e] rounded-xl p-4 border border-[#2a2a4a]">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold text-white">📊 Live Market Prices</h3>
            <span className="text-xs text-gray-400">Auto-updates</span>
          </div>
          <div className="grid grid-cols-2 gap-2 md:grid-cols-4">
            {marketPrices.slice(0, 8).map((item) => (
              <div 
                key={item.symbol} 
                className={`bg-[#0a0a1a] rounded-lg p-3 border border-[#2a2a4a] cursor-pointer hover:border-[#6366f1]/30 transition ${
                  symbol === item.symbol ? 'border-[#6366f1]' : ''
                }`}
                onClick={() => setSymbol(item.symbol)}
              >
                <p className="text-xs text-gray-400">{item.symbol}</p>
                <p className="text-sm font-bold text-white">${item.price.toFixed(2)}</p>
                <p className={`text-xs ${item.change24h >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                  {item.change24h >= 0 ? '↑' : '↓'} {Math.abs(item.change24h).toFixed(2)}%
                </p>
              </div>
            ))}
          </div>
        </div>

        {/* Trading Panel */}
        <div className="bg-[#1a1a2e] rounded-xl p-6 border border-[#2a2a4a]">
          <div className="flex flex-col items-start justify-between gap-3 mb-4 sm:flex-row sm:items-center">
            <h2 className="text-xl font-bold text-white">Trading Panel</h2>
            
            <div className="flex gap-1 bg-[#0a0a1a] rounded-lg p-1">
              <button
                type="button"
                className="px-4 py-1.5 rounded-lg text-sm font-medium bg-[#6366f1] text-white cursor-default"
              >
                📊 Demo
              </button>
              <button
                type="button"
                disabled
                className="px-4 py-1.5 rounded-lg text-sm font-medium text-gray-500 cursor-not-allowed opacity-50"
              >
                🔴 Live
                <span className="ml-1 text-[8px] text-yellow-400">(Soon)</span>
              </button>
            </div>
          </div>
          
          <div className="p-3 mb-4 text-sm text-blue-400 border rounded-lg bg-blue-500/10 border-blue-500/30">
            <div className="flex items-center gap-2">
              <Info className="w-4 h-4" />
              <span>📊 Demo Mode - No real money involved</span>
            </div>
            <div className="mt-1 text-xs text-blue-400/70">
              ⚡ Live trading is coming soon!
            </div>
          </div>
          
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block mb-1 text-sm font-medium text-gray-400">
                Symbol
              </label>
              <select
                value={symbol}
                onChange={(e) => setSymbol(e.target.value)}
                className="w-full px-3 py-2 bg-[#0a0a1a] border border-[#2a2a4a] 
                         rounded-lg text-white focus:outline-none focus:ring-2 
                         focus:ring-[#6366f1]"
              >
                <option value="BTC/USDT">BTC/USDT</option>
                <option value="ETH/USDT">ETH/USDT</option>
                <option value="SOL/USDT">SOL/USDT</option>
                <option value="BNB/USDT">BNB/USDT</option>
                <option value="XRP/USDT">XRP/USDT</option>
                <option value="DOGE/USDT">DOGE/USDT</option>
              </select>
            </div>

            <div className="grid grid-cols-2 gap-2">
              <button
                type="button"
                onClick={() => setSide('BUY')}
                className={`py-3 rounded-lg font-semibold transition ${
                  side === 'BUY'
                    ? 'bg-green-500 text-white'
                    : 'bg-[#0a0a1a] text-gray-400 hover:bg-[#2a2a4a]'
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
                    : 'bg-[#0a0a1a] text-gray-400 hover:bg-[#2a2a4a]'
                }`}
              >
                SELL
              </button>
            </div>

            <div className="grid grid-cols-2 gap-2">
              <button
                type="button"
                onClick={() => setOrderType('MARKET')}
                className={`py-2 rounded-lg text-sm transition ${
                  orderType === 'MARKET'
                    ? 'bg-[#6366f1] text-white'
                    : 'bg-[#0a0a1a] text-gray-400 hover:bg-[#2a2a4a]'
                }`}
              >
                Market
              </button>
              <button
                type="button"
                onClick={() => setOrderType('LIMIT')}
                className={`py-2 rounded-lg text-sm transition ${
                  orderType === 'LIMIT'
                    ? 'bg-[#6366f1] text-white'
                    : 'bg-[#0a0a1a] text-gray-400 hover:bg-[#2a2a4a]'
                }`}
              >
                Limit
              </button>
            </div>

            <div>
              <label className="block mb-1 text-sm font-medium text-gray-400">
                Size ({symbol.split('/')[0]})
              </label>
              <input
                type="number"
                value={size}
                onChange={(e) => setSize(parseFloat(e.target.value))}
                step="0.0001"
                min="0.0001"
                className="w-full px-3 py-2 bg-[#0a0a1a] border border-[#2a2a4a] 
                         rounded-lg text-white focus:outline-none focus:ring-2 
                         focus:ring-[#6366f1]"
              />
            </div>

            {orderType === 'LIMIT' && (
              <div>
                <label className="block mb-1 text-sm font-medium text-gray-400">
                  Limit Price
                </label>
                <input
                  type="number"
                  value={price || ''}
                  onChange={(e) => setPrice(parseFloat(e.target.value))}
                  step="0.1"
                  className="w-full px-3 py-2 bg-[#0a0a1a] border border-[#2a2a4a] 
                           rounded-lg text-white focus:outline-none focus:ring-2 
                           focus:ring-[#6366f1]"
                />
              </div>
            )}

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block mb-1 text-sm font-medium text-gray-400">
                  Stop Loss
                </label>
                <input
                  type="number"
                  value={stopLoss || ''}
                  onChange={(e) => setStopLoss(parseFloat(e.target.value))}
                  step="0.1"
                  className="w-full px-3 py-2 bg-[#0a0a1a] border border-[#2a2a4a] 
                           rounded-lg text-white focus:outline-none focus:ring-2 
                           focus:ring-[#6366f1]"
                />
              </div>
              <div>
                <label className="block mb-1 text-sm font-medium text-gray-400">
                  Take Profit
                </label>
                <input
                  type="number"
                  value={takeProfit || ''}
                  onChange={(e) => setTakeProfit(parseFloat(e.target.value))}
                  step="0.1"
                  className="w-full px-3 py-2 bg-[#0a0a1a] border border-[#2a2a4a] 
                           rounded-lg text-white focus:outline-none focus:ring-2 
                           focus:ring-[#6366f1]"
                />
              </div>
            </div>

            <div className="flex justify-between text-sm text-gray-400 bg-[#0a0a1a] p-3 rounded-lg">
              <span>Available Demo Balance:</span>
              <span className="font-medium text-white">
                ${(demoBalance?.available || user?.demoBalance || 0).toFixed(2)}
              </span>
            </div>

            <button
              type="submit"
              disabled={isSubmitting}
              className={`w-full py-3 rounded-lg font-bold text-white transition ${
                side === 'BUY'
                  ? 'bg-green-500 hover:bg-green-600'
                  : 'bg-red-500 hover:bg-red-600'
              } disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2`}
            >
              {isSubmitting ? (
                <>
                  <span className="animate-spin">⏳</span>
                  Processing...
                </>
              ) : (
                `${side === 'BUY' ? 'Buy' : 'Sell'} ${symbol} (DEMO)`
              )}
            </button>
          </form>
        </div>

        {/* Open Positions */}
        <div className="bg-[#1a1a2e] rounded-xl p-6 border border-[#2a2a4a]">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-white">Open Positions</h3>
            <span className="text-sm text-gray-400">
              {openPositions.length} positions
            </span>
          </div>
          {openPositions.length === 0 ? (
            <p className="text-sm text-gray-400">No open positions</p>
          ) : (
            <div className="space-y-3">
              {openPositions.map((position) => (
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
        <div className="bg-[#1a1a2e] rounded-xl p-6 border border-[#2a2a4a]">
          <h3 className="mb-4 text-lg font-semibold text-white">Account Info</h3>
          <div className="space-y-3 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-400">Mode</span>
              <span className="font-medium text-blue-400">DEMO</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Available</span>
              <span className="font-medium text-white">
                ${(demoBalance?.available || user?.demoBalance || 0).toFixed(2)}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Locked</span>
              <span className="font-medium text-white">
                ${(demoBalance?.locked || 0).toFixed(2)}
              </span>
            </div>
            <div className="flex justify-between border-t border-[#2a2a4a] pt-3">
              <span className="text-gray-400">Total</span>
              <span className="font-bold text-white">
                ${(demoBalance?.total || user?.demoBalance || 0).toFixed(2)}
              </span>
            </div>
          </div>
        </div>

        <div className="bg-[#1a1a2e] rounded-xl p-6 border border-[#2a2a4a]">
          <h3 className="mb-4 text-lg font-semibold text-white">Quick Stats</h3>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-400">Open Positions</span>
              <span className="text-white">{openPositions.length}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Total P&L</span>
              <span className={`font-medium ${totalPnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                ${totalPnl.toFixed(2)}
              </span>
            </div>
          </div>
          <div className="p-3 mt-4 border rounded-lg bg-yellow-500/10 border-yellow-500/30">
            <p className="flex items-center justify-center gap-1 text-xs text-center text-yellow-400">
              <Shield className="w-3 h-3" />
              Demo Mode - No real money at risk
            </p>
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
  <div className="bg-[#0a0a1a] rounded-lg p-4 border border-[#2a2a4a] hover:border-[#6366f1]/30 transition">
    <div className="flex items-start justify-between">
      <div>
        <p className="font-semibold text-white">{position.symbol}</p>
        <p className={`text-sm ${position.side === 'LONG' ? 'text-green-400' : 'text-red-400'}`}>
          {position.side} × {position.size}
        </p>
        <p className="text-xs text-gray-400">
          Entry: ${position.entryPrice?.toFixed(2) || '0.00'}
        </p>
        <p className="text-xs text-gray-500">
          Current: ${position.currentPrice?.toFixed(2) || '0.00'}
        </p>
      </div>
      <div className="text-right">
        <p className={`font-bold ${position.unrealizedPnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
          ${position.unrealizedPnl?.toFixed(2) || '0.00'}
        </p>
        <button
          onClick={() => onClose(position.id)}
          className="px-3 py-1 mt-1 text-xs text-red-400 transition rounded bg-red-500/20 hover:bg-red-500/30"
        >
          Close
        </button>
      </div>
    </div>
  </div>
);

export default Trading;