import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { listBacktests } from '../services/api';
import type { Backtest } from '../types';
import MetricCard from '../components/MetricCard';

export default function DashboardPage() {
  const [backtests, setBacktests] = useState<Backtest[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listBacktests()
      .then(setBacktests)
      .catch(() => setError('Could not load backtests. Is the backend running?'))
      .finally(() => setLoading(false));
  }, []);

  const completed = backtests.filter((b) => b.status === 'completed' && b.metrics);
  const avgSharpe = completed.length
    ? completed.reduce((sum, b) => sum + (b.metrics?.sharpe_ratio ?? 0), 0) / completed.length
    : null;
  const bestReturn = completed.length
    ? Math.max(...completed.map((b) => b.metrics?.total_return_pct ?? -Infinity))
    : null;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold">Dashboard</h1>
        <p className="text-terminal-muted text-sm">
          Overview of your research activity. Historical simulations only — not investment advice.
        </p>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <MetricCard label="Total Backtests" value={String(backtests.length)} />
        <MetricCard label="Completed" value={String(completed.length)} />
        <MetricCard
          label="Avg. Sharpe Ratio"
          value={avgSharpe !== null ? avgSharpe.toFixed(2) : '—'}
          positive={avgSharpe !== null && avgSharpe > 0}
          negative={avgSharpe !== null && avgSharpe < 0}
        />
        <MetricCard
          label="Best Total Return"
          value={bestReturn !== null && bestReturn !== -Infinity ? `${bestReturn.toFixed(1)}%` : '—'}
          positive={!!bestReturn && bestReturn > 0}
        />
      </div>

      <div className="card">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-sm font-semibold text-terminal-muted uppercase tracking-wide">
            Recent Backtests
          </h2>
          <Link to="/strategy-lab" className="text-xs text-terminal-accent">
            + New Backtest
          </Link>
        </div>

        {loading && <p className="text-terminal-muted text-sm">Loading…</p>}
        {error && <p className="text-terminal-danger text-sm">{error}</p>}
        {!loading && !error && backtests.length === 0 && (
          <p className="text-terminal-muted text-sm">
            No backtests yet. Head to Strategy Lab to run your first simulation.
          </p>
        )}

        <div className="divide-y divide-terminal-border">
          {backtests.slice(0, 8).map((bt) => (
            <Link
              key={bt.id}
              to={`/backtests/${bt.id}`}
              className="flex items-center justify-between py-2 text-sm hover:bg-white/5 px-2 -mx-2 rounded"
            >
              <div>
                <div className="font-medium">{bt.symbol} · {bt.strategy_key}</div>
                <div className="text-terminal-muted text-xs">
                  {new Date(bt.start_date).toLocaleDateString()} – {new Date(bt.end_date).toLocaleDateString()}
                </div>
              </div>
              <div className="text-right">
                <div className={bt.metrics && bt.metrics.total_return_pct >= 0 ? 'metric-value-positive' : 'metric-value-negative'}>
                  {bt.metrics ? `${bt.metrics.total_return_pct.toFixed(1)}%` : bt.status}
                </div>
                <div className="text-terminal-muted text-xs">Sharpe {bt.metrics?.sharpe_ratio.toFixed(2) ?? '—'}</div>
              </div>
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
}
