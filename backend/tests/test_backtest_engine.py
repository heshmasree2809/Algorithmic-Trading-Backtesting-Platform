import pandas as pd
import pytest

from app.backtesting.engine import run_backtest
from app.strategies.implementations import MovingAverageCrossoverStrategy


def test_backtest_runs_end_to_end_and_produces_metrics(noisy_df):
    strategy = MovingAverageCrossoverStrategy(short_window=10, long_window=30)
    result = run_backtest(
        noisy_df, strategy, initial_capital=100_000,
        transaction_cost_pct=0.001, slippage_pct=0.0005,
    )
    assert "sharpe_ratio" in result.metrics
    assert "max_drawdown_pct" in result.metrics
    assert len(result.snapshots) == len(noisy_df)


def test_backtest_raises_on_insufficient_data():
    df = pd.DataFrame({
        "timestamp": [pd.Timestamp("2023-01-01")],
        "open": [100], "high": [101], "low": [99], "close": [100], "volume": [1000],
    })
    strategy = MovingAverageCrossoverStrategy()
    with pytest.raises(ValueError):
        run_backtest(df, strategy, 100_000, 0.001, 0.0005)


def test_signal_executes_at_next_bar_open_not_same_bar_close():
    """
    This is the core look-ahead-bias regression test: a BUY signal formed
    using bar i's close must fill at bar (i+1)'s open, never at bar i's
    own close/open.
    """
    dates = pd.bdate_range("2023-01-02", periods=80)
    # Flat prices, then a sudden jump that should trigger a golden cross.
    close = [100.0] * 40 + [100 + i for i in range(40)]
    df = pd.DataFrame({
        "timestamp": dates,
        "open": [c - 0.1 for c in close],
        "high": [c + 0.2 for c in close],
        "low": [c - 0.2 for c in close],
        "close": close,
        "volume": [1_000_000.0] * 80,
    })
    strategy = MovingAverageCrossoverStrategy(short_window=5, long_window=20)
    signals = strategy.generate_signals(df)

    result = run_backtest(df, strategy, 100_000, 0.0, 0.0)

    buy_trades = [t for t in result.trades if t.side == "BUY"]
    assert buy_trades, "expected at least one BUY trade"

    first_buy = buy_trades[0]
    signal_bar_index = df.index[df["timestamp"] < first_buy.timestamp].max()
    # The signal that caused this trade must have been formed on the PRIOR bar.
    assert signals.iloc[signal_bar_index] == "BUY"
    # And the execution price must equal that prior bar's *next* open, i.e.
    # this trade's own bar's open (not its close).
    executed_bar = df[df["timestamp"] == first_buy.timestamp].iloc[0]
    assert first_buy.execution_price == pytest.approx(executed_bar["open"])


def test_transaction_costs_reduce_final_equity_versus_zero_cost(noisy_df):
    strategy_a = MovingAverageCrossoverStrategy(short_window=10, long_window=30)
    strategy_b = MovingAverageCrossoverStrategy(short_window=10, long_window=30)

    zero_cost = run_backtest(noisy_df, strategy_a, 100_000, 0.0, 0.0)
    with_cost = run_backtest(noisy_df, strategy_b, 100_000, 0.01, 0.005)  # 1% + 0.5%

    final_zero = zero_cost.snapshots[-1].total_value
    final_cost = with_cost.snapshots[-1].total_value
    assert final_cost <= final_zero


def test_open_position_is_liquidated_at_end_of_backtest(noisy_df):
    strategy = MovingAverageCrossoverStrategy(short_window=5, long_window=15)
    result = run_backtest(noisy_df, strategy, 100_000, 0.0, 0.0)
    assert result.snapshots[-1].position_qty == 0.0
