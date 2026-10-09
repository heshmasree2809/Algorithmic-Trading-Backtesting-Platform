import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { getBacktest, getMarketData } from '../services/api';
import type { BacktestDetail, OHLCVBar } from '../types';
import MetricCard from '../components/MetricCard';
import { EquityCurveChart, DrawdownChart } from '../components/EquityCharts';
import PriceChart from '../components/PriceChart';

export default function BacktestResultsPage() {
  const { id } = useParams<{ id: string }>();
  const [backtest, setBacktest] = useState<BacktestDetail | null>(null);
  const [bars, setBars] = useState<OHLCVBar[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    getBacktest(id)
      .then(async (bt) => {
        setBacktest(bt);
        try {
          const md = await getMarketData(bt.symbol, bt.start_date, bt.end_date);
          setBars(md.bars);
        } catch { /* price chart is best-effort */ }
      })
      .catch(() => setError('Could not load this backtest.'));
  }, [id]);

  if (error) return <p className="text-terminal-danger text-sm">{error}</p>;
  if (!backtest) return <p className="text-terminal-muted text-sm">Loading…</p>;

  if (backtest.status === 'failed') {
    return (
      <div className="card">
        <h1 className="text-lg font-semibold text-terminal-danger mb-2">Backtest Failed</h1>
        <p className="text-sm text-terminal-muted">{(backtest as any).error_message ?? 'Unknown error.'}</p>
      </div>
    );
  }

  const m = backtest.metrics;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold">
          {backtest.symbol} · {backtest.strategy_key}
        </h1>
        <p className="text-terminal-muted text-sm">
          {new Date(backtest.start_date).toLocaleDateString()} – {new Date(backtest.end_date).toLocaleDateString()}
          {' · '}Initial capital ${backtest.initial_capital.toLocaleString()}
        </p>
      </div>

      {m && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <MetricCard label="Total Return" value={`${m.total_return_pct.toFixed(1)}%`} positive={m.total_return_pct >= 0} negative={m.total_return_pct < 0} />
          <MetricCard label="CAGR" value={`${m.cagr_pct.toFixed(1)}%`} positive={m.cagr_pct >= 0} negative={m.cagr_pct < 0} />
          <MetricCard label="Sharpe Ratio" value={m.sharpe_ratio.toFixed(2)} positive={m.sharpe_ratio > 0} negative={m.sharpe_ratio < 0} />
          <MetricCard label="Max Drawdown" value={`${m.max_drawdown_pct.toFixed(1)}%`} negative />
          <MetricCard label="Sortino Ratio" value={m.sortino_ratio.toFixed(2)} />
          <MetricCard label="Volatility (Ann.)" value={`${m.annualized_volatility_pct.toFixed(1)}%`} />
          <MetricCard label="Win Rate" value={`${m.win_rate_pct.toFixed(1)}%`} />
          <MetricCard label="# Trades" value={String(m.number_of_trades)} />
        </div>
      )}

      <EquityCurveChart data={backtest.equity_curve} />
      <DrawdownChart data={backtest.equity_curve} />
      {bars.length > 0 && <PriceChart bars={bars} trades={backtest.trades} />}

      <div className="card">
        <h2 className="text-sm font-semibold text-terminal-muted uppercase tracking-wide mb-3">Trades</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead className="text-terminal-muted text-left">
              <tr>
                <th className="py-1 pr-4">Date</th>
                <th className="py-1 pr-4">Side</th>
                <th className="py-1 pr-4">Qty</th>
                <th className="py-1 pr-4">Price</th>
                <th className="py-1 pr-4">Fees</th>
                <th className="py-1 pr-4">Realized P&amp;L</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-terminal-border">
              {backtest.trades.map((t, i) => (
                <tr key={i}>
                  <td className="py-1 pr-4">{new Date(t.timestamp).toLocaleDateString()}</td>
                  <td className={`py-1 pr-4 ${t.side === 'BUY' ? 'metric-value-positive' : 'metric-value-negative'}`}>{t.side}</td>
                  <td className="py-1 pr-4">{t.quantity.toFixed(2)}</td>
                  <td className="py-1 pr-4">${t.execution_price.toFixed(2)}</td>
                  <td className="py-1 pr-4">${t.fees.toFixed(2)}</td>
                  <td className={`py-1 pr-4 ${t.realized_pnl >= 0 ? 'metric-value-positive' : 'metric-value-negative'}`}>
                    ${t.realized_pnl.toFixed(2)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <p className="text-[10px] text-terminal-muted">
        Historical simulation only. Past performance does not guarantee future results.
      </p>
    </div>
  );
}
