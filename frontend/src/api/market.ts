import { apiClient } from './client';

export interface MarketPrice {
  symbol: string;
  price: number;
  change24h: number;
  volume24h: number;
  high24h: number;
  low24h: number;
  timestamp: string;
}

export interface OHLCV {
  timestamp: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface SymbolInfo {
  symbol: string;
  baseAsset: string;
  quoteAsset: string;
  minSize: number;
  maxSize: number;
  stepSize: number;
  tickSize: number;
}

export interface PriceUpdate {
  symbol: string;
  price: number;
  change24h: number;
  volume: number;
}

export const marketApi = {
  // 📊 Prices
  getPrices: () =>
    apiClient.get<MarketPrice[]>('/market/prices'),
  
  getPrice: (symbol: string) =>
    apiClient.get<MarketPrice>(`/market/price/${symbol}`),
  
  // 📈 OHLCV Data
  getOHLCV: (symbol: string, interval: '1m' | '5m' | '15m' | '1h' | '4h' | '1d' | '1w', limit?: number) =>
    apiClient.get<OHLCV[]>(`/market/ohlcv/${symbol}`, { 
      params: { interval, limit } 
    }),
  
  refreshOHLCV: (symbol: string, interval: string, limit?: number) =>
    apiClient.post(`/market/ohlcv/refresh`, null, { 
      params: { symbol, interval, limit } 
    }),
  
  // 📋 Symbols
  getSymbols: () =>
    apiClient.get<string[]>('/market/symbols'),
  
  getSymbolInfo: (symbol: string) =>
    apiClient.get<SymbolInfo>(`/market/symbols/${symbol}`),
  
  // 🔄 Real-time Updates
  getLatestUpdates: () =>
    apiClient.get<PriceUpdate[]>('/market/updates'),
  
  refreshPrices: () =>
    apiClient.post('/market/prices/refresh'),
  
  // 📊 Market Status
  getMarketStatus: () =>
    apiClient.get<{
      isOpen: boolean;
      nextClose?: string;
      nextOpen?: string;
    }>('/market/status'),
};

export type { OHLCV, MarketPrice, SymbolInfo, PriceUpdate };