// ============================================
// JADOTA AI - Centralized Configuration
// ============================================

interface AppConfig {
  api: {
    url: string;
    wsUrl: string;
    timeout: number;
  };
  app: {
    name: string;
    version: string;
    env: 'development' | 'production' | 'staging';
  };
  features: {
    enableDemoMode: boolean;
    enableLiveTrading: boolean;
  };
  monitoring: {
    sentryDsn?: string;
    gaId?: string;
  };
}

const config: AppConfig = {
  api: {
    url: import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1',
    wsUrl: import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws',
    timeout: 30000,
  },
  app: {
    name: import.meta.env.VITE_APP_NAME || 'JADOTA AI',
    version: import.meta.env.VITE_APP_VERSION || '1.0.0',
    env: (import.meta.env.VITE_APP_ENV as any) || 'development',
  },
  features: {
    enableDemoMode: import.meta.env.VITE_ENABLE_DEMO_MODE === 'true',
    enableLiveTrading: import.meta.env.VITE_ENABLE_LIVE_TRADING === 'true',
  },
  monitoring: {
    sentryDsn: import.meta.env.VITE_SENTRY_DSN,
    gaId: import.meta.env.VITE_GA_ID,
  },
};

export default config;

// Helper: Get current environment
export const isDev = config.app.env === 'development';
export const isProd = config.app.env === 'production';
export const isStaging = config.app.env === 'staging';

// Helper: Get API URL
export const getApiUrl = () => config.api.url;

// Helper: Get WebSocket URL
export const getWsUrl = () => config.api.wsUrl;

// Helper: Check if feature is enabled
export const isFeatureEnabled = (feature: keyof typeof config.features) => {
  return config.features[feature] === true;
};

// Helper: Get app version
export const getAppVersion = () => config.app.version;

// Helper: Get app name
export const getAppName = () => config.app.name;