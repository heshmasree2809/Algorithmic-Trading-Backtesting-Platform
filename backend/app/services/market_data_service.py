"""
Market Data Service: cleans, validates, deduplicates, and persists OHLCV
data fetched from a MarketDataProvider, with Redis caching of read paths.
"""
from __future__ import annotations

from datetime import datetime

import pandas as pd
from sqlalchemy import select, delete
from sqlalchemy.orm import Session

from app.core.cache import cache
from app.core.config import settings
from app.models.models import MarketData
from app.services.market_data_providers import get_provider, OHLCV_COLUMNS


class DataQualityError(Exception):
    pass


def clean_ohlcv(df: pd.DataFrame) -> pd.DataFrame:
    """
    Applies the data-quality safeguards required by the spec:
    - date normalization
    - chronological sorting
    - duplicate detection/removal
    - invalid-record rejection (non-positive prices, high < low, NaNs in OHLC)
    - forward-fill of isolated missing values (never look-ahead / backward-fill)
    """
    if df.empty:
        return df

    df = df.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"]).dt.tz_localize(None)

    # Drop exact duplicate timestamps, keep first occurrence
    df = df.drop_duplicates(subset=["timestamp"], keep="first")

    # Reject rows with invalid price relationships or non-positive prices
    valid_mask = (
        (df["open"] > 0) & (df["high"] > 0) & (df["low"] > 0) & (df["close"] > 0)
        & (df["high"] >= df["low"])
        & (df["high"] >= df["open"]) & (df["high"] >= df["close"])
        & (df["low"] <= df["open"]) & (df["low"] <= df["close"])
    )
    df = df[valid_mask]

    df = df.sort_values("timestamp").reset_index(drop=True)

    # Missing-value handling: forward-fill only (no future information used)
    price_cols = ["open", "high", "low", "close", "adjusted_close"]
    df[price_cols] = df[price_cols].ffill()
    df["volume"] = df["volume"].fillna(0)

    df = df.dropna(subset=["open", "high", "low", "close"])
    return df[OHLCV_COLUMNS]


def import_market_data(
    db: Session, symbol: str, start: datetime, end: datetime, provider_name: str | None = None
) -> int:
    """Fetches, cleans, and upserts OHLCV rows for a symbol. Returns rows written."""
    provider = get_provider(provider_name or settings.MARKET_DATA_PROVIDER)
    raw = provider.fetch(symbol, start, end)
    clean = clean_ohlcv(raw)

    if clean.empty:
        return 0

    existing_ts = set(
        db.execute(
            select(MarketData.timestamp).where(MarketData.symbol == symbol)
        ).scalars().all()
    )

    rows_to_add = []
    for _, row in clean.iterrows():
        ts = row["timestamp"].to_pydatetime()
        if ts in existing_ts:
            continue  # duplicate detection against persisted data
        rows_to_add.append(MarketData(
            symbol=symbol,
            timestamp=ts,
            open=float(row["open"]),
            high=float(row["high"]),
            low=float(row["low"]),
            close=float(row["close"]),
            adjusted_close=float(row["adjusted_close"]) if pd.notna(row["adjusted_close"]) else float(row["close"]),
            volume=float(row["volume"]) if pd.notna(row["volume"]) else 0.0,
            source=provider_name or settings.MARKET_DATA_PROVIDER,
        ))

    db.bulk_save_objects(rows_to_add)
    db.commit()

    cache_key = f"market_data:{symbol}"
    cache._memory_fallback.pop(cache_key, None)  # best-effort local invalidation

    return len(rows_to_add)


def get_market_data(
    db: Session, symbol: str, start: datetime, end: datetime
) -> pd.DataFrame:
    """
    Returns cleaned OHLCV data for [start, end], reading through Redis cache.
    If nothing is persisted yet, transparently imports from the configured
    provider first (useful for the mock/demo provider in local dev).
    """
    cache_key = f"market_data:{symbol}:{start.date()}:{end.date()}"
    cached = cache.get_json(cache_key)
    if cached is not None:
        return pd.DataFrame(cached)

    stmt = (
        select(MarketData)
        .where(MarketData.symbol == symbol)
        .where(MarketData.timestamp >= start)
        .where(MarketData.timestamp <= end)
        .order_by(MarketData.timestamp.asc())
    )
    rows = db.execute(stmt).scalars().all()

    if not rows:
        import_market_data(db, symbol, start, end)
        rows = db.execute(stmt).scalars().all()

    df = pd.DataFrame([{
        "timestamp": r.timestamp, "open": r.open, "high": r.high, "low": r.low,
        "close": r.close, "adjusted_close": r.adjusted_close, "volume": r.volume,
    } for r in rows])

    if not df.empty:
        cache.set_json(cache_key, df.to_dict(orient="records"), settings.MARKET_DATA_CACHE_TTL_SECONDS)

    return df
