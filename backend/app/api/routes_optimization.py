from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.backtesting.optimization import grid_search, walk_forward_analysis
from app.core.config import settings
from app.core.database import get_db
from app.models.models import User
from app.schemas.schemas import (
    OptimizationRequest, OptimizationResponse, OptimizationResultRow,
    WalkForwardRequest, WalkForwardResponse, WalkForwardWindowResult,
)
from app.services.market_data_service import get_market_data
from app.strategies.implementations import STRATEGY_REGISTRY

router = APIRouter(prefix="/api", tags=["optimization"])

MAX_PARAM_COMBINATIONS = 200


@router.post("/optimization", response_model=OptimizationResponse)
def run_optimization(
    payload: OptimizationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if payload.strategy_key not in STRATEGY_REGISTRY:
        raise HTTPException(status_code=422, detail=f"Unknown strategy '{payload.strategy_key}'.")

    combo_count = 1
    for values in payload.param_grid.values():
        combo_count *= max(1, len(values))
    if combo_count > MAX_PARAM_COMBINATIONS:
        raise HTTPException(
            status_code=422,
            detail=f"Parameter grid too large ({combo_count} combinations); "
                   f"max is {MAX_PARAM_COMBINATIONS}. This runs synchronously; "
                   f"for larger grids use a background-job architecture.",
        )

    df = get_market_data(db, payload.symbol.upper(), payload.start_date, payload.end_date)
    if df.empty:
        raise HTTPException(status_code=404, detail=f"No market data found for {payload.symbol}.")

    raw_results = grid_search(
        df=df, strategy_key=payload.strategy_key, param_grid=payload.param_grid,
        initial_capital=payload.initial_capital,
        transaction_cost_pct=payload.transaction_cost_pct,
        slippage_pct=payload.slippage_pct,
        out_of_sample_split=payload.out_of_sample_split or 0.0,
        risk_free_rate_annual=settings.RISK_FREE_RATE_ANNUAL,
    )

    return OptimizationResponse(
        symbol=payload.symbol.upper(),
        strategy_key=payload.strategy_key,
        results=[OptimizationResultRow(**r) for r in raw_results],
    )


@router.post("/walk-forward", response_model=WalkForwardResponse)
def run_walk_forward(
    payload: WalkForwardRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if payload.strategy_key not in STRATEGY_REGISTRY:
        raise HTTPException(status_code=422, detail=f"Unknown strategy '{payload.strategy_key}'.")

    df = get_market_data(db, payload.symbol.upper(), payload.start_date, payload.end_date)
    if df.empty:
        raise HTTPException(status_code=404, detail=f"No market data found for {payload.symbol}.")

    windows = walk_forward_analysis(
        df=df, strategy_key=payload.strategy_key, params=payload.params,
        train_years=payload.train_years, test_years=payload.test_years,
        initial_capital=payload.initial_capital,
        transaction_cost_pct=payload.transaction_cost_pct,
        slippage_pct=payload.slippage_pct,
        risk_free_rate_annual=settings.RISK_FREE_RATE_ANNUAL,
    )

    if not windows:
        raise HTTPException(
            status_code=422,
            detail="Date range too short for the requested train/test window sizes.",
        )

    return WalkForwardResponse(
        symbol=payload.symbol.upper(),
        strategy_key=payload.strategy_key,
        windows=[WalkForwardWindowResult(**w) for w in windows],
    )
