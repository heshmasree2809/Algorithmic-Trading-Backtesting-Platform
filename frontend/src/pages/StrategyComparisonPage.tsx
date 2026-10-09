import { useEffect, useState } from 'react';
import { listBacktests } from '../services/api';
import type { Backtest } from '../types';

export default function StrategyComparisonPage() {
  const [backtests, setBacktests] = useState<Backtest[]>([]);
  const [selected, setSelected] = useState<string[]>([]);

  useEffect(() => {
    listBacktests().then((all) => setBacktests(all.filter((b) => b.status === 'completed' && b.metrics)));
  }, []);

  function toggle(id: string) {
    setSelected((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]));
  }

  const compared = backtests.filter((b) => selected.includes(b.id));

  const metricRows: { key: keyof NonNullable<Backtest['metrics']>; label: string; suffix?: string }[] = [
    { key: 'total_return_pct', label: 'Total Return', suffix: '%' },
    { key: 'cagr_pct', label: 'CAGR', suffix: '%' },
    { key: 'sharpe_ratio', label: 'Sharpe Ratio' },
    { key: 'max_drawdown_pct', label: 'Max Drawdown', suffix: '%' },
    { key: 'annualized_volatility_pct', label: 'Volatility', suffix: '%' },
    { key: 'number_of_trades', label: '# Trades' },
  ];

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-xl font-semibold">Strategy Comparison</h1>
        <p className="text-terminal-muted text-sm">
          Select completed backtests to compare, side by side, with no ranking implied.
        </p>
      </div>

      <div className="card">
        <h2 className="text-sm font-semibold text-terminal-muted uppercase tracking-wide mb-3">
          Select Backtests
        </h2>
        <div className="space-y-1 max-h-56 overflow-y-auto">
          {backtests.map((bt) => (
            <label key={bt.id} className="flex items-center gap-2 text-sm py-1 cursor-pointer">
              <input type="checkbox" checked={selected.includes(bt.id)} onChange={() => toggle(bt.id)} />
              <span>{bt.symbol} · {bt.strategy_key} ({new Date(bt.created_at).toLocaleDateString()})</span>
            </label>
          ))}
          {backtests.length === 0 && (
            <p className="text-terminal-muted text-sm">No completed backtests yet.</p>
          )}
        </div>
      </div>

      {compared.length > 0 && (
        <div className="card overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-terminal-muted text-xs uppercase">
                <th className="py-2 pr-4">Metric</th>
                {compared.map((bt) => (
                  <th key={bt.id} className="py-2 pr-4">{bt.symbol} · {bt.strategy_key}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-terminal-border">
              {metricRows.map((row) => (
                <tr key={row.key}>
                  <td className="py-2 pr-4 text-terminal-muted">{row.label}</td>
                  {compared.map((bt) => (
                    <td key={bt.id} className="py-2 pr-4">
                      {bt.metrics
                        ? `${Number(bt.metrics[row.key]).toFixed(2)}${row.suffix ?? ''}`
                        : '—'}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
