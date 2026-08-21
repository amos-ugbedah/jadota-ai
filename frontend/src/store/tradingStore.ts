import { create } from 'zustand';

interface Position {
  id: string;
  symbol: string;
  side: 'LONG' | 'SHORT';
  size: number;
  entryPrice: number;
  currentPrice: number;
  unrealizedPnl: number;
  realizedPnl: number;
  stopLoss?: number;
  takeProfit?: number;
  openedAt: string;
  status: 'OPEN' | 'CLOSED';
}

interface Trade {
  id: string;
  symbol: string;
  side: 'BUY' | 'SELL';
  price: number;
  size: number;
  fee: number;
  executedAt: string;
  status: 'PENDING' | 'FILLED' | 'CANCELLED' | 'REJECTED';
}

interface Balance {
  total: number;
  available: number;
  locked: number;
}

interface TradingState {
  positions: Position[];
  trades: Trade[];
  balance: Balance | null;
  isLoading: boolean;
  error: string | null;
  fetchPositions: () => Promise<void>;
  fetchTrades: () => Promise<void>;
  fetchBalance: () => Promise<void>;
  closePosition: (id: string) => Promise<void>;
  placeOrder: (data: any) => Promise<void>;
  updatePosition: (position: Position) => void;
  clearError: () => void;
}

// Mock API functions (temporary)
const mockApi = {
  getPositions: async (): Promise<Position[]> => [],
  getTradeHistory: async (): Promise<Trade[]> => [],
  getBalance: async (): Promise<Balance> => ({ total: 0, available: 0, locked: 0 }),
  closePosition: async (id: string) => {},
  placeOrder: async (data: any) => {},
};

export const useTradingStore = create<TradingState>((set, get) => ({
  positions: [],
  trades: [],
  balance: null,
  isLoading: false,
  error: null,

  fetchPositions: async () => {
    set({ isLoading: true, error: null });
    try {
      const positions = await mockApi.getPositions();
      set({ positions, isLoading: false });
    } catch (error: any) {
      set({ error: error.message || 'Failed to fetch positions', isLoading: false });
    }
  },

  fetchTrades: async () => {
    set({ isLoading: true, error: null });
    try {
      const trades = await mockApi.getTradeHistory();
      set({ trades, isLoading: false });
    } catch (error: any) {
      set({ error: error.message || 'Failed to fetch trades', isLoading: false });
    }
  },

  fetchBalance: async () => {
    try {
      const balance = await mockApi.getBalance();
      set({ balance });
    } catch (error: any) {
      set({ error: error.message || 'Failed to fetch balance' });
    }
  },

  closePosition: async (id) => {
    try {
      await mockApi.closePosition(id);
      await get().fetchPositions();
    } catch (error: any) {
      set({ error: error.message || 'Failed to close position' });
    }
  },

  placeOrder: async (data) => {
    try {
      await mockApi.placeOrder(data);
      await Promise.all([
        get().fetchPositions(),
        get().fetchTrades(),
        get().fetchBalance(),
      ]);
    } catch (error: any) {
      set({ error: error.message || 'Failed to place order' });
    }
  },

  updatePosition: (position) => {
    set((state) => ({
      positions: state.positions.map((p) =>
        p.id === position.id ? position : p
      ),
    }));
  },

  clearError: () => set({ error: null }),
}));