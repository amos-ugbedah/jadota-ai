import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { authApi } from '@/api/auth';
import type { User, RegisterData } from '@/api/auth';
import { toast } from 'react-hot-toast';

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  isSubmitting: boolean;
  error: string | null;
  login: (email: string, password: string) => Promise<void>;
  register: (data: RegisterData) => Promise<void>;
  logout: () => Promise<void>;
  checkAuth: () => Promise<void>;
  updateUser: (user: User) => void;
  clearError: () => void;
  resetPassword: (token: string, password: string) => Promise<void>;
  forgotPassword: (email: string) => Promise<void>;
  verifyEmail: (token: string) => Promise<void>;
  refreshToken: () => Promise<boolean>;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      isAuthenticated: false,
      isLoading: true,
      isSubmitting: false,
      error: null,

      login: async (email: string, password: string) => {
        try {
          set({ isLoading: true, isSubmitting: true, error: null });
          
          const response = await authApi.login({ email, password });
          console.log('🔐 Login response:', response);
          
          const { user, accessToken, refreshToken } = response;
          
          localStorage.setItem('access_token', accessToken);
          if (refreshToken) {
            localStorage.setItem('refresh_token', refreshToken);
          }
          
          set({ 
            user, 
            isAuthenticated: true, 
            isLoading: false,
            isSubmitting: false,
            error: null 
          });
          
          toast.success(`Welcome back, ${user.fullName}! 🎉`);
        } catch (error: any) {
          console.error('❌ Login error:', error);
          const message = error.response?.data?.detail || error.message || 'Login failed';
          set({ 
            error: message, 
            isLoading: false,
            isSubmitting: false,
            isAuthenticated: false,
            user: null
          });
          toast.error(message);
        }
      },

      register: async (data: RegisterData) => {
        try {
          set({ isLoading: true, isSubmitting: true, error: null });
          
          const response = await authApi.register(data);
          const { user, accessToken, refreshToken } = response;
          
          localStorage.setItem('access_token', accessToken);
          if (refreshToken) {
            localStorage.setItem('refresh_token', refreshToken);
          }
          
          set({ 
            user, 
            isAuthenticated: true, 
            isLoading: false,
            isSubmitting: false,
            error: null 
          });
          
          toast.success('Account created successfully! Please verify your email.');
        } catch (error: any) {
          const message = error.response?.data?.detail || error.message || 'Registration failed';
          set({ 
            error: message, 
            isLoading: false,
            isSubmitting: false,
            isAuthenticated: false,
            user: null
          });
          toast.error(message);
        }
      },

      logout: async () => {
        try {
          set({ isLoading: true });
          await authApi.logout();
        } catch (error) {
          // Ignore logout errors
        } finally {
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          localStorage.removeItem('auth-storage');
          set({ 
            user: null, 
            isAuthenticated: false, 
            isLoading: false,
            error: null 
          });
          toast.success('Logged out successfully');
        }
      },

      // 🔥 FIXED: checkAuth with proper error handling
      checkAuth: async () => {
        const token = localStorage.getItem('access_token');
        
        // If no token, immediately set as not authenticated
        if (!token) {
          set({ isLoading: false, isAuthenticated: false, user: null });
          return;
        }

        try {
          set({ isLoading: true });
          
          const user = await authApi.getCurrentUser();
          console.log('👤 User fetched:', user);
          
          set({ 
            user, 
            isAuthenticated: true, 
            isLoading: false,
            error: null 
          });
        } catch (error: any) {
          // If token is invalid, clear it and set as not authenticated
          console.warn('Auth check failed:', error.message);
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          set({ 
            user: null, 
            isAuthenticated: false, 
            isLoading: false,
            error: null 
          });
        }
      },

      refreshToken: async () => {
        const refreshToken = localStorage.getItem('refresh_token');
        if (!refreshToken) {
          return false;
        }

        try {
          const response = await authApi.refreshToken(refreshToken);
          const { accessToken, refreshToken: newRefreshToken } = response;
          
          localStorage.setItem('access_token', accessToken);
          if (newRefreshToken) {
            localStorage.setItem('refresh_token', newRefreshToken);
          }
          
          const user = await authApi.getCurrentUser();
          set({ user, isAuthenticated: true, error: null });
          
          return true;
        } catch (error) {
          console.error('Token refresh failed:', error);
          return false;
        }
      },

      updateUser: (user: User) => {
        set({ user });
      },

      clearError: () => set({ error: null }),

      forgotPassword: async (email: string) => {
        try {
          set({ isLoading: true, error: null });
          await authApi.forgotPassword(email);
          toast.success('Password reset email sent! Check your inbox.');
          set({ isLoading: false });
        } catch (error: any) {
          const message = error.response?.data?.detail || error.message || 'Failed to send reset email';
          set({ error: message, isLoading: false });
          toast.error(message);
        }
      },

      resetPassword: async (token: string, password: string) => {
        try {
          set({ isLoading: true, error: null });
          await authApi.resetPassword(token, password);
          toast.success('Password reset successfully! Please login.');
          set({ isLoading: false });
        } catch (error: any) {
          const message = error.response?.data?.detail || error.message || 'Failed to reset password';
          set({ error: message, isLoading: false });
          toast.error(message);
        }
      },

      verifyEmail: async (token: string) => {
        try {
          set({ isLoading: true, error: null });
          await authApi.verifyEmail(token);
          toast.success('Email verified successfully!');
          await get().checkAuth();
          set({ isLoading: false });
        } catch (error: any) {
          const message = error.response?.data?.detail || error.message || 'Failed to verify email';
          set({ error: message, isLoading: false });
          toast.error(message);
        }
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({ 
        user: state.user, 
        isAuthenticated: state.isAuthenticated 
      }),
      version: 1,
    }
  )
);

// Selector Hooks
export const useUser = () => useAuthStore((state) => state.user);
export const useIsAuthenticated = () => useAuthStore((state) => state.isAuthenticated);
export const useIsLoading = () => useAuthStore((state) => state.isLoading);
export const useAuthError = () => useAuthStore((state) => state.error);
export const useIsSubmitting = () => useAuthStore((state) => state.isSubmitting);

export const useLogin = () => useAuthStore((state) => state.login);
export const useRegister = () => useAuthStore((state) => state.register);
export const useLogout = () => useAuthStore((state) => state.logout);
export const useCheckAuth = () => useAuthStore((state) => state.checkAuth);
export const useRefreshToken = () => useAuthStore((state) => state.refreshToken);