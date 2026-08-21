import { apiClient } from './client';

export interface Plan {
  id: string;
  name: string;
  tier: 'BASIC' | 'PRO' | 'ENTERPRISE';
  price: number;
  currency: 'USDT';
  duration: number;
  features: string[];
  isPopular?: boolean;
}

export interface Subscription {
  id: string;
  plan: Plan;
  startAt: string;
  expiresAt: string;
  status: 'ACTIVE' | 'EXPIRED' | 'CANCELLED' | 'PENDING';
  isTrial: boolean;
}

export interface PaymentRequest {
  planId: string;
  duration: number;
  paymentMethod: 'USDT';
}

export interface PaymentResponse {
  paymentId: string;
  address: string;
  amount: number;
  expiresAt: string;
}

export interface PaymentVerification {
  status: 'PENDING' | 'COMPLETED' | 'FAILED';
  subscription?: Subscription;
}

export const subscriptionApi = {
  getPlans: () =>
    apiClient.get<Plan[]>('/subscription/plans'),
  
  getCurrentSubscription: () =>
    apiClient.get<Subscription>('/subscription/current'),
  
  createPayment: (data: PaymentRequest) =>
    apiClient.post<PaymentResponse>('/subscription/payment', data),
  
  verifyPayment: (paymentId: string) =>
    apiClient.get<PaymentVerification>(`/subscription/payment/${paymentId}/verify`),
  
  cancelSubscription: () =>
    apiClient.post('/subscription/cancel'),
};