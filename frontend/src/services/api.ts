import axios from 'axios';
import type {
  Backtest, BacktestCreateRequest, BacktestDetail, Instrument,
  IndicatorPoint, OHLCVBar, StrategyDef,
} from '../types';

export const api = axios.create({ baseURL: '/api' });

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('quantx_token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// ---------- Auth ----------
export async function login(email: string, password: string) {
  const form = new URLSearchParams();
  form.set('username', email);
  form.set('password', password);
  const { data } = await api.post('/auth/login', form, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  });
  return data as { access_token: string; token_type: string };
}

export async function register(email: string, password: string, full_name?: string) {
  const { data } = await api.post('/auth/register', { email, password, full_name });
  return data;
}

// ---------- Market Data ----------
export async function getInstruments(): Promise<Instrument[]> {
  const { data } = await api.get('/instruments');
  return data;
}

export async function getMarketData(symbol: string, start: string, end: string) {
  const { data } = await api.get(`/market-data/${symbol}`, {
    params: { start_date: start, end_date: end },
  });
  return data as { symbol: string; bars: OHLCVBar[]; count: number };
}

export async function importMarketData(symbol: string, start: string, end: string, provider = 'mock') {
  const { data } = await api.post('/market-data/import', {
    symbol, start_date: start, end_date: end, provider,
  });
  return data;
}

// ---------- Indicators ----------
export async function getIndicator(
  indicator: string, symbol: string, start: string, end: string, period = 14
) {
  const { data } = await api.get(`/indicators/${indicator}`, {
    params: { symbol, start_date: start, end_date: end, period },
  });
  return data as { symbol: string; indicator: string; period: number; points: IndicatorPoint[] };
}

// ---------- Strategies ----------
export async function getStrategies(): Promise<StrategyDef[]> {
  const { data } = await api.get('/strategies');
  return data;
}

// ---------- Backtests ----------
export async function createBacktest(payload: BacktestCreateRequest): Promise<Backtest> {
  const { data } = await api.post('/backtests', payload);
  return data;
}

export async function listBacktests(): Promise<Backtest[]> {
  const { data } = await api.get('/backtests');
  return data;
}

export async function getBacktest(id: string): Promise<BacktestDetail> {
  const { data } = await api.get(`/backtests/${id}`);
  return data;
}
