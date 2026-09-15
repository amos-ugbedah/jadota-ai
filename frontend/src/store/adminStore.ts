import { create } from 'zustand';
import { adminApi } from '@/api/admin';
import type { SystemStatus, RevenueStats, SystemHealth } from '@/api/admin';
import type { User } from '@/api/auth';
import type { Subscription } from '@/api/subscription';
import { toast } from 'react-hot-toast';


// ... rest of the store stays the same

interface AdminState {
  users: User[];
  subscriptions: Subscription[];
  systemStatus: SystemStatus | null;
  revenue: RevenueStats | null;
  systemHealth: SystemHealth | null;
  isLoading: boolean;
  error: string | null;
  fetchUsers: (params?: { limit?: number; search?: string }) => Promise<void>;
  fetchSubscriptions: () => Promise<void>;
  fetchSystemStatus: () => Promise<void>;
  fetchRevenue: (period?: 'day' | 'week' | 'month' | 'year') => Promise<void>;
  fetchSystemHealth: () => Promise<void>;
  suspendUser: (id: string, reason?: string) => Promise<void>;
  restoreUser: (id: string) => Promise<void>;
  pauseAI: () => Promise<void>;
  resumeAI: () => Promise<void>;
  clearError: () => void;
  refreshAll: () => Promise<void>;
}

export const useAdminStore = create<AdminState>((set, get) => ({
  users: [],
  subscriptions: [],
  systemStatus: null,
  revenue: null,
  systemHealth: null,
  isLoading: false,
  error: null,

  fetchUsers: async (params) => {
    set({ isLoading: true, error: null });
    try {
      const users = await adminApi.getUsers(params);
      set({ users, isLoading: false });
    } catch (error: any) {
      const message = error.response?.data?.detail || error.message || 'Failed to fetch users';
      set({ error: message, isLoading: false });
      toast.error(message);
    }
  },

  fetchSubscriptions: async () => {
    set({ isLoading: true, error: null });
    try {
      const subscriptions = await adminApi.getSubscriptions();
      set({ subscriptions, isLoading: false });
    } catch (error: any) {
      const message = error.response?.data?.detail || error.message || 'Failed to fetch subscriptions';
      set({ error: message, isLoading: false });
      toast.error(message);
    }
  },

  fetchSystemStatus: async () => {
    try {
      const status = await adminApi.getSystemStatus();
      set({ systemStatus: status });
    } catch (error: any) {
      const message = error.response?.data?.detail || error.message || 'Failed to fetch system status';
      set({ error: message });
      toast.error(message);
    }
  },

  fetchRevenue: async (period = 'month') => {
    try {
      const revenue = await adminApi.getRevenue(period);
      set({ revenue });
    } catch (error: any) {
      const message = error.response?.data?.detail || error.message || 'Failed to fetch revenue';
      set({ error: message });
      toast.error(message);
    }
  },

  fetchSystemHealth: async () => {
    try {
      const health = await adminApi.getSystemHealth();
      set({ systemHealth: health });
    } catch (error: any) {
      const message = error.response?.data?.detail || error.message || 'Failed to fetch system health';
      set({ error: message });
      toast.error(message);
    }
  },

  suspendUser: async (id: string, reason?: string) => {
    try {
      await adminApi.suspendUser(id, reason);
      toast.success('User suspended successfully');
      await get().fetchUsers();
    } catch (error: any) {
      const message = error.response?.data?.detail || error.message || 'Failed to suspend user';
      toast.error(message);
    }
  },

  restoreUser: async (id: string) => {
    try {
      await adminApi.restoreUser(id);
      toast.success('User restored successfully');
      await get().fetchUsers();
    } catch (error: any) {
      const message = error.response?.data?.detail || error.message || 'Failed to restore user';
      toast.error(message);
    }
  },

  pauseAI: async () => {
    try {
      await adminApi.pauseAI();
      toast.success('AI Engine paused');
      await get().fetchSystemStatus();
    } catch (error: any) {
      const message = error.response?.data?.detail || error.message || 'Failed to pause AI';
      toast.error(message);
    }
  },

  resumeAI: async () => {
    try {
      await adminApi.resumeAI();
      toast.success('AI Engine resumed');
      await get().fetchSystemStatus();
    } catch (error: any) {
      const message = error.response?.data?.detail || error.message || 'Failed to resume AI';
      toast.error(message);
    }
  },

  clearError: () => set({ error: null }),

  refreshAll: async () => {
    set({ isLoading: true });
    try {
      await Promise.all([
        get().fetchUsers(),
        get().fetchSubscriptions(),
        get().fetchSystemStatus(),
        get().fetchRevenue(),
        get().fetchSystemHealth(),
      ]);
      set({ isLoading: false });
    } catch (error) {
      set({ isLoading: false });
    }
  },
}));