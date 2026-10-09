import { useEffect, useState } from 'react';
import { getInstruments, getMarketData, getIndicator } from '../services/api';
import type { Instrument, OHLCVBar } from '../types';
import PriceChart from '../components/PriceChart';

const DEFAULT_START = '2023-01-01';
const DEFAULT_END = '2024-01-01';

export default function MarketExplorerPage() {
  const [instruments, setInstruments] = useState<Instrument[]>([]);
  const [symbol, setSymbol] = useState('AAPL');
  const [start, setStart] = useState(DEFAULT_START);
  const [end, setEnd] = useState(DEFAULT_END);
  const [bars, setBars] = useState<OHLCVBar[]>([]);
  const [rsiValue, setRsiValue] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getInstruments().then(setInstruments).catch(() => {});
  }, []);

  async function loadData() {
    setLoading(true);
    setError(null);
    try {
      const [marketData, rsi] = await Promise.all([
        getMarketData(symbol, start, end),
        getIndicator('rsi', symbol, start, end, 14),
      ]);
      setBars(marketData.bars);
      const lastRsi = rsi.points.filter((p) => p.value !== null).pop();
      setRsiValue(lastRsi?.value ?? null);
    } catch (err: any) {
      setError(err?.response?.data?.detail ?? 'Could not load market data.');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { loadData(); }, []); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-xl font-semibold">Market Explorer</h1>
        <p className="text-terminal-muted text-sm">Browse historical price, volume, and indicators.</p>
      </div>

      <div className="card flex flex-wrap items-end gap-4">
        <div>
          <label className="label">Symbol</label>
          <select className="input w-40" value={symbol} onChange={(e) => setSymbol(e.target.value)}>
            {instruments.length === 0 && <option value={symbol}>{symbol}</option>}
            {instruments.map((i) => (
              <option key={i.symbol} value={i.symbol}>{i.symbol}</option>
            ))}
          </select>
        </div>
        <div>
          <label className="label">Start Date</label>
          <input type="date" className="input w-40" value={start} onChange={(e) => setStart(e.target.value)} />
        </div>
        <div>
          <label className="label">End Date</label>
          <input type="date" className="input w-40" value={end} onChange={(e) => setEnd(e.target.value)} />
        </div>
        <button className="btn-primary" onClick={loadData} disabled={loading}>
          {loading ? 'Loading…' : 'Load'}
        </button>
        {rsiValue !== null && (
          <div className="ml-auto text-sm">
            <span className="text-terminal-muted">Latest RSI(14): </span>
            <span className={rsiValue > 70 ? 'metric-value-negative' : rsiValue < 30 ? 'metric-value-positive' : ''}>
              {rsiValue.toFixed(1)}
            </span>
          </div>
        )}
      </div>

      {error && <p className="text-terminal-danger text-sm">{error}</p>}
      {!error && bars.length > 0 && <PriceChart bars={bars} />}
      {!error && !loading && bars.length === 0 && (
        <p className="text-terminal-muted text-sm">No data loaded yet.</p>
      )}
    </div>
  );
}
