import numpy as np
import pandas as pd

from app.services.market_data_service import clean_ohlcv


def _base_df():
    dates = pd.bdate_range("2023-01-02", periods=10)
    return pd.DataFrame({
        "timestamp": dates,
        "open": np.full(10, 100.0),
        "high": np.full(10, 101.0),
        "low": np.full(10, 99.0),
        "close": np.full(10, 100.5),
        "adjusted_close": np.full(10, 100.5),
        "volume": np.full(10, 1_000_000.0),
    })


def test_clean_removes_exact_duplicate_timestamps():
    df = _base_df()
    dup = pd.concat([df, df.iloc[[0]]], ignore_index=True)
    cleaned = clean_ohlcv(dup)
    assert cleaned["timestamp"].is_unique


def test_clean_rejects_negative_or_zero_prices():
    df = _base_df()
    df.loc[3, "close"] = -5.0
    cleaned = clean_ohlcv(df)
    assert len(cleaned) == len(df) - 1


def test_clean_rejects_high_less_than_low():
    df = _base_df()
    df.loc[2, "high"] = 50.0  # now high < low, invalid
    cleaned = clean_ohlcv(df)
    assert len(cleaned) == len(df) - 1


def test_clean_sorts_chronologically():
    df = _base_df()
    shuffled = df.sample(frac=1.0, random_state=1).reset_index(drop=True)
    cleaned = clean_ohlcv(shuffled)
    assert cleaned["timestamp"].is_monotonic_increasing


def test_clean_forward_fills_missing_close():
    df = _base_df()
    df.loc[5, "close"] = np.nan
    cleaned = clean_ohlcv(df)
    assert not cleaned["close"].isna().any()
    assert cleaned.loc[5, "close"] == cleaned.loc[4, "close"]


def test_clean_handles_empty_dataframe():
    empty = pd.DataFrame(columns=["timestamp", "open", "high", "low", "close", "adjusted_close", "volume"])
    result = clean_ohlcv(empty)
    assert result.empty
