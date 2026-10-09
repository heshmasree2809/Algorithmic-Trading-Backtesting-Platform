"""
Backtesting Engine.

Look-ahead bias prevention (critical requirement, spec section 7 & 19):
  1. Signals are generated once, up front, from the full price history, but
     every indicator used to build them (SMA, RSI, MACD, Bollinger, ...) is
     computed with pandas rolling/ewm windows that are strictly causal: the
     value at index i is a function only of rows <= i.
  2. Execution never happens on the same bar the signal was formed. A signal
     computed using bar i's close is executed at bar (i+1)'s open. This
     "signal at close, fill at next open" convention is the standard way to
     eliminate look-ahead bias in an event-driven or vectorized backtest.
  3. Portfolio state (cash/position) carried strictly forward in time, never
     mutated retroactively.
"""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from app.backtesting.portfolio import Portfolio
from app.risk.metrics import full_performance_report
from app.strategies.base import Strategy, BUY, SELL


@dataclass
class BacktestResult:
    trades: list
    snapshots: list
    metrics: dict


def run_backtest(
    df: pd.DataFrame,
    strategy: Strategy,
    initial_capital: float,
    transaction_cost_pct: float,
    slippage_pct: float,
    position_sizing: str = "full",
    fixed_fraction: float = 1.0,
    risk_free_rate_annual: float = 0.02,
) -> BacktestResult:
    """
    df must contain columns: timestamp, open, high, low, close, volume,
    sorted ascending chronologically with no gaps in ordering.
    """
    if df.empty or len(df) < 2:
        raise ValueError("Insufficient market data to run a backtest.")

    df = df.sort_values("timestamp").reset_index(drop=True)
    signals = strategy.generate_signals(df)

    fraction = fixed_fraction if position_sizing == "fixed_fraction" else 1.0
    portfolio = Portfolio(
        initial_capital=initial_capital,
        symbol=getattr(strategy, "symbol", "SYMBOL"),
        transaction_cost_pct=transaction_cost_pct,
        slippage_pct=slippage_pct,
    )

    n = len(df)
    for i in range(n):
        row = df.iloc[i]
        timestamp = row["timestamp"]

        # Execute the PREVIOUS bar's signal at THIS bar's open price. This is
        # what prevents look-ahead bias: bar i-1's close generated the signal,
        # bar i's open is the earliest tradable price after that information
        # was available.
        if i > 0:
            prior_signal = signals.iloc[i - 1]
            open_price = row["open"]
            if prior_signal == BUY:
                portfolio.buy(timestamp, open_price, fraction_of_cash=fraction)
            elif prior_signal == SELL:
                portfolio.sell(timestamp, open_price)

        # Mark-to-market at the close of every bar.
        portfolio.mark_to_market(timestamp, row["close"])

    # Liquidate any open position at the final close so the equity curve
    # reflects fully realized performance.
    if portfolio.position_qty > 0:
        last_row = df.iloc[-1]
        portfolio.sell(last_row["timestamp"], last_row["close"])
        portfolio.snapshots[-1] = portfolio.snapshots[-1].__class__(
            timestamp=last_row["timestamp"], cash=portfolio.cash,
            holdings_value=0.0, total_value=portfolio.cash, position_qty=0.0,
        )

    equity_curve = pd.Series([s.total_value for s in portfolio.snapshots])
    timestamps = pd.Series([s.timestamp for s in portfolio.snapshots])

    metrics = full_performance_report(
        equity_curve=equity_curve,
        timestamps=timestamps,
        trade_pnls=portfolio.closed_trade_pnls,
        entry_exit_pairs=portfolio.entry_exit_pairs,
        risk_free_rate_annual=risk_free_rate_annual,
    )

    return BacktestResult(trades=portfolio.trades, snapshots=portfolio.snapshots, metrics=metrics)
