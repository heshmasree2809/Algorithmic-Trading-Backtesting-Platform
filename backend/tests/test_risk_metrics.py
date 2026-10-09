import numpy as np
import pandas as pd
import pytest

from app.risk.metrics import (
    total_return, cagr, annualized_volatility, sharpe_ratio, sortino_ratio,
    max_drawdown, calmar_ratio, trade_statistics, average_holding_period_days,
)


def test_total_return_simple_case():
    equity = pd.Series([100, 110, 121])
    assert total_return(equity) == pytest.approx(0.21)


def test_cagr_one_year_doubling():
    equity = pd.Series([100, 200])
    timestamps = pd.Series(pd.to_datetime(["2020-01-01", "2021-01-01"]))
    result = cagr(equity, timestamps)
    assert result == pytest.approx(1.0, rel=0.02)


def test_cagr_handles_flat_equity():
    equity = pd.Series([100, 100, 100])
    timestamps = pd.Series(pd.to_datetime(["2020-01-01", "2020-06-01", "2021-01-01"]))
    assert cagr(equity, timestamps) == pytest.approx(0.0)


def test_annualized_volatility_zero_for_constant_returns():
    returns = pd.Series([0.001] * 100)
    assert annualized_volatility(returns) == pytest.approx(0.0, abs=1e-9)


def test_sharpe_ratio_zero_when_no_volatility():
    returns = pd.Series([0.001] * 50)
    assert sharpe_ratio(returns, risk_free_rate_annual=0.0) == 0.0


def test_sharpe_ratio_positive_for_positive_drift():
    rng = np.random.default_rng(1)
    returns = pd.Series(rng.normal(0.001, 0.005, 500))
    assert sharpe_ratio(returns, risk_free_rate_annual=0.0) > 0


def test_sortino_only_penalizes_downside():
    # All positive returns -> no downside deviation -> function returns 0
    # by definition (guards against div-by-zero), which is the documented
    # edge-case behavior.
    returns = pd.Series([0.01, 0.02, 0.015, 0.03])
    assert sortino_ratio(returns) == 0.0


def test_max_drawdown_detects_known_peak_to_trough():
    equity = pd.Series([100, 120, 90, 95, 130])
    # Peak 120 -> trough 90 => drawdown of -25%
    assert max_drawdown(equity) == pytest.approx(-0.25)


def test_max_drawdown_zero_for_monotonic_increase():
    equity = pd.Series([100, 110, 120, 130])
    assert max_drawdown(equity) == pytest.approx(0.0)


def test_calmar_ratio_divides_cagr_by_abs_drawdown():
    assert calmar_ratio(0.20, -0.10) == pytest.approx(2.0)


def test_calmar_ratio_zero_when_no_drawdown():
    assert calmar_ratio(0.20, 0.0) == 0.0


def test_trade_statistics_win_rate_and_profit_factor():
    pnls = [100, -50, 200, -25, 75]
    stats = trade_statistics(pnls)
    assert stats["number_of_trades"] == 5
    assert stats["win_rate_pct"] == pytest.approx(60.0)
    assert stats["profit_factor"] == pytest.approx((100 + 200 + 75) / (50 + 25))
    assert stats["average_win"] == pytest.approx((100 + 200 + 75) / 3)
    assert stats["average_loss"] == pytest.approx((-50 - 25) / 2)


def test_trade_statistics_handles_no_trades():
    stats = trade_statistics([])
    assert stats["number_of_trades"] == 0
    assert stats["win_rate_pct"] == 0.0


def test_average_holding_period_days():
    pairs = [
        (pd.Timestamp("2023-01-01"), pd.Timestamp("2023-01-11")),  # 10 days
        (pd.Timestamp("2023-02-01"), pd.Timestamp("2023-02-06")),  # 5 days
    ]
    assert average_holding_period_days(pairs) == pytest.approx(7.5)
