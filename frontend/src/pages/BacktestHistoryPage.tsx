import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { listBacktests } from '../services/api';
import type { Backtest } from '../types';

export default function BacktestHistoryPage() {
  const [backtests, setBacktests] = useState<Backtest[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    listBacktests().then(setBacktests).finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-xl font-semibold">Backtest History</h1>
        <p className="text-terminal-muted text-sm">All previous experiments.</p>
      </div>

      <div className="card overflow-x-auto">
        {loading ? (
          <p className="text-terminal-muted text-sm">Loading…</p>
        ) : backtests.length === 0 ? (
          <p className="text-terminal-muted text-sm">No backtests yet.</p>
        ) : (
          <table className="w-full text-sm">
            <thead className="text-terminal-muted text-left text-xs uppercase">
              <tr>
                <th className="py-2 pr-4">Strategy</th>
                <th className="py-2 pr-4">Symbol</th>
                <th className="py-2 pr-4">Date Range</th>
                <th className="py-2 pr-4">Return</th>
                <th className="py-2 pr-4">Sharpe</th>
                <th className="py-2 pr-4">Max DD</th>
                <th className="py-2 pr-4">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-terminal-border">
              {backtests.map((bt) => (
                <tr key={bt.id} className="hover:bg-white/5">
                  <td className="py-2 pr-4">
                    <Link to={`/backtests/${bt.id}`} className="text-terminal-accent">{bt.strategy_key}</Link>
                  </td>
                  <td className="py-2 pr-4">{bt.symbol}</td>
                  <td className="py-2 pr-4 text-terminal-muted text-xs">
                    {new Date(bt.start_date).toLocaleDateString()} – {new Date(bt.end_date).toLocaleDateString()}
                  </td>
                  <td className={`py-2 pr-4 ${bt.metrics && bt.metrics.total_return_pct >= 0 ? 'metric-value-positive' : 'metric-value-negative'}`}>
                    {bt.metrics ? `${bt.metrics.total_return_pct.toFixed(1)}%` : '—'}
                  </td>
                  <td className="py-2 pr-4">{bt.metrics?.sharpe_ratio.toFixed(2) ?? '—'}</td>
                  <td className="py-2 pr-4 metric-value-negative">
                    {bt.metrics ? `${bt.metrics.max_drawdown_pct.toFixed(1)}%` : '—'}
                  </td>
                  <td className="py-2 pr-4 text-xs">{bt.status}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
