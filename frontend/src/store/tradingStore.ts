import { create } from 'zustand';
import { tradingApi } from '@/api/trading';
import { marketApi } from '@/api/market';
import type { Position, Trade, Balance, OrderRequest } from '@/api/trading';
import { toast } from 'react-hot-toast';

interface TradingState {
  positions: Position[];
  trades: Trade[];
  balance: Balance | null;
  demoBalance: Balance | null;
  marketPrices: any[];
  isLoading: boolean;
  isSubmitting: boolean;
  error: string | null;
  fetchPositions: () => Promise<void>;
  fetchTrades: (limit?: number) => Promise<void>;
  fetchBalance: () => Promise<void>;
  fetchDemoBalance: () => Promise<void>;
  fetchMarketPrices: () => Promise<void>;
  closePosition: (id: string) => Promise<void>;
  placeOrder: (data: OrderRequest & { mode?: 'demo' | 'live' }) => Promise<Trade | null>;
  updatePosition: (position: Position) => void;
  clearError: () => void;
  refreshAll: () => Promise<void>;
}

export const useTradingStore = create<TradingState>((set, get) => ({
  positions: [],
  trades: [],
  balance: null,
  demoBalance: null,
  marketPrices: [],
  isLoading: false,
  isSubmitting: false,
  error: null,

  fetchPositions: async () => {
    set({ isLoading: true, error: null });
    try {
      const positions = await tradingApi.getPositions();
      set({ positions, isLoading: false });
    } catch (error: any) {
      const message = error.response?.data?.detail || error.message || 'Failed to fetch positions';
      set({ error: message, isLoading: false });
      toast.error(message);
    }
  },

  fetchTrades: async (limit: number = 50) => {
    set({ isLoading: true, error: null });
    try {
      const trades = await tradingApi.getTradeHistory({ limit });
      set({ trades, isLoading: false });
    } catch (error: any) {
      const message = error.response?.data?.detail || error.message || 'Failed to fetch trades';
      set({ error: message, isLoading: false });
      toast.error(message);
    }
  },

  fetchBalance: async () => {
    try {
      const balance = await tradingApi.getBalance();
      set({ balance });
    } catch (error: any) {
      const message = error.response?.data?.detail || error.message || 'Failed to fetch balance';
      set({ error: message });
      toast.error(message);
    }
  },

  fetchDemoBalance: async () => {
    try {
      const demoBalance = await tradingApi.getDemoBalance();
      set({ demoBalance });
    } catch (error: any) {
      const message = error.response?.data?.detail || error.message || 'Failed to fetch demo balance';
      set({ error: message });
      toast.error(message);
    }
  },

  fetchMarketPrices: async () => {
    try {
      const marketPrices = await marketApi.getPrices();
      set({ marketPrices });
    } catch (error: any) {
      console.error('Failed to fetch market prices:', error);
    }
  },

  closePosition: async (id: string) => {
    set({ isSubmitting: true, error: null });
    try {
      await tradingApi.closePosition(id);
      toast.success('Position closed successfully!');
      await Promise.all([
        get().fetchPositions(),
        get().fetchBalance(),
        get().fetchDemoBalance(),
      ]);
      set({ isSubmitting: false });
    } catch (error: any) {
      const message = error.response?.data?.detail || error.message || 'Failed to close position';
      set({ error: message, isSubmitting: false });
      toast.error(message);
    }
  },

  placeOrder: async (data: OrderRequest & { mode?: 'demo' | 'live' }) => {
    set({ isSubmitting: true, error: null });
    try {
      let response: Trade;
      
      if (data.mode === 'demo') {
        response = await tradingApi.placeDemoOrder(data);
        await get().fetchDemoBalance();
      } else {
        response = await tradingApi.placeOrder(data);
        await get().fetchBalance();
      }
      
      await Promise.all([
        get().fetchPositions(),
        get().fetchTrades(10),
        get().fetchMarketPrices(),
      ]);
      
      set({ isSubmitting: false });
      toast.success(`✅ ${data.mode?.toUpperCase() || 'Demo'} order placed successfully!`);
      return response;
    } catch (error: any) {
      const message = error.response?.data?.detail || error.message || 'Failed to place order';
      set({ error: message, isSubmitting: false });
      toast.error(message);
      return null;
    }
  },

  updatePosition: (position: Position) => {
    set((state) => ({
      positions: state.positions.map((p) =>
        p.id === position.id ? position : p
      ),
    }));
  },

  clearError: () => set({ error: null }),

  refreshAll: async () => {
    set({ isLoading: true });
    try {
      await Promise.all([
        get().fetchPositions(),
        get().fetchTrades(50),
        get().fetchBalance(),
        get().fetchDemoBalance(),
        get().fetchMarketPrices(),
      ]);
      set({ isLoading: false });
    } catch (error) {
      set({ isLoading: false });
    }
  },
}));