import { apiClient } from './client';

export interface Notification {
  id: string;
  userId: string;
  type: 'trade' | 'price' | 'subscription' | 'system';
  title: string;
  message: string;
  read: boolean;
  createdAt: string;
  data?: any;
}

export interface NotificationPreferences {
  email: boolean;
  push: boolean;
  tradeAlerts: boolean;
  priceAlerts: boolean;
}

export const notificationApi = {
  getNotifications: (limit?: number) =>
    apiClient.get<Notification[]>('/notifications', { params: { limit } }),
  
  getUnreadCount: () =>
    apiClient.get<{ count: number }>('/notifications/unread-count'),
  
  markAsRead: (notificationIds: string[]) =>
    apiClient.post('/notifications/mark-read', { notificationIds }),
  
  markAllRead: () =>
    apiClient.post('/notifications/mark-all-read'),
  
  getPreferences: () =>
    apiClient.get<NotificationPreferences>('/notifications/preferences'),
  
  updatePreferences: (preferences: Partial<NotificationPreferences>) =>
    apiClient.put('/notifications/preferences', preferences),
};