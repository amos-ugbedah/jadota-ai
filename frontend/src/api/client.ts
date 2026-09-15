import axios from 'axios';
import toast from 'react-hot-toast';
import config, { getApiUrl, getWsUrl, isDev } from '@/utils/config';

// ============================================
// JADOTA AI - API Client
// ============================================

const API_URL = getApiUrl();

export const apiClient = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
    'X-Client-Version': config.app.version,
    'X-Client-Env': config.app.env,
  },
  timeout: config.api.timeout,
});

// ============================================
// Request Interceptor
// ============================================
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    
    config.headers['X-Request-ID'] = `${Date.now()}-${Math.random().toString(36).substring(2, 9)}`;
    
    return config;
  },
  (error) => {
    console.error('Request error:', error);
    return Promise.reject(error);
  }
);

// ============================================
// 🔥 Silent Token Refresh Helper
// ============================================
let isRefreshing = false;
let refreshSubscribers: Array<(token: string) => void> = [];

function subscribeTokenRefresh(cb: (token: string) => void) {
  refreshSubscribers.push(cb);
}

function onTokenRefreshed(token: string) {
  refreshSubscribers.forEach((cb) => cb(token));
  refreshSubscribers = [];
}

async function performTokenRefresh(): Promise<string | null> {
  const refreshToken = localStorage.getItem('refresh_token');
  if (!refreshToken) return null;

  try {
    // Use raw axios to avoid interceptor recursion
    const { data } = await axios.post(
      `${API_URL}/api/v1/auth/refresh`,
      { refresh_token: refreshToken },
      { headers: { 'Content-Type': 'application/json' } }
    );

    const newAccess = data.accessToken;
    const newRefresh = data.refreshToken;

    if (newAccess) localStorage.setItem('access_token', newAccess);
    if (newRefresh) localStorage.setItem('refresh_token', newRefresh);

    return newAccess || null;
  } catch (err) {
    console.warn('Token refresh failed:', err);
    return null;
  }
}

// ============================================
// Response Interceptor - Production Ready
// ============================================
apiClient.interceptors.response.use(
  (response) => {
    if (isDev) {
      console.log(`✅ ${response.config.method?.toUpperCase()} ${response.config.url}`, response.data);
    }
    return response.data;
  },
  async (error) => {
    const originalRequest = error.config || {};
    const status = error.response?.status;

    // ============================================
    // 🔥 401 handling: try silent refresh, then log out only on failure
    // ============================================
    if (status === 401 && !originalRequest._retry) {
      const isAuthPage =
        window.location.pathname.includes('/login') ||
        window.location.pathname.includes('/register');
      const isAuthCall =
        originalRequest.url?.includes('/auth/login') ||
        originalRequest.url?.includes('/auth/register') ||
        originalRequest.url?.includes('/auth/refresh');

      // Never try to refresh on login/register/refresh calls
      if (isAuthCall || isAuthPage) {
        return Promise.reject(error);
      }

      originalRequest._retry = true;

      // If a refresh is already in-flight, queue this request
      if (isRefreshing) {
        return new Promise((resolve) => {
          subscribeTokenRefresh((newToken: string) => {
            originalRequest.headers = originalRequest.headers || {};
            originalRequest.headers.Authorization = `Bearer ${newToken}`;
            resolve(apiClient(originalRequest));
          });
        });
      }

      isRefreshing = true;

      const newToken = await performTokenRefresh();
      isRefreshing = false;

      if (newToken) {
        onTokenRefreshed(newToken);
        originalRequest.headers = originalRequest.headers || {};
        originalRequest.headers.Authorization = `Bearer ${newToken}`;
        return apiClient(originalRequest);
      }

      // Refresh failed — only NOW do we log out
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      localStorage.removeItem('auth-storage');

      if (!isAuthPage) {
        toast.error('Session expired. Please login again.');
        // Give toast a moment to be seen
        setTimeout(() => {
          window.location.href = '/login';
        }, 300);
      }
      return Promise.reject(error);
    }

    // Handle 403 Forbidden
    if (status === 403) {
      toast.error('You do not have permission to perform this action.');
      return Promise.reject(error);
    }

    // Handle 404 Not Found
    if (status === 404) {
      toast.error('Resource not found.');
      return Promise.reject(error);
    }

    // Handle 429 Rate Limit
    if (status === 429) {
      toast.error('Too many requests. Please slow down.');
      return Promise.reject(error);
    }

    // Handle 500+ Server Errors
    if (status && status >= 500) {
      toast.error('Server error. Please try again later.');
      return Promise.reject(error);
    }

    // Handle Network Errors
    if (error.code === 'ERR_NETWORK' || error.message === 'Network Error') {
      toast.error('Network error. Please check your connection.');
      return Promise.reject(error);
    }

    // Handle Timeout
    if (error.code === 'ECONNABORTED' || error.message?.includes('timeout')) {
      toast.error('Request timed out. Please try again.');
      return Promise.reject(error);
    }

    // Generic error - don't show toast for cancel requests
    const message =
      error.response?.data?.detail ||
      error.response?.data?.message ||
      error.message ||
      'An error occurred';

    if (!axios.isCancel(error)) {
      toast.error(message);
    }

    return Promise.reject(error);
  }
);

