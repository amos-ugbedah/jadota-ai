import { apiClient } from './client';

export interface OHLCV {
  timestamp: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface MarketPrice {
  symbol: string;
  price: number;
  change24h: number;
  volume24h: number;
  high24h: number;
  low24h: number;
}

export const marketApi = {
  getPrices: () =>
    apiClient.get<MarketPrice[]>('/market/prices'),
  
  getOHLCV: (symbol: string, interval: string, limit?: number) =>
    apiClient.get<OHLCV[]>(`/market/ohlcv/${symbol}`, { 
      params: { interval, limit } 
    }),
  
  getSymbols: () =>
    apiClient.get<string[]>('/market/symbols'),
};