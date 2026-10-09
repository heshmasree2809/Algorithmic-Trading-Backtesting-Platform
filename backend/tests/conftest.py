"""Shared pytest fixtures: synthetic OHLCV data for deterministic tests."""
import pandas as pd
import numpy as np
import pytest


@pytest.fixture
def uptrend_df():
    """A clean, perfectly linear uptrend - useful for sanity-checking
    indicator and strategy math without noise."""
    dates = pd.bdate_range("2023-01-02", periods=120)
    close = np.linspace(100, 160, len(dates))
    df = pd.DataFrame({
        "timestamp": dates,
        "open": close - 0.2,
        "high": close + 0.5,
        "low": close - 0.5,
        "close": close,
        "adjusted_close": close,
        "volume": np.full(len(dates), 1_000_000.0),
    })
    return df


@pytest.fixture
def noisy_df():
    """Seeded random-walk data with realistic OHLC relationships."""
    rng = np.random.default_rng(42)
    dates = pd.bdate_range("2020-01-02", periods=750)
    returns = rng.normal(0.0003, 0.015, len(dates))
    close = 100 * np.cumprod(1 + returns)
    high = close * (1 + np.abs(rng.normal(0, 0.004, len(dates))))
    low = close * (1 - np.abs(rng.normal(0, 0.004, len(dates))))
    open_ = low + (high - low) * rng.uniform(0.2, 0.8, len(dates))
    volume = rng.integers(500_000, 5_000_000, len(dates)).astype(float)
    return pd.DataFrame({
        "timestamp": dates, "open": open_, "high": high, "low": low,
        "close": close, "adjusted_close": close, "volume": volume,
    })
