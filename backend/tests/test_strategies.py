import pandas as pd

from app.strategies.base import BUY, SELL, HOLD
from app.strategies.implementations import (
    MovingAverageCrossoverStrategy, RSIReversalStrategy,
    BollingerMeanReversionStrategy, MACDStrategy, get_strategy, list_strategies,
)


def test_ma_crossover_generates_buy_signal_on_golden_cross():
    # Flat then rising prices force a clean short-SMA-over-long-SMA cross.
    prices = [100] * 60 + list(range(100, 140))
    df = pd.DataFrame({"close": prices})
    strategy = MovingAverageCrossoverStrategy(short_window=5, long_window=20)
    signals = strategy.generate_signals(df)
    assert BUY in signals.values


def test_ma_crossover_respects_custom_params():
    df = pd.DataFrame({"close": [100] * 100})
    strategy = MovingAverageCrossoverStrategy(short_window=3, long_window=10)
    assert strategy.params["short_window"] == 3
    assert strategy.params["long_window"] == 10
    # Flat prices never cross -> everything HOLD
    signals = strategy.generate_signals(df)
    assert set(signals.unique()) <= {HOLD}


def test_rsi_reversal_buy_on_exit_from_oversold():
    # Construct a sharp drop then recovery to force RSI below 30 then back above.
    prices = [100] * 20 + list(range(100, 60, -2)) + list(range(60, 100, 2))
    df = pd.DataFrame({"close": prices})
    strategy = RSIReversalStrategy(period=14, oversold=30, overbought=70)
    signals = strategy.generate_signals(df)
    assert BUY in signals.values


def test_bollinger_mean_reversion_buy_below_lower_band():
    prices = [100] * 25 + [80]  # sharp one-bar drop far below the bands
    df = pd.DataFrame({"close": prices})
    strategy = BollingerMeanReversionStrategy(period=20, num_std=2.0)
    signals = strategy.generate_signals(df)
    assert signals.iloc[-1] == BUY


def test_macd_strategy_produces_signals_on_trend_change():
    prices = [100 - i * 0.5 for i in range(40)] + [80 + i for i in range(40)]
    df = pd.DataFrame({"close": prices})
    strategy = MACDStrategy()
    signals = strategy.generate_signals(df)
    assert BUY in signals.values


def test_get_strategy_factory_returns_correct_type():
    strategy = get_strategy("ma_crossover", short_window=10, long_window=30)
    assert isinstance(strategy, MovingAverageCrossoverStrategy)
    assert strategy.params["short_window"] == 10


def test_list_strategies_returns_all_registered():
    strategies = list_strategies()
    keys = {s["key"] for s in strategies}
    assert {"ma_crossover", "rsi_reversal", "bollinger_mean_reversion", "macd"} <= keys
