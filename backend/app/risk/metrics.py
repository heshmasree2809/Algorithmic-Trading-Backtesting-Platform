"""
Risk & performance analytics.

Formulas (documented per project spec section 9):

Total Return       = (V_end / V_start) - 1
CAGR               = (V_end / V_start) ** (365.25 / days) - 1
Daily Return        r_t = V_t / V_(t-1) - 1
Annualized Vol      = std(r_t) * sqrt(252)
Sharpe Ratio        = (mean(r_t) * 252 - risk_free_rate) / (std(r_t) * sqrt(252))
Sortino Ratio       = (mean(r_t) * 252 - risk_free_rate) / (downside_std(r_t) * sqrt(252))
                      downside_std uses only r_t < 0
Max Drawdown        = min over t of (V_t / running_max(V_0..t) - 1)
Calmar Ratio        = CAGR / abs(Max Drawdown)
Win Rate            = (# winning trades) / (# closed trades)
Profit Factor       = sum(winning trade PnL) / abs(sum(losing trade PnL))
Average Win/Loss    = mean realized PnL of winning / losing trades
Average Holding     = mean(exit_timestamp - entry_timestamp) across round-trip trades
Period              (in days)

All ratios use a 252 trading-day annualization convention, standard for
daily-bar equities data.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

TRADING_DAYS_PER_YEAR = 252


def compute_returns(equity_curve: pd.Series) -> pd.Series:
    return equity_curve.pct_change().dropna()


def total_return(equity_curve: pd.Series) -> float:
    if len(equity_curve) < 2 or equity_curve.iloc[0] == 0:
        return 0.0
    return float(equity_curve.iloc[-1] / equity_curve.iloc[0] - 1)


def cagr(equity_curve: pd.Series, timestamps: pd.Series) -> float:
    if len(equity_curve) < 2:
        return 0.0
    days = (timestamps.iloc[-1] - timestamps.iloc[0]).days
    if days <= 0 or equity_curve.iloc[0] <= 0:
        return 0.0
    years = days / 365.25
    ratio = equity_curve.iloc[-1] / equity_curve.iloc[0]
    if ratio <= 0:
        return -1.0
    return float(ratio ** (1 / years) - 1) if years > 0 else 0.0


def annualized_volatility(returns: pd.Series) -> float:
    if len(returns) < 2:
        return 0.0
    return float(returns.std(ddof=1) * np.sqrt(TRADING_DAYS_PER_YEAR))


def sharpe_ratio(returns: pd.Series, risk_free_rate_annual: float = 0.0) -> float:
    if len(returns) < 2 or returns.std(ddof=1) == 0:
        return 0.0
    excess_annual_return = returns.mean() * TRADING_DAYS_PER_YEAR - risk_free_rate_annual
    vol = returns.std(ddof=1) * np.sqrt(TRADING_DAYS_PER_YEAR)
    return float(excess_annual_return / vol) if vol != 0 else 0.0


def sortino_ratio(returns: pd.Series, risk_free_rate_annual: float = 0.0) -> float:
    downside = returns[returns < 0]
    if len(returns) < 2 or len(downside) == 0 or downside.std(ddof=1) == 0:
        return 0.0
    excess_annual_return = returns.mean() * TRADING_DAYS_PER_YEAR - risk_free_rate_annual
    downside_vol = downside.std(ddof=1) * np.sqrt(TRADING_DAYS_PER_YEAR)
    return float(excess_annual_return / downside_vol) if downside_vol != 0 else 0.0


def max_drawdown(equity_curve: pd.Series) -> float:
    if equity_curve.empty:
        return 0.0
    running_max = equity_curve.cummax()
    drawdown = equity_curve / running_max - 1
    return float(drawdown.min())


def calmar_ratio(cagr_value: float, max_dd: float) -> float:
    if max_dd == 0:
        return 0.0
    return float(cagr_value / abs(max_dd))


def trade_statistics(trade_pnls: list[float]) -> dict:
    """Win rate, profit factor, avg win/loss from a list of realized round-trip PnLs."""
    if not trade_pnls:
        return {
            "win_rate_pct": 0.0, "profit_factor": 0.0,
            "average_win": 0.0, "average_loss": 0.0, "number_of_trades": 0,
        }
    wins = [p for p in trade_pnls if p > 0]
    losses = [p for p in trade_pnls if p < 0]

    gross_profit = sum(wins)
    gross_loss = abs(sum(losses))

    return {
        "win_rate_pct": 100 * len(wins) / len(trade_pnls),
        "profit_factor": (gross_profit / gross_loss) if gross_loss > 0 else (float("inf") if gross_profit > 0 else 0.0),
        "average_win": float(np.mean(wins)) if wins else 0.0,
        "average_loss": float(np.mean(losses)) if losses else 0.0,
        "number_of_trades": len(trade_pnls),
    }


def average_holding_period_days(entry_exit_pairs: list[tuple]) -> float:
    if not entry_exit_pairs:
        return 0.0
    deltas = [(exit_ts - entry_ts).total_seconds() / 86400 for entry_ts, exit_ts in entry_exit_pairs]
    return float(np.mean(deltas))


def full_performance_report(
    equity_curve: pd.Series,
    timestamps: pd.Series,
    trade_pnls: list[float],
    entry_exit_pairs: list[tuple],
    risk_free_rate_annual: float = 0.02,
) -> dict:
    """Assembles the full PerformanceMetrics payload used by the API."""
    returns = compute_returns(equity_curve)
    tr = total_return(equity_curve)
    growth = cagr(equity_curve, timestamps)
    vol = annualized_volatility(returns)
    sharpe = sharpe_ratio(returns, risk_free_rate_annual)
    sortino = sortino_ratio(returns, risk_free_rate_annual)
    mdd = max_drawdown(equity_curve)
    calmar = calmar_ratio(growth, mdd)
    trade_stats = trade_statistics(trade_pnls)
    holding_period = average_holding_period_days(entry_exit_pairs)

    return {
        "total_return_pct": tr * 100,
        "cagr_pct": growth * 100,
        "annualized_volatility_pct": vol * 100,
        "sharpe_ratio": sharpe,
        "sortino_ratio": sortino,
        "max_drawdown_pct": mdd * 100,
        "calmar_ratio": calmar,
        **trade_stats,
        "average_holding_period_days": holding_period,
    }
