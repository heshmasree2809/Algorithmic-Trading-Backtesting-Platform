from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.models import Instrument
from app.schemas.schemas import (
    InstrumentOut, MarketDataImportRequest, MarketDataResponse, OHLCVBar,
)
from app.services.market_data_service import get_market_data, import_market_data

router = APIRouter(prefix="/api", tags=["market-data"])


@router.post("/market-data/import")
def import_data(payload: MarketDataImportRequest, db: Session = Depends(get_db)):
    rows_written = import_market_data(
        db, payload.symbol.upper(), payload.start_date, payload.end_date, payload.provider,
    )
    return {"symbol": payload.symbol.upper(), "rows_imported": rows_written}


@router.get("/market-data/{symbol}", response_model=MarketDataResponse)
def read_market_data(
    symbol: str,
    start_date: str = Query(...),
    end_date: str = Query(...),
    db: Session = Depends(get_db),
):
    from datetime import datetime
    try:
        start = datetime.fromisoformat(start_date)
        end = datetime.fromisoformat(end_date)
    except ValueError:
        raise HTTPException(status_code=422, detail="Dates must be ISO format (YYYY-MM-DD).")

    df = get_market_data(db, symbol.upper(), start, end)
    if df.empty:
        raise HTTPException(status_code=404, detail=f"No market data found for {symbol}.")

    bars = [
        OHLCVBar(
            timestamp=row["timestamp"], open=row["open"], high=row["high"], low=row["low"],
            close=row["close"], adjusted_close=row.get("adjusted_close"), volume=row.get("volume"),
        )
        for _, row in df.iterrows()
    ]
    return MarketDataResponse(symbol=symbol.upper(), bars=bars, count=len(bars))


@router.get("/instruments", response_model=list[InstrumentOut])
def list_instruments(db: Session = Depends(get_db)):
    instruments = db.query(Instrument).all()
    if not instruments:
        # Seed a small default watchlist so the Market Explorer isn't empty on first run.
        defaults = [
            ("AAPL", "Apple Inc.", "equity"), ("MSFT", "Microsoft Corp.", "equity"),
            ("SPY", "S&P 500 ETF", "etf"), ("QQQ", "Nasdaq 100 ETF", "etf"),
            ("BTC-USD", "Bitcoin", "crypto"),
        ]
        for symbol, name, asset_class in defaults:
            db.add(Instrument(symbol=symbol, name=name, asset_class=asset_class))
        db.commit()
        instruments = db.query(Instrument).all()
    return instruments
