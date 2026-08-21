import { apiClient } from './client';

export interface LoginData {
  email: string;
  password: string;
}

export interface RegisterData {
  email: string;
  password: string;
  fullName: string;
}

export interface User {
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

export interface AuthResponse {
  user: User;
  accessToken: string;
}

export const authApi = {
  login: (data: LoginData) => 
    apiClient.post<AuthResponse>('/auth/login', data),
  
  register: (data: RegisterData) =>
    apiClient.post<AuthResponse>('/auth/register', data),
  
  logout: () =>
    apiClient.post('/auth/logout'),
  
  getCurrentUser: () =>
    apiClient.get<User>('/auth/me'),
  
  verifyEmail: (token: string) =>
    apiClient.get(`/auth/verify-email?token=${token}`),
  
  forgotPassword: (email: string) =>
    apiClient.post('/auth/forgot-password', { email }),
  
  resetPassword: (token: string, password: string) =>
    apiClient.post('/auth/reset-password', { token, password }),
};

// ✅ Export all types
export type { User, LoginData, RegisterData, AuthResponse };