import pandas as pd
import pytest

from app.backtesting.portfolio import Portfolio


def test_buy_deducts_cash_including_fees():
    p = Portfolio(initial_capital=10_000, symbol="TEST", transaction_cost_pct=0.01, slippage_pct=0.0)
    p.buy(pd.Timestamp("2023-01-01"), price=100.0)
    assert p.position_qty > 0
    assert p.cash < 10_000
    # qty * price * (1 + fee) should approx equal initial capital
    assert p.position_qty * 100.0 * 1.01 == pytest.approx(10_000, rel=1e-6)


def test_slippage_increases_buy_execution_price():
    p = Portfolio(initial_capital=10_000, symbol="TEST", transaction_cost_pct=0.0, slippage_pct=0.05)
    p.buy(pd.Timestamp("2023-01-01"), price=100.0)
    trade = p.trades[0]
    assert trade.execution_price == pytest.approx(105.0)


def test_slippage_decreases_sell_execution_price():
    p = Portfolio(initial_capital=10_000, symbol="TEST", transaction_cost_pct=0.0, slippage_pct=0.05)
    p.buy(pd.Timestamp("2023-01-01"), price=100.0)
    p.sell(pd.Timestamp("2023-01-02"), price=110.0)
    sell_trade = p.trades[-1]
    assert sell_trade.execution_price == pytest.approx(110.0 * 0.95)


def test_realized_pnl_is_positive_on_profitable_round_trip():
    p = Portfolio(initial_capital=10_000, symbol="TEST", transaction_cost_pct=0.0, slippage_pct=0.0)
    p.buy(pd.Timestamp("2023-01-01"), price=100.0)
    p.sell(pd.Timestamp("2023-01-05"), price=120.0)
    assert p.closed_trade_pnls[-1] > 0


def test_realized_pnl_is_negative_on_losing_round_trip():
    p = Portfolio(initial_capital=10_000, symbol="TEST", transaction_cost_pct=0.0, slippage_pct=0.0)
    p.buy(pd.Timestamp("2023-01-01"), price=100.0)
    p.sell(pd.Timestamp("2023-01-05"), price=80.0)
    assert p.closed_trade_pnls[-1] < 0


def test_cannot_buy_while_already_long():
    p = Portfolio(initial_capital=10_000, symbol="TEST", transaction_cost_pct=0.0, slippage_pct=0.0)
    p.buy(pd.Timestamp("2023-01-01"), price=100.0)
    qty_after_first_buy = p.position_qty
    p.buy(pd.Timestamp("2023-01-02"), price=90.0)  # should be a no-op
    assert p.position_qty == qty_after_first_buy


def test_sell_with_no_position_is_a_no_op():
    p = Portfolio(initial_capital=10_000, symbol="TEST", transaction_cost_pct=0.0, slippage_pct=0.0)
    p.sell(pd.Timestamp("2023-01-01"), price=100.0)
    assert p.cash == 10_000
    assert len(p.trades) == 0


def test_mark_to_market_reflects_unrealized_gains():
    p = Portfolio(initial_capital=10_000, symbol="TEST", transaction_cost_pct=0.0, slippage_pct=0.0)
    p.buy(pd.Timestamp("2023-01-01"), price=100.0)
    p.mark_to_market(pd.Timestamp("2023-01-02"), close_price=150.0)
    snapshot = p.snapshots[-1]
    assert snapshot.total_value > 10_000  # price rose 50% while holding
