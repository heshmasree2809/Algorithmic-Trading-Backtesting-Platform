"""
Backtest orchestration service: wires market data -> strategy -> engine ->
persistence. Kept separate from API routes per the clean-architecture
requirement in the spec.
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from app.backtesting.engine import run_backtest
from app.models.models import Backtest, BacktestStatus, BacktestTrade, PortfolioSnapshot
from app.services.market_data_service import get_market_data
from app.strategies.implementations import get_strategy


def execute_backtest(db: Session, backtest_id: str) -> None:
    """
    Runs a previously-created Backtest row synchronously and writes back
    status/metrics/trades/snapshots. In production this would be invoked by
    a background worker (see spec section 20); it is synchronous here for
    simplicity and because backtests over single-symbol daily data are fast.
    """
    bt = db.get(Backtest, backtest_id)
    if bt is None:
        return

    bt.status = BacktestStatus.RUNNING
    db.commit()

    try:
        df = get_market_data(db, bt.symbol, bt.start_date, bt.end_date)
        if df.empty:
            raise ValueError(f"No market data available for {bt.symbol} in the requested range.")

        strategy = get_strategy(bt.strategy_key, **(bt.params or {}))
        strategy.symbol = bt.symbol

        result = run_backtest(
            df=df,
            strategy=strategy,
            initial_capital=bt.initial_capital,
            transaction_cost_pct=bt.transaction_cost_pct,
            slippage_pct=bt.slippage_pct,
            position_sizing=bt.position_sizing,
        )

        for t in result.trades:
            db.add(BacktestTrade(
                backtest_id=bt.id, timestamp=t.timestamp, symbol=t.symbol, side=t.side,
                quantity=t.quantity, execution_price=t.execution_price, fees=t.fees,
                slippage_cost=t.slippage_cost, realized_pnl=t.realized_pnl,
            ))

        for s in result.snapshots:
            db.add(PortfolioSnapshot(
                backtest_id=bt.id, timestamp=s.timestamp, cash=s.cash,
                holdings_value=s.holdings_value, total_value=s.total_value,
                position_qty=s.position_qty,
            ))

        bt.metrics = result.metrics
        bt.status = BacktestStatus.COMPLETED
        bt.completed_at = datetime.utcnow()

    except Exception as exc:  # noqa: BLE001 - surfaced to the user via error_message
        bt.status = BacktestStatus.FAILED
        bt.error_message = str(exc)

    db.commit()
