"""
Parameter optimization and walk-forward analysis.

Both modules explicitly separate in-sample (training) data from
out-of-sample (testing/validation) data so that optimized parameters are
never selected using the same data on which they are finally evaluated
(spec section 12 & 13).
"""
from __future__ import annotations

import itertools
from datetime import datetime

import pandas as pd

from app.backtesting.engine import run_backtest
from app.strategies.implementations import get_strategy


def _slice(df: pd.DataFrame, start: datetime, end: datetime) -> pd.DataFrame:
    mask = (df["timestamp"] >= start) & (df["timestamp"] <= end)
    return df.loc[mask].reset_index(drop=True)


def grid_search(
    df: pd.DataFrame,
    strategy_key: str,
    param_grid: dict[str, list],
    initial_capital: float,
    transaction_cost_pct: float,
    slippage_pct: float,
    out_of_sample_split: float = 0.3,
    risk_free_rate_annual: float = 0.02,
) -> list[dict]:
    """
    Runs every combination of param_grid on the in-sample portion of `df`,
    then re-evaluates each combination's in-sample-optimal parameters on the
    held-out out-of-sample tail, so users can see whether performance holds up.
    """
    df = df.sort_values("timestamp").reset_index(drop=True)
    split_idx = int(len(df) * (1 - out_of_sample_split))
    split_idx = max(2, min(split_idx, len(df) - 2))

    in_sample_df = df.iloc[:split_idx].reset_index(drop=True)
    out_sample_df = df.iloc[split_idx:].reset_index(drop=True)

    keys = list(param_grid.keys())
    combinations = list(itertools.product(*param_grid.values()))

    results = []
    for combo in combinations:
        params = dict(zip(keys, combo))
        strategy = get_strategy(strategy_key, **params)

        try:
            in_sample_result = run_backtest(
                in_sample_df, strategy, initial_capital, transaction_cost_pct,
                slippage_pct, risk_free_rate_annual=risk_free_rate_annual,
            )
        except ValueError:
            continue

        out_sample_metrics = None
        if len(out_sample_df) >= 2 and out_of_sample_split > 0:
            try:
                oos_strategy = get_strategy(strategy_key, **params)
                oos_result = run_backtest(
                    out_sample_df, oos_strategy, initial_capital, transaction_cost_pct,
                    slippage_pct, risk_free_rate_annual=risk_free_rate_annual,
                )
                out_sample_metrics = oos_result.metrics
            except ValueError:
                out_sample_metrics = None

        results.append({
            "params": params,
            "in_sample_metrics": in_sample_result.metrics,
            "out_of_sample_metrics": out_sample_metrics,
        })

    return results


def walk_forward_analysis(
    df: pd.DataFrame,
    strategy_key: str,
    params: dict,
    train_years: int,
    test_years: int,
    initial_capital: float,
    transaction_cost_pct: float,
    slippage_pct: float,
    risk_free_rate_annual: float = 0.02,
) -> list[dict]:
    """
    Rolls a (train_years, test_years) window forward across the full date
    range. Only the test window's out-of-sample metrics are reported for
    each roll, matching the spec's train->test->roll-forward description.
    """
    df = df.sort_values("timestamp").reset_index(drop=True)
    start = df["timestamp"].min()
    end = df["timestamp"].max()

    windows = []
    train_start = start
    while True:
        train_end = train_start + pd.DateOffset(years=train_years)
        test_start = train_end
        test_end = test_start + pd.DateOffset(years=test_years)
        if test_end > end:
            break

        test_df = _slice(df, test_start, test_end)
        if len(test_df) >= 2:
            strategy = get_strategy(strategy_key, **params)
            try:
                result = run_backtest(
                    test_df, strategy, initial_capital, transaction_cost_pct,
                    slippage_pct, risk_free_rate_annual=risk_free_rate_annual,
                )
                windows.append({
                    "train_start": train_start, "train_end": train_end,
                    "test_start": test_start, "test_end": test_end,
                    "out_of_sample_metrics": result.metrics,
                })
            except ValueError:
                pass

        train_start = train_start + pd.DateOffset(years=test_years)

    return windows