// ============================================
// WebSocket Client
// ============================================
export class WebSocketClient {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private listeners: Map<string, Set<(data: any) => void>> = new Map();
  private isConnecting = false;
  private isConnected = false;
  private wsUrl: string;
  private pingInterval: NodeJS.Timeout | null = null;
  private lastPingResponse: number = Date.now();

  constructor(wsUrl: string = getWsUrl()) {
    this.wsUrl = wsUrl;
  }

  connect(token: string) {
    if (this.isConnecting || this.isConnected) {
      return;
    }
    
    this.isConnecting = true;
    
    try {
      this.ws = new WebSocket(`${this.wsUrl}?token=${token}`);
    } catch (error) {
      console.error('Failed to create WebSocket:', error);
      this.isConnecting = false;
      this.reconnect();
      return;
    }

    this.ws.onopen = () => {
      console.log('✅ WebSocket connected');
      this.reconnectAttempts = 0;
      this.isConnecting = false;
      this.isConnected = true;
      this.lastPingResponse = Date.now();
      this.startPingInterval();
    };

    this.ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        
        if (data.type === 'pong') {
          this.lastPingResponse = Date.now();
          return;
        }
        
        const { type, payload } = data;
        const callbacks = this.listeners.get(type);
        if (callbacks) {
          callbacks.forEach(cb => {
            try {
              cb(payload);
            } catch (error) {
              console.error('WebSocket callback error:', error);
            }
          });
        }
      } catch (error) {
        console.error('WebSocket message error:', error);
      }
    };

    this.ws.onclose = (event) => {
      console.log(`WebSocket disconnected: ${event.code}`);
      this.isConnecting = false;
      this.isConnected = false;
      this.stopPingInterval();
      this.reconnect();
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      this.isConnecting = false;
    };
  }

  private startPingInterval() {
    this.stopPingInterval();
    this.pingInterval = setInterval(() => {
      if (this.isConnected && this.ws?.readyState === WebSocket.OPEN) {
        this.send('ping', { timestamp: Date.now() });
        
        if (Date.now() - this.lastPingResponse > 30000) {
          console.warn('WebSocket ping timeout, reconnecting...');
          this.reconnect();
        }
      }
    }, 15000);
  }

  private stopPingInterval() {
    if (this.pingInterval) {
      clearInterval(this.pingInterval);
      this.pingInterval = null;
    }
  }

  private reconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('Max reconnection attempts reached');
      return;
    }

    this.reconnectAttempts++;
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
    
    setTimeout(() => {
      const token = localStorage.getItem('access_token');
      if (token) {
        this.connect(token);
      }
    }, delay);
  }

  subscribe(type: string, callback: (data: any) => void) {
    if (!this.listeners.has(type)) {
      this.listeners.set(type, new Set());
    }
    this.listeners.get(type)!.add(callback);
    
    return () => {
      this.listeners.get(type)?.delete(callback);
    };
  }

  send(type: string, data: any) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      try {
        this.ws.send(JSON.stringify({ type, data }));
      } catch (error) {
        console.error('WebSocket send error:', error);
      }
    }
  }

  disconnect() {
    this.stopPingInterval();
    if (this.ws) {
      this.ws.close(1000, 'Client disconnected');
      this.ws = null;
    }
    this.isConnected = false;
    this.isConnecting = false;
    this.listeners.clear();
  }

  getConnectionStatus() {
    return {
      isConnected: this.isConnected,
      isConnecting: this.isConnecting,
      reconnectAttempts: this.reconnectAttempts,
      readyState: this.ws?.readyState ?? -1,
    };
  }

  subscribeToPrice(symbol: string, callback: (data: { symbol: string; price: number; timestamp: string }) => void) {
    const unsubscribe = this.subscribe('price_update', callback);
    this.send('subscribe', { symbol });
    return unsubscribe;
  }

  subscribeToTrades(callback: (data: any) => void) {
    return this.subscribe('trade_executed', callback);
  }

  subscribeToPositions(callback: (data: any) => void) {
    return this.subscribe('position_updated', callback);
  }

  subscribeToNotifications(callback: (data: any) => void) {
    return this.subscribe('notification', callback);
  }
}

export const wsClient = new WebSocketClient();

export const initWebSocket = (token?: string) => {
  const authToken = token || localStorage.getItem('access_token');
  if (authToken) {
    wsClient.connect(authToken);
    return true;
  }
  return false;
};

export const disconnectWebSocket = () => {
  wsClient.disconnect();
};

export const getWebSocketStatus = () => {
  return wsClient.getConnectionStatus();
};

export default apiClient;