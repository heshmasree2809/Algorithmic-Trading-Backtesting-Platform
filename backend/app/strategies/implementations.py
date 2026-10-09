"""
Concrete trading strategies. Each implements Strategy.generate_signals and
is fully parameterized (no hard-coded windows/thresholds).
"""
from __future__ import annotations

import pandas as pd

from app.indicators.indicators import sma, rsi, bollinger_bands, macd
from app.strategies.base import Strategy, BUY, SELL, HOLD


class MovingAverageCrossoverStrategy(Strategy):
    key = "ma_crossover"
    name = "Moving Average Crossover"
    description = "BUY when the short SMA crosses above the long SMA; SELL on the reverse cross."
    default_params = {"short_window": 20, "long_window": 50}

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        short = sma(df["close"], self.params["short_window"])
        long = sma(df["close"], self.params["long_window"])

        signals = pd.Series(HOLD, index=df.index)
        cross_up = (short > long) & (short.shift(1) <= long.shift(1))
        cross_down = (short < long) & (short.shift(1) >= long.shift(1))

        signals[cross_up] = BUY
        signals[cross_down] = SELL
        return signals


class RSIReversalStrategy(Strategy):
    key = "rsi_reversal"
    name = "RSI Reversal"
    description = "BUY when RSI exits oversold territory; SELL when it exits overbought territory."
    default_params = {"period": 14, "oversold": 30, "overbought": 70}

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        r = rsi(df["close"], self.params["period"])
        oversold, overbought = self.params["oversold"], self.params["overbought"]

        signals = pd.Series(HOLD, index=df.index)
        buy_cross = (r > oversold) & (r.shift(1) <= oversold)
        sell_cross = (r < overbought) & (r.shift(1) >= overbought)

        signals[buy_cross] = BUY
        signals[sell_cross] = SELL
        return signals


class BollingerMeanReversionStrategy(Strategy):
    key = "bollinger_mean_reversion"
    name = "Bollinger Mean Reversion"
    description = "BUY when price closes below the lower band; SELL when it closes above the upper band."
    default_params = {"period": 20, "num_std": 2.0}

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        bands = bollinger_bands(df["close"], self.params["period"], self.params["num_std"])

        signals = pd.Series(HOLD, index=df.index)
        signals[df["close"] < bands["lower"]] = BUY
        signals[df["close"] > bands["upper"]] = SELL
        return signals


class MACDStrategy(Strategy):
    key = "macd"
    name = "MACD Strategy"
    description = "BUY when the MACD line crosses above the signal line; SELL on the reverse cross."
    default_params = {"fast": 12, "slow": 26, "signal": 9}

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        m = macd(df["close"], self.params["fast"], self.params["slow"], self.params["signal"])

        signals = pd.Series(HOLD, index=df.index)
        cross_up = (m["macd"] > m["signal"]) & (m["macd"].shift(1) <= m["signal"].shift(1))
        cross_down = (m["macd"] < m["signal"]) & (m["macd"].shift(1) >= m["signal"].shift(1))

        signals[cross_up] = BUY
        signals[cross_down] = SELL
        return signals


STRATEGY_REGISTRY: dict[str, type[Strategy]] = {
    cls.key: cls for cls in [
        MovingAverageCrossoverStrategy,
        RSIReversalStrategy,
        BollingerMeanReversionStrategy,
        MACDStrategy,
    ]
}


def get_strategy(key: str, **params) -> Strategy:
    if key not in STRATEGY_REGISTRY:
        raise ValueError(f"Unknown strategy: {key}")
    return STRATEGY_REGISTRY[key](**params)


def list_strategies() -> list[dict]:
    return [
        {
            "key": cls.key,
            "name": cls.name,
            "description": cls.description,
            "default_params": cls.default_params,
        }
        for cls in STRATEGY_REGISTRY.values()
    ]
