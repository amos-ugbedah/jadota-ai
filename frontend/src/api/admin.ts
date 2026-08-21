import { apiClient } from './client';
import { User } from './auth';
import { Subscription } from './subscription';

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

export const adminApi = {
  getUsers: (params?: { limit?: number; offset?: number }) =>
    apiClient.get<User[]>('/admin/users', { params }),
  
  getUser: (id: string) =>
    apiClient.get<User>(`/admin/users/${id}`),
  
  suspendUser: (id: string) =>
    apiClient.post(`/admin/users/${id}/suspend`),
  
  restoreUser: (id: string) =>
    apiClient.post(`/admin/users/${id}/restore`),
  
  getSubscriptions: () =>
    apiClient.get<Subscription[]>('/admin/subscriptions'),
  
  getSystemStatus: () =>
    apiClient.get<SystemStatus>('/admin/system/status'),
  
  getRevenue: () =>
    apiClient.get<RevenueStats>('/admin/revenue'),
  
  pauseAI: () =>
    apiClient.post('/admin/ai/pause'),
  
  resumeAI: () =>
    apiClient.post('/admin/ai/resume'),
};