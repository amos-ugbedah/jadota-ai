import { apiClient } from './client';

// ============ Types ============
export interface LoginData {
  email: string;
  password: string;
}

export interface RegisterData {
  email: string;
  password: string;
  fullName: string;
  username?: string;
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
  refreshToken?: string;
}

export interface ForgotPasswordData {
  email: string;
}

export interface ResetPasswordData {
  token: string;
  password: string;
}

export interface VerifyEmailData {
  token: string;
}

export interface RefreshTokenData {
  refreshToken: string;
}

// ============ API Functions ============
export const authApi = {
  // 🔐 Authentication
  login: (data: LoginData) => 
    apiClient.post<AuthResponse>('/auth/login', data),
  
  register: (data: RegisterData) =>
    apiClient.post<AuthResponse>('/auth/register', data),
  
  logout: () =>
    apiClient.post('/auth/logout'),
  
  getCurrentUser: () =>
    apiClient.get<User>('/auth/me'),
  
  // 📧 Email Verification
  verifyEmail: (token: string) =>
    apiClient.get(`/auth/verify-email?token=${token}`),
  
  resendVerification: (email: string) =>
    apiClient.post('/auth/resend-verification', { email }),
  
  // 🔑 Password Reset
  forgotPassword: (email: string) =>
    apiClient.post('/auth/forgot-password', { email }),
  
  resetPassword: (token: string, password: string) =>
    apiClient.post('/auth/reset-password', { token, password }),
  
  // 🔄 Refresh Token
  refreshToken: (refreshToken: string) =>
    apiClient.post<AuthResponse>('/auth/refresh', { refresh_token: refreshToken }),
};

// ============ EXPLICIT TYPE EXPORTS ============
export type { 
  User, 
  LoginData, 
  RegisterData, 
  AuthResponse,
  ForgotPasswordData,
  ResetPasswordData,
  VerifyEmailData,
  RefreshTokenData
};