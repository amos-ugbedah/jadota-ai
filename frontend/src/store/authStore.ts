import { create } from 'zustand';
import { persist } from 'zustand/middleware';

// Define User type locally to avoid import issues
interface User {
  id: string;
  email: string;
  fullName: string;
  role: 'USER' | 'ADMIN' | 'SUPER_ADMIN';
  subscription: {
    plan: string | null;
    expiresAt: string | null;
    isActive: boolean;
  };
  demoBalance: number;
  createdAt: string;
}

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  login: (email: string, password: string) => Promise<void>;
  register: (data: any) => Promise<void>;
  logout: () => Promise<void>;
  checkAuth: () => Promise<void>;
  clearError: () => void;
}

// Mock auth API (temporary)
const mockAuthApi = {
  login: async (data: { email: string; password: string }) => {
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 500));
    return {
      user: {
        id: '1',
        email: data.email,
        fullName: 'Test User',
        role: 'USER' as const,
        subscription: { plan: null, expiresAt: null, isActive: false },
        demoBalance: 1000,
        createdAt: new Date().toISOString(),
      },
      accessToken: 'mock-token'
    };
  },
  register: async (data: any) => {
    await new Promise(resolve => setTimeout(resolve, 500));
    return {
      user: {
        id: '1',
        email: data.email,
        fullName: data.fullName,
        role: 'USER' as const,
        subscription: { plan: null, expiresAt: null, isActive: false },
        demoBalance: 1000,
        createdAt: new Date().toISOString(),
      },
      accessToken: 'mock-token'
    };
  },
  logout: async () => {
    await new Promise(resolve => setTimeout(resolve, 300));
  },
  getCurrentUser: async () => {
    await new Promise(resolve => setTimeout(resolve, 300));
    return {
      id: '1',
      email: 'test@example.com',
      fullName: 'Test User',
      role: 'USER' as const,
      subscription: { plan: null, expiresAt: null, isActive: false },
      demoBalance: 1000,
      createdAt: new Date().toISOString(),
    };
  }
};

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      isAuthenticated: false,
      isLoading: true,
      error: null,

      login: async (email, password) => {
        try {
          set({ isLoading: true, error: null });
          const response = await mockAuthApi.login({ email, password });
          const { user, accessToken } = response;
          localStorage.setItem('access_token', accessToken);
          set({ user, isAuthenticated: true, isLoading: false });
        } catch (error: any) {
          set({ 
            error: error.message || 'Login failed', 
            isLoading: false 
          });
        }
      },

      register: async (data) => {
        try {
          set({ isLoading: true, error: null });
          const response = await mockAuthApi.register(data);
          const { user, accessToken } = response;
          localStorage.setItem('access_token', accessToken);
          set({ user, isAuthenticated: true, isLoading: false });
        } catch (error: any) {
          set({ 
            error: error.message || 'Registration failed', 
            isLoading: false 
          });
        }
      },

      logout: async () => {
        try {
          await mockAuthApi.logout();
        } finally {
          localStorage.removeItem('access_token');
          set({ user: null, isAuthenticated: false });
        }
      },

      checkAuth: async () => {
        try {
          set({ isLoading: true });
          const user = await mockAuthApi.getCurrentUser();
          set({ user, isAuthenticated: true, isLoading: false });
        } catch {
          set({ user: null, isAuthenticated: false, isLoading: false });
        }
      },

      clearError: () => set({ error: null }),
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({ 
        user: state.user, 
        isAuthenticated: state.isAuthenticated 
      }),
    }
  )
);