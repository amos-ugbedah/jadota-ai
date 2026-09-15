import { apiClient } from './client';
import type { User } from './auth';
import type { Subscription } from './subscription';

// ============ Types ============
export interface SystemStatus {
  status: 'online' | 'offline' | 'degraded';
  uptime: number;
  aiStatus: 'active' | 'paused' | 'error';
  tradesToday: number;
  winRate: number;
  pl: number;
  drawdown: number;
}

export interface RevenueStats {
  total: number;
  monthly: number;
  pending: number;
}

export interface SystemHealth {
  api: 'healthy' | 'degraded' | 'down';
  database: 'healthy' | 'degraded' | 'down';
  redis: 'healthy' | 'degraded' | 'down';
  websocket: 'healthy' | 'degraded' | 'down';
  timestamp: string;
}

export interface AIStatus {
  status: string;
  models: string[];
  lastRun: string;
  tradesToday: number;
}

export interface AuditLog {
  id: string;
  userId: string;
  action: string;
  details: any;
  timestamp: string;
  ip: string;
}

export interface SubscriptionStats {
  active: number;
  pending: number;
  expired: number;
  cancelled: number;
  total: number;
}

// ============ API Functions ============
export const adminApi = {
  // 👥 Users
  getUsers: (params?: { limit?: number; offset?: number; search?: string }) =>
    apiClient.get<User[]>('/admin/users', { params }),
  
  getUser: (id: string) =>
    apiClient.get<User>(`/admin/users/${id}`),
  
  suspendUser: (id: string, reason?: string) =>
    apiClient.post(`/admin/users/${id}/suspend`, { reason }),
  
  restoreUser: (id: string) =>
    apiClient.post(`/admin/users/${id}/restore`),
  
  deleteUser: (id: string) =>
    apiClient.delete(`/admin/users/${id}`),
  
  // 📊 Subscriptions
  getSubscriptions: (params?: { status?: string; limit?: number }) =>
    apiClient.get<Subscription[]>('/admin/subscriptions', { params }),
  
  getSubscriptionStats: () =>
    apiClient.get<SubscriptionStats>('/admin/subscriptions/stats'),
  
  // 📈 Revenue
  getRevenue: (period?: 'day' | 'week' | 'month' | 'year') =>
    apiClient.get<RevenueStats>('/admin/revenue', { params: { period } }),
  
  // 🖥️ System
  getSystemStatus: () =>
    apiClient.get<SystemStatus>('/admin/system/status'),
  
  getSystemHealth: () =>
    apiClient.get<SystemHealth>('/admin/system/health'),
  
  getSystemLogs: (limit?: number, level?: string) =>
    apiClient.get<string[]>('/admin/system/logs', { params: { limit, level } }),
  
  // 🤖 AI Control
  pauseAI: () =>
    apiClient.post('/admin/ai/pause'),
  
  resumeAI: () =>
    apiClient.post('/admin/ai/resume'),
  
  getAIStatus: () =>
    apiClient.get<AIStatus>('/admin/ai/status'),
  
  // 🛡️ Security
  getAuditLogs: (params?: { userId?: string; limit?: number }) =>
    apiClient.get<AuditLog[]>('/admin/audit', { params }),
};

// ============ EXPLICIT EXPORTS (FIXED - ALL TYPES INCLUDED) ============
export type { 
  SystemStatus, 
  RevenueStats, 
  SystemHealth, 
  AIStatus, 
  AuditLog,
  SubscriptionStats,
  User,
  Subscription
};