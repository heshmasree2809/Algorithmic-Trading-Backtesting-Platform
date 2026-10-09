"""
QuantX API entrypoint. Wires together the API Gateway layer with the
service layer (market data, indicators, strategies, backtesting, risk).

IMPORTANT: This platform is a historical-simulation research tool. It does
NOT execute real trades and does NOT provide personalized investment advice.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import (
    routes_auth, routes_market_data, routes_indicators,
    routes_strategies, routes_backtests, routes_optimization,
)
from app.core.cache import cache
from app.core.config import settings
from app.core.database import Base, engine

# Create tables if they don't exist yet (Alembic migrations are the source
# of truth for production; this is a convenience for local/dev/demo boot).
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description=(
        "QuantX is a research and simulation platform for backtesting trading "
        "strategies on historical data. It does not execute real trades and "
        "does not provide personalized investment advice. All results are "
        "historical simulations and do not guarantee future performance."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(routes_auth.router)
app.include_router(routes_market_data.router)
app.include_router(routes_indicators.router)
app.include_router(routes_strategies.router)
app.include_router(routes_backtests.router)
app.include_router(routes_optimization.router)


@app.get("/api/health")
def health_check():
    return {"status": "ok", "service": settings.PROJECT_NAME}


@app.get("/api/metrics/cache")
def cache_metrics():
    """Exposes Redis cache hit-rate stats referenced in the README."""
    return cache.stats()
