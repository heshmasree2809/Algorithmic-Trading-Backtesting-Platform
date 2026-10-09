import {
  ResponsiveContainer, ComposedChart, Line, Bar, XAxis, YAxis, Tooltip,
  CartesianGrid, Scatter, ReferenceDot,
} from 'recharts';
import type { OHLCVBar, Trade } from '../types';

function formatDate(ts: string) {
  return new Date(ts).toLocaleDateString();
}

interface PriceChartProps {
  bars: OHLCVBar[];
  trades?: Trade[];
}

export default function PriceChart({ bars, trades = [] }: PriceChartProps) {
  const data = bars.map((b) => ({ ...b, dateLabel: formatDate(b.timestamp) }));

  const buyMarkers = trades.filter((t) => t.side === 'BUY');
  const sellMarkers = trades.filter((t) => t.side === 'SELL');

  const closestBarValue = (ts: string) => {
    const target = new Date(ts).getTime();
    let best = data[0];
    let bestDiff = Infinity;
    for (const bar of data) {
      const diff = Math.abs(new Date(bar.timestamp).getTime() - target);
      if (diff < bestDiff) { bestDiff = diff; best = bar; }
    }
    return best?.close ?? 0;
  };

  return (
    <div className="space-y-2">
      <div className="card">
        <div className="label mb-2">Price with Trade Markers</div>
        <ResponsiveContainer width="100%" height={320}>
          <ComposedChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e2732" />
            <XAxis dataKey="timestamp" tickFormatter={formatDate} stroke="#8a99a8" fontSize={11} minTickGap={40} />
            <YAxis stroke="#8a99a8" fontSize={11} domain={['auto', 'auto']} />
            <Tooltip
              contentStyle={{ background: '#121821', border: '1px solid #1e2732', fontSize: 12 }}
              labelFormatter={formatDate}
            />
            <Line type="monotone" dataKey="close" stroke="#60a5fa" dot={false} strokeWidth={1.5} name="Close" />
            {buyMarkers.map((t, i) => (
              <ReferenceDot
                key={`buy-${i}`}
                x={t.timestamp}
                y={closestBarValue(t.timestamp)}
                r={5}
                fill="#3ddc97"
                stroke="none"
              />
            ))}
            {sellMarkers.map((t, i) => (
              <ReferenceDot
                key={`sell-${i}`}
                x={t.timestamp}
                y={closestBarValue(t.timestamp)}
                r={5}
                fill="#ef4444"
                stroke="none"
              />
            ))}
          </ComposedChart>
        </ResponsiveContainer>
        <div className="flex gap-4 text-xs text-terminal-muted mt-2">
          <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-terminal-accent inline-block" /> Buy</span>
          <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-terminal-danger inline-block" /> Sell</span>
        </div>
      </div>
      <div className="card">
        <div className="label mb-2">Volume</div>
        <ResponsiveContainer width="100%" height={120}>
          <ComposedChart data={data}>
            <XAxis dataKey="timestamp" tickFormatter={formatDate} stroke="#8a99a8" fontSize={10} minTickGap={40} />
            <YAxis stroke="#8a99a8" fontSize={10} />
            <Tooltip contentStyle={{ background: '#121821', border: '1px solid #1e2732', fontSize: 12 }} labelFormatter={formatDate} />
            <Bar dataKey="volume" fill="#3b82f6" opacity={0.6} />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
