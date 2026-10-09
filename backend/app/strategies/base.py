"""
Strategy interface. Every strategy consumes a full OHLCV DataFrame and
returns a Series of signals aligned to the same index, using ONLY
information available up to and including that row's timestamp (no
look-ahead). The backtesting engine treats a signal at index i as the
decision made using data through the close of bar i, executed at the
next bar's open (see backtesting/engine.py).
"""
from __future__ import annotations

import abc

import pandas as pd

BUY = "BUY"
SELL = "SELL"
HOLD = "HOLD"


class Strategy(abc.ABC):
    key: str = "base"
    name: str = "Base Strategy"
    description: str = ""
    default_params: dict = {}

    def __init__(self, **params):
        self.params = {**self.default_params, **params}

    @abc.abstractmethod
    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        """Return a pandas Series of BUY/SELL/HOLD aligned to df.index."""
        raise NotImplementedError
