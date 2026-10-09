from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.cache import cache
from app.core.config import settings
from app.core.database import get_db
from app.indicators.indicators import calculate_indicator, INDICATOR_REGISTRY
from app.schemas.schemas import IndicatorPoint, IndicatorResponse
from app.services.market_data_service import get_market_data

router = APIRouter(prefix="/api/indicators", tags=["indicators"])


@router.get("/{indicator}", response_model=IndicatorResponse)
def get_indicator(
    indicator: str,
    symbol: str = Query(...),
    start_date: str = Query(...),
    end_date: str = Query(...),
    period: int = Query(14, ge=1),
    db: Session = Depends(get_db),
):
    if indicator.lower() not in INDICATOR_REGISTRY:
        raise HTTPException(status_code=404, detail=f"Unknown indicator '{indicator}'.")

    start, end = datetime.fromisoformat(start_date), datetime.fromisoformat(end_date)
    symbol = symbol.upper()

    cache_key = f"indicator:{indicator}:{symbol}:{start.date()}:{end.date()}:{period}"
    cached = cache.get_json(cache_key)
    if cached:
        return IndicatorResponse(**cached)

    df = get_market_data(db, symbol, start, end)
    if df.empty:
        raise HTTPException(status_code=404, detail=f"No market data found for {symbol}.")

    result_df = calculate_indicator(df.set_index("timestamp"), indicator.lower(), period=period)

    points = []
    for ts, row in result_df.iterrows():
        row_dict = row.to_dict()
        primary_col = result_df.columns[0]
        points.append(IndicatorPoint(
            timestamp=ts,
            value=None if pd_isna(row_dict[primary_col]) else float(row_dict[primary_col]),
            extra={k: (None if pd_isna(v) else float(v)) for k, v in row_dict.items()},
        ))

    response = IndicatorResponse(symbol=symbol, indicator=indicator.lower(), period=period, points=points)
    cache.set_json(cache_key, response.model_dump(), settings.INDICATOR_CACHE_TTL_SECONDS)
    return response


def pd_isna(value) -> bool:
    import pandas as pd
    return pd.isna(value)
