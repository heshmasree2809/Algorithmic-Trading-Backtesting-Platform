import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { createBacktest, getInstruments, getStrategies } from '../services/api';
import type { Instrument, StrategyDef } from '../types';

export default function StrategyLabPage() {
  const [instruments, setInstruments] = useState<Instrument[]>([]);
  const [strategies, setStrategies] = useState<StrategyDef[]>([]);
  const [symbol, setSymbol] = useState('AAPL');
  const [strategyKey, setStrategyKey] = useState('');
  const [params, setParams] = useState<Record<string, number>>({});
  const [startDate, setStartDate] = useState('2020-01-01');
  const [endDate, setEndDate] = useState('2024-01-01');
  const [initialCapital, setInitialCapital] = useState(100000);
  const [transactionCostPct, setTransactionCostPct] = useState(0.001);
  const [slippagePct, setSlippagePct] = useState(0.0005);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    getInstruments().then(setInstruments).catch(() => {});
    getStrategies().then((s) => {
      setStrategies(s);
      if (s.length) {
        setStrategyKey(s[0].key);
        setParams(s[0].default_params as Record<string, number>);
      }
    }).catch(() => {});
  }, []);

  function handleStrategyChange(key: string) {
    setStrategyKey(key);
    const found = strategies.find((s) => s.key === key);
    setParams((found?.default_params as Record<string, number>) ?? {});
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      const bt = await createBacktest({
        symbol,
        strategy_key: strategyKey,
        start_date: startDate,
        end_date: endDate,
        initial_capital: initialCapital,
        transaction_cost_pct: transactionCostPct,
        slippage_pct: slippagePct,
        position_sizing: 'full',
        fixed_fraction: 1.0,
        params,
      });
      navigate(`/backtests/${bt.id}`);
    } catch (err: any) {
      setError(err?.response?.data?.detail ?? 'Failed to launch backtest.');
    } finally {
      setSubmitting(false);
    }
  }

  const selectedStrategy = strategies.find((s) => s.key === strategyKey);

  return (
    <div className="space-y-4 max-w-3xl">
      <div>
        <h1 className="text-xl font-semibold">Strategy Lab</h1>
        <p className="text-terminal-muted text-sm">
          Configure a strategy and launch a historical simulation.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="card space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="label">Symbol</label>
            <select className="input" value={symbol} onChange={(e) => setSymbol(e.target.value)}>
              {instruments.length === 0 && <option value={symbol}>{symbol}</option>}
              {instruments.map((i) => <option key={i.symbol} value={i.symbol}>{i.symbol}</option>)}
            </select>
          </div>
          <div>
            <label className="label">Strategy</label>
            <select className="input" value={strategyKey} onChange={(e) => handleStrategyChange(e.target.value)}>
              {strategies.map((s) => <option key={s.key} value={s.key}>{s.name}</option>)}
            </select>
          </div>
        </div>

        {selectedStrategy && (
          <p className="text-xs text-terminal-muted -mt-2">{selectedStrategy.description}</p>
        )}

        {selectedStrategy && Object.keys(params).length > 0 && (
          <div className="grid grid-cols-3 gap-3">
            {Object.entries(params).map(([key, value]) => (
              <div key={key}>
                <label className="label">{key.replace(/_/g, ' ')}</label>
                <input
                  type="number" step="any" className="input" value={value}
                  onChange={(e) => setParams({ ...params, [key]: Number(e.target.value) })}
                />
              </div>
            ))}
          </div>
        )}

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="label">Start Date</label>
            <input type="date" className="input" value={startDate} onChange={(e) => setStartDate(e.target.value)} />
          </div>
          <div>
            <label className="label">End Date</label>
            <input type="date" className="input" value={endDate} onChange={(e) => setEndDate(e.target.value)} />
          </div>
        </div>

        <div className="grid grid-cols-3 gap-4">
          <div>
            <label className="label">Initial Capital ($)</label>
            <input
              type="number" min={1} className="input" value={initialCapital}
              onChange={(e) => setInitialCapital(Number(e.target.value))}
            />
          </div>
          <div>
            <label className="label">Transaction Cost (%)</label>
            <input
              type="number" step="0.001" min={0} className="input" value={transactionCostPct * 100}
              onChange={(e) => setTransactionCostPct(Number(e.target.value) / 100)}
            />
          </div>
          <div>
            <label className="label">Slippage (%)</label>
            <input
              type="number" step="0.001" min={0} className="input" value={slippagePct * 100}
              onChange={(e) => setSlippagePct(Number(e.target.value) / 100)}
            />
          </div>
        </div>

        {error && <p className="text-terminal-danger text-sm">{error}</p>}

        <button type="submit" disabled={submitting || !strategyKey} className="btn-primary w-full">
          {submitting ? 'Running Backtest…' : 'Launch Backtest'}
        </button>

        <p className="text-[10px] text-terminal-muted leading-snug">
          This runs a historical simulation only. Results do not guarantee future performance
          and this platform never executes real trades.
        </p>
      </form>
    </div>
  );
}
