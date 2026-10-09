from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.models import Backtest, BacktestStatus, BacktestTrade, PortfolioSnapshot, User
from app.schemas.schemas import (
    BacktestCreateRequest, BacktestDetail, BacktestOut, EquityPoint, TradeOut,
)
from app.services.backtest_service import execute_backtest
from app.strategies.implementations import STRATEGY_REGISTRY

router = APIRouter(prefix="/api/backtests", tags=["backtests"])


@router.post("", response_model=BacktestOut, status_code=201)
def create_backtest(
    payload: BacktestCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if payload.strategy_key not in STRATEGY_REGISTRY:
        raise HTTPException(status_code=422, detail=f"Unknown strategy '{payload.strategy_key}'.")
    if payload.end_date <= payload.start_date:
        raise HTTPException(status_code=422, detail="end_date must be after start_date.")

    bt = Backtest(
        user_id=current_user.id,
        strategy_key=payload.strategy_key,
        symbol=payload.symbol.upper(),
        start_date=payload.start_date,
        end_date=payload.end_date,
        initial_capital=payload.initial_capital,
        transaction_cost_pct=payload.transaction_cost_pct,
        slippage_pct=payload.slippage_pct,
        position_sizing=payload.position_sizing,
        params={**payload.params, "fixed_fraction": payload.fixed_fraction},
        status=BacktestStatus.PENDING,
    )
    db.add(bt)
    db.commit()
    db.refresh(bt)

    # Executed synchronously here; see README "Future Improvements" for the
    # Celery/RQ background-worker upgrade path noted in spec section 20.
    execute_backtest(db, bt.id)
    db.refresh(bt)
    return bt


def _get_owned_backtest(db: Session, backtest_id: str, user: User) -> Backtest:
    bt = db.get(Backtest, backtest_id)
    if bt is None or bt.user_id != user.id:
        raise HTTPException(status_code=404, detail="Backtest not found.")
    return bt


@router.get("", response_model=list[BacktestOut])
def list_backtests(
    skip: int = 0, limit: int = 50,
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user),
):
    return (
        db.query(Backtest)
        .filter(Backtest.user_id == current_user.id)
        .order_by(Backtest.created_at.desc())
        .offset(skip).limit(min(limit, 200))
        .all()
    )


@router.get("/{backtest_id}", response_model=BacktestDetail)
def get_backtest(
    backtest_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user),
):
    bt = _get_owned_backtest(db, backtest_id, current_user)
    trades = db.query(BacktestTrade).filter(BacktestTrade.backtest_id == bt.id).all()
    snapshots = (
        db.query(PortfolioSnapshot)
        .filter(PortfolioSnapshot.backtest_id == bt.id)
        .order_by(PortfolioSnapshot.timestamp.asc())
        .all()
    )
    return BacktestDetail(
        **BacktestOut.model_validate(bt).model_dump(),
        trades=[TradeOut.model_validate(t) for t in trades],
        equity_curve=[
            EquityPoint(
                timestamp=s.timestamp, cash=s.cash, holdings_value=s.holdings_value,
                total_value=s.total_value, position_qty=s.position_qty,
            ) for s in snapshots
        ],
    )


@router.get("/{backtest_id}/trades", response_model=list[TradeOut])
def get_backtest_trades(
    backtest_id: str, skip: int = 0, limit: int = 500,
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user),
):
    bt = _get_owned_backtest(db, backtest_id, current_user)
    trades = (
        db.query(BacktestTrade)
        .filter(BacktestTrade.backtest_id == bt.id)
        .order_by(BacktestTrade.timestamp.asc())
        .offset(skip).limit(min(limit, 2000))
        .all()
    )
    return trades


@router.get("/{backtest_id}/metrics")
def get_backtest_metrics(
    backtest_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user),
):
    bt = _get_owned_backtest(db, backtest_id, current_user)
    if bt.status != BacktestStatus.COMPLETED:
        raise HTTPException(status_code=409, detail=f"Backtest status is '{bt.status.value}'.")
    return bt.metrics


@router.get("/{backtest_id}/equity-curve", response_model=list[EquityPoint])
def get_equity_curve(
    backtest_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user),
):
    bt = _get_owned_backtest(db, backtest_id, current_user)
    snapshots = (
        db.query(PortfolioSnapshot)
        .filter(PortfolioSnapshot.backtest_id == bt.id)
        .order_by(PortfolioSnapshot.timestamp.asc())
        .all()
    )
    return [
        EquityPoint(
            timestamp=s.timestamp, cash=s.cash, holdings_value=s.holdings_value,
            total_value=s.total_value, position_qty=s.position_qty,
        ) for s in snapshots
    ]
