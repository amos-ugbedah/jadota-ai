import { apiClient } from './client';

// ============ Types ============
export interface Plan {
  id: string;
  name: string;
  tier: 'BASIC' | 'PRO' | 'ENTERPRISE';
  price: number;
  currency: 'USDT';
  duration: number; // in months
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
  userId?: string;
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
  transactionHash?: string;
}

export interface PaymentVerification {
  status: 'PENDING' | 'COMPLETED' | 'FAILED' | 'CONFIRMING';
  subscription?: Subscription;
  confirmations?: number;
  requiredConfirmations?: number;
}

export interface SubscriptionAccess {
  hasAccess: boolean;
  isActive: boolean;
  plan: string | null;
  expiresAt: string | null;
  daysRemaining: number | null;
  features: string[];
}

// ============ API Functions ============
export const subscriptionApi = {
  // 📋 Plans
  getPlans: () =>
    apiClient.get<Plan[]>('/subscription/plans'),
  
  // 🔍 Current Subscription
  getCurrentSubscription: () =>
    apiClient.get<Subscription>('/subscription/current'),
  
  getSubscriptionHistory: () =>
    apiClient.get<Subscription[]>('/subscription/history'),
  
  getAccess: () =>
    apiClient.get<SubscriptionAccess>('/subscription/access'),
  
  // 💳 Payments
  createPayment: (data: PaymentRequest) =>
    apiClient.post<PaymentResponse>('/subscription/payment', data),
  
  verifyPayment: (paymentId: string) =>
    apiClient.get<PaymentVerification>(`/subscription/payment/${paymentId}/verify`),
  
  verifyTransaction: (transactionHash: string, amount: number, network: string) =>
    apiClient.post<PaymentVerification>('/subscription/verify-payment', {
      transaction_hash: transactionHash,
      amount_usdt: amount,
      network
    }),
  
  getPaymentHistory: () =>
    apiClient.get<PaymentResponse[]>('/subscription/payments'),
  
  // 🔄 Cancel
  cancelSubscription: () =>
    apiClient.post('/subscription/cancel'),
};

// ============ EXPLICIT TYPE EXPORTS (FIXED) ============
export type { 
  Plan, 
  Subscription, 
  PaymentRequest,
  PaymentResponse, 
  PaymentVerification, 
  SubscriptionAccess 
};