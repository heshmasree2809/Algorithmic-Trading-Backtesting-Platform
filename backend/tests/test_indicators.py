import numpy as np
import pandas as pd

from app.indicators.indicators import (
    sma, ema, rsi, macd, bollinger_bands, atr, obv, stochastic_oscillator, roc,
)


def test_sma_matches_manual_rolling_mean(noisy_df):
    result = sma(noisy_df["close"], 10)
    expected = noisy_df["close"].rolling(10).mean()
    pd.testing.assert_series_equal(result, expected, check_names=False)


def test_sma_has_nan_until_period_reached(noisy_df):
    result = sma(noisy_df["close"], 20)
    assert result.iloc[:19].isna().all()
    assert not pd.isna(result.iloc[19])


def test_ema_reacts_faster_than_sma_to_a_shock():
    prices = pd.Series([100] * 30 + [130] * 10)
    e = ema(prices, 10)
    s = sma(prices, 10)
    # A few bars after the shock, EMA should have moved further toward
    # the new level than the SMA (it weights recent data more heavily).
    assert e.iloc[32] > s.iloc[32]


def test_rsi_is_bounded_0_100(noisy_df):
    result = rsi(noisy_df["close"], 14).dropna()
    assert (result >= 0).all() and (result <= 100).all()


def test_rsi_is_high_in_a_strict_uptrend(uptrend_df):
    result = rsi(uptrend_df["close"], 14).dropna()
    # A monotonic uptrend has no losses, so RSI should sit at/near 100.
    assert (result > 95).all()


def test_macd_returns_expected_columns(noisy_df):
    result = macd(noisy_df["close"])
    assert set(result.columns) == {"macd", "signal", "histogram"}
    assert np.allclose(
        result["histogram"].dropna(), (result["macd"] - result["signal"]).dropna()
    )


def test_bollinger_bands_ordering(noisy_df):
    bands = bollinger_bands(noisy_df["close"], period=20, num_std=2.0).dropna()
    assert (bands["upper"] >= bands["middle"]).all()
    assert (bands["middle"] >= bands["lower"]).all()


def test_atr_non_negative(noisy_df):
    result = atr(noisy_df["high"], noisy_df["low"], noisy_df["close"], 14).dropna()
    assert (result >= 0).all()


def test_obv_direction_matches_price_direction():
    close = pd.Series([10, 11, 10.5, 12])
    volume = pd.Series([100, 100, 100, 100])
    result = obv(close, volume)
    # Up day adds volume, down day subtracts it.
    assert result.iloc[1] == 100
    assert result.iloc[2] == 0
    assert result.iloc[3] == 100


def test_stochastic_oscillator_bounded(noisy_df):
    result = stochastic_oscillator(noisy_df["high"], noisy_df["low"], noisy_df["close"]).dropna()
    assert (result["%K"] >= 0).all() and (result["%K"] <= 100).all()


def test_roc_zero_when_price_unchanged():
    close = pd.Series([100] * 20)
    result = roc(close, 5).dropna()
    assert np.allclose(result, 0.0)


def test_indicators_are_causal_no_lookahead(noisy_df):
    """Perturbing a future bar must not change an indicator's past values."""
    truncated = noisy_df.iloc[:100].copy()
    full = noisy_df.copy()
    full.loc[100:, "close"] = full.loc[100:, "close"] + 1000  # huge future shock

    r1 = sma(truncated["close"], 10)
    r2 = sma(full["close"], 10).iloc[:100]
    pd.testing.assert_series_equal(r1, r2, check_names=False)
