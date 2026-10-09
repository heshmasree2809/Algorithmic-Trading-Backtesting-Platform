"""
Technical indicator engine. Every function is a pure, vectorized
transformation of a `close`/OHLCV pandas Series/DataFrame into a new
Series/DataFrame, which makes each one trivially unit-testable and safe to
call from both the REST API and the strategy engine without duplicating math.

All indicators are causal: value at index i depends only on data at indices
<= i, which is required to keep the backtesting engine free of look-ahead bias.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


# ---------------- Trend ----------------

def sma(series: pd.Series, period: int) -> pd.Series:
    return series.rolling(window=period, min_periods=period).mean()


def ema(series: pd.Series, period: int) -> pd.Series:
    return series.ewm(span=period, adjust=False, min_periods=period).mean()


def wma(series: pd.Series, period: int) -> pd.Series:
    weights = np.arange(1, period + 1)
    return series.rolling(period, min_periods=period).apply(
        lambda x: np.dot(x, weights) / weights.sum(), raw=True
    )


def macd(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
    ema_fast = ema(series, fast)
    ema_slow = ema(series, slow)
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False, min_periods=signal).mean()
    histogram = macd_line - signal_line
    return pd.DataFrame({"macd": macd_line, "signal": signal_line, "histogram": histogram})


# ---------------- Momentum ----------------

def rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()

    rs = avg_gain / avg_loss.replace(0, np.nan)
    result = 100 - (100 / (1 + rs))
    return result.where(avg_loss != 0, 100.0)


def stochastic_oscillator(
    high: pd.Series, low: pd.Series, close: pd.Series, k_period: int = 14, d_period: int = 3
) -> pd.DataFrame:
    lowest_low = low.rolling(k_period, min_periods=k_period).min()
    highest_high = high.rolling(k_period, min_periods=k_period).max()
    percent_k = 100 * (close - lowest_low) / (highest_high - lowest_low)
    percent_d = percent_k.rolling(d_period, min_periods=d_period).mean()
    return pd.DataFrame({"%K": percent_k, "%D": percent_d})


def roc(series: pd.Series, period: int = 12) -> pd.Series:
    return (series / series.shift(period) - 1) * 100


# ---------------- Volatility ----------------

def bollinger_bands(series: pd.Series, period: int = 20, num_std: float = 2.0) -> pd.DataFrame:
    middle = sma(series, period)
    std = series.rolling(period, min_periods=period).std()
    upper = middle + num_std * std
    lower = middle - num_std * std
    return pd.DataFrame({"upper": upper, "middle": middle, "lower": lower})


def atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    prev_close = close.shift(1)
    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low - prev_close).abs(),
    ], axis=1).max(axis=1)
    return tr.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()


# ---------------- Volume ----------------

def obv(close: pd.Series, volume: pd.Series) -> pd.Series:
    direction = np.sign(close.diff().fillna(0))
    return (direction * volume).fillna(0).cumsum()


def volume_sma(volume: pd.Series, period: int = 20) -> pd.Series:
    return sma(volume, period)


INDICATOR_REGISTRY = {
    "sma": lambda df, period=20, **_: sma(df["close"], period),
    "ema": lambda df, period=20, **_: ema(df["close"], period),
    "wma": lambda df, period=20, **_: wma(df["close"], period),
    "macd": lambda df, fast=12, slow=26, signal=9, **_: macd(df["close"], fast, slow, signal),
    "rsi": lambda df, period=14, **_: rsi(df["close"], period),
    "stochastic": lambda df, k_period=14, d_period=3, **_: stochastic_oscillator(
        df["high"], df["low"], df["close"], k_period, d_period
    ),
    "roc": lambda df, period=12, **_: roc(df["close"], period),
    "bollinger": lambda df, period=20, num_std=2.0, **_: bollinger_bands(df["close"], period, num_std),
    "atr": lambda df, period=14, **_: atr(df["high"], df["low"], df["close"], period),
    "obv": lambda df, **_: obv(df["close"], df["volume"]),
    "volume_sma": lambda df, period=20, **_: volume_sma(df["volume"], period),
}


def calculate_indicator(df: pd.DataFrame, name: str, **params) -> pd.DataFrame:
    """Dispatches to the right indicator function and always returns a DataFrame
    indexed the same as `df`, with one or more named value columns."""
    name = name.lower()
    if name not in INDICATOR_REGISTRY:
        raise ValueError(f"Unknown indicator: {name}")

    result = INDICATOR_REGISTRY[name](df, **params)
    if isinstance(result, pd.Series):
        result = result.to_frame(name=name)
    return result
