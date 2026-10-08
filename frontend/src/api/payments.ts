import apiClient from './client';

export type PaymentStatus =
  | 'pending' | 'verifying' | 'completed'
  | 'failed' | 'expired' | 'cancelled';

export interface Payment {
  id: string;
  user_id: string;
  plan: string;
  months: number;
  amount_usdt: number;
  network: string;
  wallet_address: string;
  status: PaymentStatus;
  tx_hash?: string | null;
  created_at?: string;
  expires_at?: string;
  verified_at?: string | null;
  completed_at?: string | null;
}

export interface VerifyResponse {
  success: boolean;
  status: PaymentStatus;
  message: string;
  tx_hash?: string | null;
}

export const paymentsApi = {
  create: (plan: string, months = 1) =>
    apiClient.post<Payment>('/payments/create', { plan, months }),

  get: (id: string) =>
    apiClient.get<Payment>(`/payments/${id}`),

  verify: (id: string) =>
    apiClient.post<VerifyResponse>(`/payments/${id}/verify`),

  cancel: (id: string) =>
    apiClient.post<Payment>(`/payments/${id}/cancel`),

  history: () =>
    apiClient.get<Payment[]>('/payments/'),

  // Admin
  adminList: (statusFilter?: string) =>
    apiClient.get<Payment[]>('/payments/admin/all', {
      params: statusFilter ? { status_filter: statusFilter } : undefined,
    }),

  adminApprove: (id: string, txHash?: string, notes?: string) =>
    apiClient.post<VerifyResponse>(`/payments/admin/${id}/approve`, {
      tx_hash: txHash, admin_notes: notes,
    }),

  adminReject: (id: string, notes?: string) =>
    apiClient.post<Payment>(`/payments/admin/${id}/reject`, {
      admin_notes: notes,
    }),
};