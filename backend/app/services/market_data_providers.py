"""
Market data provider abstraction.

The rest of the application depends only on `MarketDataProvider`, never on a
concrete provider, so a new data source can be added without touching
calling code (Open/Closed Principle).
"""
from __future__ import annotations

import abc
import io
from datetime import datetime

import numpy as np
import pandas as pd

OHLCV_COLUMNS = ["timestamp", "open", "high", "low", "close", "adjusted_close", "volume"]


class MarketDataProvider(abc.ABC):
    """Abstract base class every market data source must implement."""

    @abc.abstractmethod
    def fetch(self, symbol: str, start: datetime, end: datetime) -> pd.DataFrame:
        """Return a DataFrame with OHLCV_COLUMNS, sorted ascending by timestamp."""
        raise NotImplementedError


class YahooFinanceProvider(MarketDataProvider):
    """Fetches historical OHLCV data from Yahoo Finance via yfinance."""

    def fetch(self, symbol: str, start: datetime, end: datetime) -> pd.DataFrame:
        import yfinance as yf

        df = yf.download(symbol, start=start, end=end, progress=False, auto_adjust=False)
        if df.empty:
            return pd.DataFrame(columns=OHLCV_COLUMNS)

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        df = df.reset_index().rename(columns={
            "Date": "timestamp", "Open": "open", "High": "high", "Low": "low",
            "Close": "close", "Adj Close": "adjusted_close", "Volume": "volume",
        })
        for col in OHLCV_COLUMNS:
            if col not in df.columns:
                df[col] = np.nan
        return df[OHLCV_COLUMNS]


class CSVProvider(MarketDataProvider):
    """Reads OHLCV data from a CSV file or in-memory buffer with standard columns."""

    def __init__(self, file_path_or_buffer):
        self.file_path_or_buffer = file_path_or_buffer

    def fetch(self, symbol: str, start: datetime, end: datetime) -> pd.DataFrame:
        df = pd.read_csv(self.file_path_or_buffer)
        df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
        rename_map = {"date": "timestamp", "adj_close": "adjusted_close"}
        df = df.rename(columns=rename_map)
        for col in OHLCV_COLUMNS:
            if col not in df.columns:
                df[col] = np.nan
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df = df[(df["timestamp"] >= start) & (df["timestamp"] <= end)]
        return df[OHLCV_COLUMNS]


class MockProvider(MarketDataProvider):
    """
    Deterministic synthetic OHLCV generator (seeded by symbol) used for local
    development, tests, and CI where no network access or API keys exist.
    """

    def fetch(self, symbol: str, start: datetime, end: datetime) -> pd.DataFrame:
        dates = pd.bdate_range(start=start, end=end)  # business days only
        if len(dates) == 0:
            return pd.DataFrame(columns=OHLCV_COLUMNS)

        seed = abs(hash(symbol)) % (2 ** 32)
        rng = np.random.default_rng(seed)

        n = len(dates)
        daily_returns = rng.normal(loc=0.0004, scale=0.012, size=n)
        close = 100 * np.cumprod(1 + daily_returns)

        high = close * (1 + np.abs(rng.normal(0.0, 0.004, size=n)))
        low = close * (1 - np.abs(rng.normal(0.0, 0.004, size=n)))
        open_ = low + (high - low) * rng.uniform(0.2, 0.8, size=n)
        volume = rng.integers(1_000_000, 8_000_000, size=n).astype(float)

        df = pd.DataFrame({
            "timestamp": dates,
            "open": open_,
            "high": high,
            "low": low,
            "close": close,
            "adjusted_close": close,
            "volume": volume,
        })
        return df[OHLCV_COLUMNS]


def get_provider(name: str, **kwargs) -> MarketDataProvider:
    """Factory returning the requested provider implementation."""
    name = (name or "mock").lower()
    if name == "yahoo":
        return YahooFinanceProvider()
    if name == "csv":
        return CSVProvider(kwargs["file_path_or_buffer"])
    if name == "mock":
        return MockProvider()
    raise ValueError(f"Unknown market data provider: {name}")
