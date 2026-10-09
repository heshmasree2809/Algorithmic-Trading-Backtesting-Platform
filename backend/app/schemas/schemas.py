"""
Pydantic schemas used for request validation and response serialization.
"""
from datetime import datetime
from typing import Optional, Any

from pydantic import BaseModel, EmailStr, Field, ConfigDict


# ---------- Auth ----------

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: Optional[str] = None


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    email: EmailStr
    full_name: Optional[str] = None
    is_active: bool


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ---------- Market Data ----------

class OHLCVBar(BaseModel):
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    adjusted_close: Optional[float] = None
    volume: Optional[float] = None


class MarketDataImportRequest(BaseModel):
    symbol: str
    start_date: datetime
    end_date: datetime
    provider: Optional[str] = None  # "yahoo" | "csv" | "mock"


class MarketDataResponse(BaseModel):
    symbol: str
    bars: list[OHLCVBar]
    count: int


class InstrumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    symbol: str
    name: Optional[str] = None
    asset_class: str
    currency: str
    exchange: Optional[str] = None


# ---------- Indicators ----------

class IndicatorRequest(BaseModel):
    symbol: str
    start_date: datetime
    end_date: datetime
    period: int = 14
    extra_params: dict[str, Any] = Field(default_factory=dict)


class IndicatorPoint(BaseModel):
    timestamp: datetime
    value: Optional[float] = None
    extra: dict[str, Optional[float]] = Field(default_factory=dict)


class IndicatorResponse(BaseModel):
    symbol: str
    indicator: str
    period: int
    points: list[IndicatorPoint]


# ---------- Strategies ----------

class StrategyOut(BaseModel):
    key: str
    name: str
    description: str
    default_params: dict[str, Any]


# ---------- Backtests ----------

class BacktestCreateRequest(BaseModel):
    symbol: str
    strategy_key: str
    start_date: datetime
    end_date: datetime
    initial_capital: float = Field(default=100_000.0, gt=0)
    transaction_cost_pct: float = Field(default=0.001, ge=0)
    slippage_pct: float = Field(default=0.0005, ge=0)
    position_sizing: str = Field(default="full")  # full | fixed_fraction
    fixed_fraction: float = Field(default=1.0, gt=0, le=1)
    params: dict[str, Any] = Field(default_factory=dict)


class TradeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    timestamp: datetime
    symbol: str
    side: str
    quantity: float
    execution_price: float
    fees: float
    slippage_cost: float
    realized_pnl: float


class EquityPoint(BaseModel):
    timestamp: datetime
    cash: float
    holdings_value: float
    total_value: float
    position_qty: float


class PerformanceMetrics(BaseModel):
    total_return_pct: float
    cagr_pct: float
    annualized_volatility_pct: float
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown_pct: float
    calmar_ratio: float
    win_rate_pct: float
    profit_factor: float
    average_win: float
    average_loss: float
    number_of_trades: int
    average_holding_period_days: float


class BacktestOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    symbol: str
    strategy_key: str
    start_date: datetime
    end_date: datetime
    initial_capital: float
    status: str
    metrics: Optional[dict] = None
    created_at: datetime


class BacktestDetail(BacktestOut):
    trades: list[TradeOut] = Field(default_factory=list)
    equity_curve: list[EquityPoint] = Field(default_factory=list)


# ---------- Optimization / Walk-forward ----------

class OptimizationRequest(BaseModel):
    symbol: str
    strategy_key: str
    start_date: datetime
    end_date: datetime
    param_grid: dict[str, list[Any]]
    initial_capital: float = 100_000.0
    transaction_cost_pct: float = 0.001
    slippage_pct: float = 0.0005
    out_of_sample_split: Optional[float] = Field(
        default=0.3, ge=0, le=0.9,
        description="Fraction of the date range held out as out-of-sample for validation."
    )


class OptimizationResultRow(BaseModel):
    params: dict[str, Any]
    in_sample_metrics: PerformanceMetrics
    out_of_sample_metrics: Optional[PerformanceMetrics] = None


class OptimizationResponse(BaseModel):
    symbol: str
    strategy_key: str
    results: list[OptimizationResultRow]


class WalkForwardRequest(BaseModel):
    symbol: str
    strategy_key: str
    start_date: datetime
    end_date: datetime
    train_years: int = 3
    test_years: int = 1
    params: dict[str, Any] = Field(default_factory=dict)
    initial_capital: float = 100_000.0
    transaction_cost_pct: float = 0.001
    slippage_pct: float = 0.0005


class WalkForwardWindowResult(BaseModel):
    train_start: datetime
    train_end: datetime
    test_start: datetime
    test_end: datetime
    out_of_sample_metrics: PerformanceMetrics


class WalkForwardResponse(BaseModel):
    symbol: str
    strategy_key: str
    windows: list[WalkForwardWindowResult]
    disclaimer: str = (
        "Walk-forward and backtest results are historical simulations only. "
        "Past performance does not guarantee future results."
    )
