export interface OHLCVBar {
  timestamp: string;
  open: number;
  high: number;
  low: number;
  close: number;
  adjusted_close?: number;
  volume?: number;
}

export interface Instrument {
  symbol: string;
  name?: string;
  asset_class: string;
  currency: string;
  exchange?: string;
}

export interface IndicatorPoint {
  timestamp: string;
  value: number | null;
  extra: Record<string, number | null>;
}

export interface StrategyDef {
  key: string;
  name: string;
  description: string;
  default_params: Record<string, number | string>;
}

export interface PerformanceMetrics {
  total_return_pct: number;
  cagr_pct: number;
  annualized_volatility_pct: number;
  sharpe_ratio: number;
  sortino_ratio: number;
  max_drawdown_pct: number;
  calmar_ratio: number;
  win_rate_pct: number;
  profit_factor: number;
  average_win: number;
  average_loss: number;
  number_of_trades: number;
  average_holding_period_days: number;
}

export interface Trade {
  timestamp: string;
  symbol: string;
  side: 'BUY' | 'SELL';
  quantity: number;
  execution_price: number;
  fees: number;
  slippage_cost: number;
  realized_pnl: number;
}

export interface EquityPoint {
  timestamp: string;
  cash: number;
  holdings_value: number;
  total_value: number;
  position_qty: number;
}

export interface Backtest {
  id: string;
  symbol: string;
  strategy_key: string;
  start_date: string;
  end_date: string;
  initial_capital: number;
  status: 'pending' | 'running' | 'completed' | 'failed';
  metrics?: PerformanceMetrics;
  created_at: string;
}

export interface BacktestDetail extends Backtest {
  trades: Trade[];
  equity_curve: EquityPoint[];
}

export interface BacktestCreateRequest {
  symbol: string;
  strategy_key: string;
  start_date: string;
  end_date: string;
  initial_capital: number;
  transaction_cost_pct: number;
  slippage_pct: number;
  position_sizing: 'full' | 'fixed_fraction';
  fixed_fraction: number;
  params: Record<string, number>;
}
