/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_URL: string;
  readonly VITE_WS_URL: string;
  readonly VITE_APP_NAME: string;
  readonly VITE_APP_VERSION: string;
  readonly VITE_APP_ENV: 'development' | 'production' | 'staging';
  readonly VITE_ENABLE_DEMO_MODE: string;
  readonly VITE_ENABLE_LIVE_TRADING: string;
  readonly VITE_SENTRY_DSN?: string;
  readonly VITE_GA_ID?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}