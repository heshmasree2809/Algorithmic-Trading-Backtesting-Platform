import {
  ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip, CartesianGrid, Line, ComposedChart,
} from 'recharts';
import type { EquityPoint } from '../types';

function formatDate(ts: string) {
  return new Date(ts).toLocaleDateString();
}

export function EquityCurveChart({ data }: { data: EquityPoint[] }) {
  return (
    <div className="card">
      <div className="label mb-2">Equity Curve</div>
      <ResponsiveContainer width="100%" height={280}>
        <AreaChart data={data}>
          <defs>
            <linearGradient id="equityFill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#3ddc97" stopOpacity={0.4} />
              <stop offset="95%" stopColor="#3ddc97" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#1e2732" />
          <XAxis dataKey="timestamp" tickFormatter={formatDate} stroke="#8a99a8" fontSize={11} minTickGap={40} />
          <YAxis stroke="#8a99a8" fontSize={11} domain={['auto', 'auto']} />
          <Tooltip
            contentStyle={{ background: '#121821', border: '1px solid #1e2732', fontSize: 12 }}
            labelFormatter={formatDate}
            formatter={(value: number) => [`$${value.toLocaleString(undefined, { maximumFractionDigits: 0 })}`, 'Portfolio Value']}
          />
          <Area type="monotone" dataKey="total_value" stroke="#3ddc97" fill="url(#equityFill)" strokeWidth={2} />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}

export function DrawdownChart({ data }: { data: EquityPoint[] }) {
  let peak = -Infinity;
  const drawdownData = data.map((d) => {
    peak = Math.max(peak, d.total_value);
    const drawdown = peak > 0 ? (d.total_value / peak - 1) * 100 : 0;
    return { timestamp: d.timestamp, drawdown };
  });

  return (
    <div className="card">
      <div className="label mb-2">Drawdown</div>
      <ResponsiveContainer width="100%" height={200}>
        <ComposedChart data={drawdownData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1e2732" />
          <XAxis dataKey="timestamp" tickFormatter={formatDate} stroke="#8a99a8" fontSize={11} minTickGap={40} />
          <YAxis stroke="#8a99a8" fontSize={11} />
          <Tooltip
            contentStyle={{ background: '#121821', border: '1px solid #1e2732', fontSize: 12 }}
            labelFormatter={formatDate}
            formatter={(value: number) => [`${value.toFixed(2)}%`, 'Drawdown']}
          />
          <Line type="monotone" dataKey="drawdown" stroke="#ef4444" dot={false} strokeWidth={1.5} />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}
