"""
Central application configuration, loaded from environment variables.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    PROJECT_NAME: str = "QuantX"
    API_V1_PREFIX: str = "/api"

    # Database
    DATABASE_URL: str = "postgresql+psycopg2://quantx:quantx@postgres:5432/quantx"

    # Redis
    REDIS_URL: str = "redis://redis:6379/0"
    MARKET_DATA_CACHE_TTL_SECONDS: int = 3600
    INDICATOR_CACHE_TTL_SECONDS: int = 1800

    # Auth
    SECRET_KEY: str = "CHANGE_ME_IN_PRODUCTION_9f8c7a6b5d4e3f2a1b0c"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24

    # Market data provider: "yahoo", "csv", or "mock"
    MARKET_DATA_PROVIDER: str = "mock"

    # Backtesting defaults
    DEFAULT_INITIAL_CAPITAL: float = 100_000.0
    DEFAULT_TRANSACTION_COST_PCT: float = 0.001   # 0.10%
    DEFAULT_SLIPPAGE_PCT: float = 0.0005          # 0.05%
    RISK_FREE_RATE_ANNUAL: float = 0.02

    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:3000"]


settings = Settings()
