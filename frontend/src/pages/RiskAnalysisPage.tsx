import { useEffect, useState } from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid, ResponsiveContainer } from 'recharts';
import { listBacktests, getBacktest } from '../services/api';
import type { Backtest, BacktestDetail } from '../types';
import MetricCard from '../components/MetricCard';

export default function RiskAnalysisPage() {
  const [backtests, setBacktests] = useState<Backtest[]>([]);
  const [selectedId, setSelectedId] = useState<string>('');
  const [detail, setDetail] = useState<BacktestDetail | null>(null);

  useEffect(() => {
    listBacktests().then((all) => {
      const completed = all.filter((b) => b.status === 'completed');
      setBacktests(completed);
      if (completed.length) setSelectedId(completed[0].id);
    });
  }, []);

  useEffect(() => {
    if (selectedId) getBacktest(selectedId).then(setDetail);
  }, [selectedId]);

  const returnDistribution = detail
    ? detail.equity_curve.slice(1).map((point, i) => {
        const prev = detail.equity_curve[i].total_value;
        const ret = prev !== 0 ? ((point.total_value - prev) / prev) * 100 : 0;
        return { date: point.timestamp, dailyReturnPct: ret };
      })
    : [];

  // Bucket returns into a histogram
  const buckets: Record<string, number> = {};
  returnDistribution.forEach((d) => {
    const bucket = Math.round(d.dailyReturnPct * 2) / 2; // nearest 0.5%
    const key = bucket.toFixed(1);
    buckets[key] = (buckets[key] || 0) + 1;
  });
  const histogramData = Object.entries(buckets)
    .map(([bucket, count]) => ({ bucket: Number(bucket), count }))
    .sort((a, b) => a.bucket - b.bucket);

  const m = detail?.metrics;
  const exposure = detail
    ? (detail.equity_curve.filter((p) => p.position_qty > 0).length / Math.max(detail.equity_curve.length, 1)) * 100
    : null;

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-xl font-semibold">Risk Analysis</h1>
        <p className="text-terminal-muted text-sm">Volatility, drawdown, and return-distribution diagnostics.</p>
      </div>

      <div className="card">
        <label className="label">Backtest</label>
        <select className="input max-w-md" value={selectedId} onChange={(e) => setSelectedId(e.target.value)}>
          {backtests.map((bt) => (
            <option key={bt.id} value={bt.id}>{bt.symbol} · {bt.strategy_key} ({new Date(bt.created_at).toLocaleDateString()})</option>
          ))}
        </select>
      </div>

      {m && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <MetricCard label="Volatility (Ann.)" value={`${m.annualized_volatility_pct.toFixed(1)}%`} />
          <MetricCard label="Max Drawdown" value={`${m.max_drawdown_pct.toFixed(1)}%`} negative />
          <MetricCard label="Sharpe" value={m.sharpe_ratio.toFixed(2)} />
          <MetricCard label="Sortino" value={m.sortino_ratio.toFixed(2)} />
          <MetricCard label="Exposure (time in market)" value={exposure !== null ? `${exposure.toFixed(0)}%` : '—'} />
          <MetricCard label="Calmar Ratio" value={m.calmar_ratio.toFixed(2)} />
          <MetricCard label="Profit Factor" value={Number.isFinite(m.profit_factor) ? m.profit_factor.toFixed(2) : '∞'} />
          <MetricCard label="Avg Holding (days)" value={m.average_holding_period_days.toFixed(1)} />
        </div>
      )}

      {histogramData.length > 0 && (
        <div className="card">
          <div className="label mb-2">Daily Return Distribution</div>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={histogramData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e2732" />
              <XAxis dataKey="bucket" tickFormatter={(v) => `${v}%`} stroke="#8a99a8" fontSize={11} />
              <YAxis stroke="#8a99a8" fontSize={11} />
              <Tooltip contentStyle={{ background: '#121821', border: '1px solid #1e2732', fontSize: 12 }} />
              <Bar dataKey="count" fill="#3ddc97" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}
