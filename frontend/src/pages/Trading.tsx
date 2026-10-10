import React, { useState, useEffect } from 'react';
import { useTradingStore } from '@/store/tradingStore';
import { useAuthStore } from '@/store/authStore';
import { marketApi } from '@/api/market';
import { exchangeApi } from '@/api/exchange';
import type { BitgetStatus } from '@/api/exchange';
import { toast } from 'react-hot-toast';
import { Link } from 'react-router-dom';
import { Info, Shield, Sparkles, TrendingUp, TrendingDown, Loader2 } from 'lucide-react';
import PositionSourceBadge from '@/components/PositionSourceBadge';

const MODE_STORAGE_KEY = 'jadota-trading-mode';

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
    isSubmitting,
  } = useTradingStore();

  // 🔥 Persist trading mode across page refreshes.
  const [tradingMode, setTradingMode] = useState<'demo' | 'live'>(() => {
    if (typeof window === 'undefined') return 'demo';
    return window.localStorage.getItem(MODE_STORAGE_KEY) === 'live'
      ? 'live'
      : 'demo';
  });

  const [symbol, setSymbol] = useState('BTC/USDT');
  const [side, setSide] = useState<'BUY' | 'SELL'>('BUY');
  const [orderType, setOrderType] = useState<'MARKET' | 'LIMIT'>('MARKET');
  const [size, setSize] = useState(0.001);
  const [price, setPrice] = useState<number | undefined>(undefined);
  const [stopLoss, setStopLoss] = useState<number | undefined>(undefined);
  const [takeProfit, setTakeProfit] = useState<number | undefined>(undefined);

  const [bitgetStatus, setBitgetStatus] = useState<BitgetStatus | null>(null);
  const [liveUsdt, setLiveUsdt] = useState<number | null>(null);
  const [isLiveSubmitting, setIsLiveSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (tradingMode === 'live') {
      if (!bitgetStatus?.connected) {
        toast.error('Connect your Bitget account in Settings → API Keys first');
        return;
      }
      if (orderType !== 'MARKET') {
        toast.error('Live mode currently supports Market orders only');
        return;
      }
      setIsLiveSubmitting(true);
      try {
        const result = await exchangeApi.placeManualOrder({
          symbol,
          side,
          size,
          type: 'MARKET',
          stopLoss,
          takeProfit,
        });
        toast.success(
          `✅ Live ${side} order placed on Bitget · #${(result.bitgetOrderId || '').slice(0, 8)}`
        );
        await Promise.all([
          fetchPositions(),
          fetchMarketPrices(),
          loadLiveBalance(),
        ]);
      } catch (error: any) {
        toast.error(error?.message || 'Live order failed');
      } finally {
        setIsLiveSubmitting(false);
      }
      return;
    }

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
        mode: 'demo',
      });
      if (result) {
        toast.success(`✅ Demo order placed successfully!`);
        await Promise.all([
          fetchPositions(),
          fetchBalance(),
          fetchDemoBalance(),
          fetchMarketPrices(),
        ]);
      }
    } catch (error: any) {
      toast.error(error.message || 'Failed to place order');
    }
  };

  const loadBitgetStatus = async () => {
    try {
      const status = await exchangeApi.getBitgetStatus();
      setBitgetStatus(status);
    } catch (error) {
      setBitgetStatus({ connected: false, exchange: 'bitget' });
    }
  };

  const loadLiveBalance = async () => {
    try {
      const data = await exchangeApi.getBalance('USDT');
      const usdt = data.balances.find((b) => b.asset.toUpperCase() === 'USDT');
      setLiveUsdt(usdt?.free ?? 0);
    } catch (error: any) {
      setLiveUsdt(null);
    }
  };

  useEffect(() => {
    fetchPositions();
    fetchBalance();
    fetchDemoBalance();
    fetchMarketPrices();
    loadBitgetStatus();

    const interval = setInterval(() => {
      fetchMarketPrices();
      fetchPositions();
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  // 🔥 Persist mode whenever it changes
  useEffect(() => {
    try {
      window.localStorage.setItem(MODE_STORAGE_KEY, tradingMode);
    } catch { /* localStorage unavailable — no-op */ }
  }, [tradingMode]);

  // 🔥 If Bitget disconnects while user is on 'live', force back to 'demo'
  useEffect(() => {
    if (
      tradingMode === 'live' &&
      bitgetStatus !== null &&
      bitgetStatus?.exchange &&
      !bitgetStatus.connected
    ) {
      setTradingMode('demo');
      toast.error('Bitget disconnected — switched back to Demo mode');
    }
  }, [bitgetStatus, tradingMode]);

  useEffect(() => {
    if (tradingMode === 'live' && bitgetStatus?.connected) {
      loadLiveBalance();
    }
  }, [tradingMode, bitgetStatus?.connected]);

  const openPositions = positions.filter((p) => p.status === 'OPEN');
  const totalPnl = openPositions.reduce((sum, p) => sum + (p.unrealizedPnl || 0), 0);
  const isBitgetConnected = !!bitgetStatus?.connected;
  const isLive = tradingMode === 'live';

  const displayBalance = isLive
    ? { total: liveUsdt ?? 0, available: liveUsdt ?? 0, locked: 0 }
    : {
        total: demoBalance?.total || user?.demoBalance || 0,
        available: demoBalance?.available || user?.demoBalance || 0,
        locked: demoBalance?.locked || 0,
      };

  return (
    <div className="grid grid-cols-1 gap-6 p-6 mx-auto lg:grid-cols-3 max-w-7xl">
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
                onClick={() => setTradingMode('demo')}
                className={`px-4 py-1.5 rounded-lg text-sm font-medium transition ${
                  tradingMode === 'demo' ? 'bg-[#6366f1] text-white' : 'text-gray-400 hover:text-white'
                }`}
              >
                📊 Demo
              </button>
              <button
                type="button"
                onClick={() => {
                  if (!isBitgetConnected) {
                    toast.error('Connect Bitget in Settings → API Keys first');
                    return;
                  }
                  setTradingMode('live');
                }}
                disabled={!isBitgetConnected}
                title={isBitgetConnected ? 'Place real orders on Bitget' : 'Connect Bitget to enable live trading'}
                className={`px-4 py-1.5 rounded-lg text-sm font-medium transition flex items-center gap-1 ${
                  tradingMode === 'live'
                    ? 'bg-red-500 text-white'
                    : isBitgetConnected
                      ? 'text-gray-400 hover:text-white'
                      : 'text-gray-600 cursor-not-allowed opacity-60'
                }`}
              >
                🔴 Live
                {!isBitgetConnected && (
                  <span className="text-[10px] text-yellow-400">(connect first)</span>
                )}
              </button>
            </div>
          </div>

          {isLive ? (
            <div className="p-3 mb-4 text-sm text-red-400 border rounded-lg bg-red-500/10 border-red-500/30">
              <div className="flex items-center gap-2">
                <Sparkles className="w-4 h-4" />
                <span className="font-medium">🔴 Live Mode — Real money will be spent from your Bitget spot balance</span>
              </div>
              <div className="mt-1 text-xs text-red-300/80">
                Orders are placed immediately at market price. No confirmation dialog.
              </div>
            </div>
          ) : (
            <div className="p-3 mb-4 text-sm text-blue-400 border rounded-lg bg-blue-500/10 border-blue-500/30">
              <div className="flex items-center gap-2">
                <Info className="w-4 h-4" />
                <span>📊 Demo Mode - No real money involved</span>
              </div>
              {isBitgetConnected && (
                <div className="mt-1 text-xs text-blue-400/70">
                  ⚡ Bitget connected — switch to Live to place real orders
                </div>
              )}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block mb-1 text-sm font-medium text-gray-400">Symbol</label>
              <select
                value={symbol}
                onChange={(e) => setSymbol(e.target.value)}
                className="w-full px-3 py-2 bg-[#0a0a1a] border border-[#2a2a4a] rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-[#6366f1]"
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
                  side === 'BUY' ? 'bg-green-500 text-white' : 'bg-[#0a0a1a] text-gray-400 hover:bg-[#2a2a4a]'
                }`}
              >
                BUY
              </button>
              <button
                type="button"
                onClick={() => setSide('SELL')}
                className={`py-3 rounded-lg font-semibold transition ${
                  side === 'SELL' ? 'bg-red-500 text-white' : 'bg-[#0a0a1a] text-gray-400 hover:bg-[#2a2a4a]'
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
                  orderType === 'MARKET' ? 'bg-[#6366f1] text-white' : 'bg-[#0a0a1a] text-gray-400 hover:bg-[#2a2a4a]'
                }`}
              >
                Market
              </button>
              <button
                type="button"
                onClick={() => setOrderType('LIMIT')}
                disabled={isLive}
                title={isLive ? 'Limit orders coming soon in live mode' : ''}
                className={`py-2 rounded-lg text-sm transition ${
                  orderType === 'LIMIT' ? 'bg-[#6366f1] text-white' : 'bg-[#0a0a1a] text-gray-400 hover:bg-[#2a2a4a]'
                } ${isLive ? 'opacity-40 cursor-not-allowed' : ''}`}
              >
                Limit {isLive && <span className="text-[10px] text-yellow-400">(soon)</span>}
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
                className="w-full px-3 py-2 bg-[#0a0a1a] border border-[#2a2a4a] rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-[#6366f1]"
              />
              {isLive && (
                <p className="mt-1 text-xs text-gray-500">
                  ≈ ${(size * (marketPrices.find((p) => p.symbol === symbol)?.price || 0)).toFixed(2)} at current market price
                </p>
              )}
            </div>

            {orderType === 'LIMIT' && !isLive && (
              <div>
                <label className="block mb-1 text-sm font-medium text-gray-400">Limit Price</label>
                <input
                  type="number"
                  value={price || ''}
                  onChange={(e) => setPrice(parseFloat(e.target.value))}
                  step="0.1"
                  className="w-full px-3 py-2 bg-[#0a0a1a] border border-[#2a2a4a] rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-[#6366f1]"
                />
              </div>
            )}

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block mb-1 text-sm font-medium text-gray-400">Stop Loss</label>
                <input
                  type="number"
                  value={stopLoss || ''}
                  onChange={(e) => setStopLoss(parseFloat(e.target.value))}
                  step="0.1"
                  placeholder="Optional"
                  className="w-full px-3 py-2 bg-[#0a0a1a] border border-[#2a2a4a] rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-[#6366f1]"
                />
              </div>
              <div>
                <label className="block mb-1 text-sm font-medium text-gray-400">Take Profit</label>
                <input
                  type="number"
                  value={takeProfit || ''}
                  onChange={(e) => setTakeProfit(parseFloat(e.target.value))}
                  step="0.1"
                  placeholder="Optional"
                  className="w-full px-3 py-2 bg-[#0a0a1a] border border-[#2a2a4a] rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-[#6366f1]"
                />
              </div>
            </div>

            <div className="flex justify-between text-sm text-gray-400 bg-[#0a0a1a] p-3 rounded-lg">
              <span>{isLive ? 'Bitget USDT Balance:' : 'Available Demo Balance:'}</span>
              <span className="font-medium text-white">${displayBalance.available.toFixed(2)}</span>
            </div>

            <button
              type="submit"
              disabled={isSubmitting || isLiveSubmitting}
              className={`w-full py-3 rounded-lg font-bold text-white transition ${
                side === 'BUY' ? 'bg-green-500 hover:bg-green-600' : 'bg-red-500 hover:bg-red-600'
              } disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2`}
            >
              {(isSubmitting || isLiveSubmitting) ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Processing...
                </>
              ) : (
                `${side === 'BUY' ? 'Buy' : 'Sell'} ${symbol} ${isLive ? '(LIVE)' : '(DEMO)'}`
              )}
            </button>
          </form>
        </div>

        {/* Open Positions */}
        <div className="bg-[#1a1a2e] rounded-xl p-6 border border-[#2a2a4a]">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-white">Open Positions</h3>
            <span className="text-sm text-gray-400">{openPositions.length} positions</span>
          </div>
          {openPositions.length === 0 ? (
            <p className="text-sm text-gray-400">No open positions</p>
          ) : (
            <div className="space-y-3">
              {openPositions.map((position) => (
                <PositionCard key={position.id} position={position} onClose={closePosition} />
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
              <span className={`font-medium ${isLive ? 'text-red-400' : 'text-blue-400'}`}>
                {isLive ? 'LIVE' : 'DEMO'}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Available</span>
              <span className="font-medium text-white">${displayBalance.available.toFixed(2)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Locked</span>
              <span className="font-medium text-white">${displayBalance.locked.toFixed(2)}</span>
            </div>
            <div className="flex justify-between border-t border-[#2a2a4a] pt-3">
              <span className="text-gray-400">Total</span>
              <span className="font-bold text-white">${displayBalance.total.toFixed(2)}</span>
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
          <div
            className={`p-3 mt-4 border rounded-lg ${
              isLive ? 'bg-red-500/10 border-red-500/30' : 'bg-yellow-500/10 border-yellow-500/30'
            }`}
          >
            <p
              className={`flex items-center justify-center gap-1 text-xs text-center ${
                isLive ? 'text-red-400' : 'text-yellow-400'
              }`}
            >
              <Shield className="w-3 h-3" />
              {isLive ? 'Live Mode - Real money at risk' : 'Demo Mode - No real money at risk'}
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
        <p className="flex items-center gap-2 font-semibold text-white">
          {position.symbol}
          <PositionSourceBadge source={position.source} />
        </p>
        <p className={`text-sm ${position.side === 'LONG' || position.side === 'BUY' ? 'text-green-400' : 'text-red-400'}`}>
          {position.side} × {position.size}
        </p>
        <p className="text-xs text-gray-400">Entry: ${position.entryPrice?.toFixed(2) || '0.00'}</p>
        <p className="text-xs text-gray-500">Current: ${position.currentPrice?.toFixed(2) || '0.00'}</p>
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