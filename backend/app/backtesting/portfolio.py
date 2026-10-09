"""
Portfolio Engine: tracks cash, position, realized/unrealized P&L, and emits
trade records and per-bar portfolio snapshots for a single-symbol backtest.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Trade:
    timestamp: datetime
    symbol: str
    side: str  # BUY / SELL
    quantity: float
    execution_price: float
    fees: float
    slippage_cost: float
    realized_pnl: float = 0.0


@dataclass
class Snapshot:
    timestamp: datetime
    cash: float
    holdings_value: float
    total_value: float
    position_qty: float


class Portfolio:
    """
    Single-symbol long-only portfolio (short-selling out of scope for v1,
    consistent with a research/education-focused platform).
    """

    def __init__(self, initial_capital: float, symbol: str,
                 transaction_cost_pct: float, slippage_pct: float):
        self.cash = initial_capital
        self.initial_capital = initial_capital
        self.symbol = symbol
        self.transaction_cost_pct = transaction_cost_pct
        self.slippage_pct = slippage_pct

        self.position_qty = 0.0
        self.avg_entry_price = 0.0
        self._entry_timestamp: datetime | None = None

        self.trades: list[Trade] = []
        self.snapshots: list[Snapshot] = []
        self.closed_trade_pnls: list[float] = []
        self.entry_exit_pairs: list[tuple] = []

    def _apply_slippage(self, price: float, side: str) -> float:
        # Buying executes slightly worse (higher); selling slightly worse (lower).
        if side == "BUY":
            return price * (1 + self.slippage_pct)
        return price * (1 - self.slippage_pct)

    def buy(self, timestamp: datetime, price: float, fraction_of_cash: float = 1.0) -> None:
        if self.position_qty > 0 or self.cash <= 0:
            return  # already long, or no cash

        exec_price = self._apply_slippage(price, "BUY")
        cash_to_use = self.cash * fraction_of_cash
        # size so that cash covers price + fees
        qty = cash_to_use / (exec_price * (1 + self.transaction_cost_pct))
        if qty <= 0:
            return

        fees = qty * exec_price * self.transaction_cost_pct
        slippage_cost = qty * abs(exec_price - price)
        total_cost = qty * exec_price + fees

        self.cash -= total_cost
        self.position_qty = qty
        self.avg_entry_price = exec_price
        self._entry_timestamp = timestamp

        self.trades.append(Trade(
            timestamp=timestamp, symbol=self.symbol, side="BUY", quantity=qty,
            execution_price=exec_price, fees=fees, slippage_cost=slippage_cost, realized_pnl=0.0,
        ))

    def sell(self, timestamp: datetime, price: float) -> None:
        if self.position_qty <= 0:
            return  # nothing to sell

        exec_price = self._apply_slippage(price, "SELL")
        qty = self.position_qty
        fees = qty * exec_price * self.transaction_cost_pct
        slippage_cost = qty * abs(price - exec_price)
        proceeds = qty * exec_price - fees

        realized_pnl = (exec_price - self.avg_entry_price) * qty - fees

        self.cash += proceeds
        self.closed_trade_pnls.append(realized_pnl)
        if self._entry_timestamp is not None:
            self.entry_exit_pairs.append((self._entry_timestamp, timestamp))

        self.trades.append(Trade(
            timestamp=timestamp, symbol=self.symbol, side="SELL", quantity=qty,
            execution_price=exec_price, fees=fees, slippage_cost=slippage_cost,
            realized_pnl=realized_pnl,
        ))

        self.position_qty = 0.0
        self.avg_entry_price = 0.0
        self._entry_timestamp = None

    def mark_to_market(self, timestamp: datetime, close_price: float) -> None:
        holdings_value = self.position_qty * close_price
        total_value = self.cash + holdings_value
        self.snapshots.append(Snapshot(
            timestamp=timestamp, cash=self.cash, holdings_value=holdings_value,
            total_value=total_value, position_qty=self.position_qty,
        ))

    @property
    def equity_curve(self) -> list[float]:
        return [s.total_value for s in self.snapshots]
