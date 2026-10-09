"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-09-27

"""
from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=True),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"])

    op.create_table(
        "instruments",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("symbol", sa.String(32), nullable=False, unique=True),
        sa.Column("name", sa.String(255), nullable=True),
        sa.Column("asset_class", sa.String(32), default="equity"),
        sa.Column("currency", sa.String(8), default="USD"),
        sa.Column("exchange", sa.String(64), nullable=True),
    )
    op.create_index("ix_instruments_symbol", "instruments", ["symbol"])

    op.create_table(
        "market_data",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("symbol", sa.String(32), nullable=False),
        sa.Column("timestamp", sa.DateTime, nullable=False),
        sa.Column("open", sa.Float, nullable=False),
        sa.Column("high", sa.Float, nullable=False),
        sa.Column("low", sa.Float, nullable=False),
        sa.Column("close", sa.Float, nullable=False),
        sa.Column("adjusted_close", sa.Float, nullable=True),
        sa.Column("volume", sa.Float, nullable=True),
        sa.Column("source", sa.String(32), default="unknown"),
        sa.UniqueConstraint("symbol", "timestamp", name="uq_market_data_symbol_ts"),
    )
    op.create_index("ix_market_data_symbol_ts", "market_data", ["symbol", "timestamp"])

    op.create_table(
        "strategies",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("key", sa.String(64), nullable=False, unique=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("default_params", sa.JSON, default=dict),
    )

    backtest_status = sa.Enum("pending", "running", "completed", "failed", name="backteststatus")

    op.create_table(
        "backtests",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("strategy_key", sa.String(64), nullable=False),
        sa.Column("symbol", sa.String(32), nullable=False),
        sa.Column("start_date", sa.DateTime, nullable=False),
        sa.Column("end_date", sa.DateTime, nullable=False),
        sa.Column("initial_capital", sa.Float, nullable=False),
        sa.Column("transaction_cost_pct", sa.Float, nullable=False),
        sa.Column("slippage_pct", sa.Float, nullable=False),
        sa.Column("position_sizing", sa.String(32), default="full"),
        sa.Column("params", sa.JSON, default=dict),
        sa.Column("status", backtest_status, nullable=False, server_default="pending"),
        sa.Column("metrics", sa.JSON, nullable=True),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("completed_at", sa.DateTime, nullable=True),
    )
    op.create_index("ix_backtests_user_id", "backtests", ["user_id"])

    op.create_table(
        "backtest_trades",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("backtest_id", sa.String(36), sa.ForeignKey("backtests.id"), nullable=False),
        sa.Column("timestamp", sa.DateTime, nullable=False),
        sa.Column("symbol", sa.String(32), nullable=False),
        sa.Column("side", sa.String(8), nullable=False),
        sa.Column("quantity", sa.Float, nullable=False),
        sa.Column("execution_price", sa.Float, nullable=False),
        sa.Column("fees", sa.Float, default=0.0),
        sa.Column("slippage_cost", sa.Float, default=0.0),
        sa.Column("realized_pnl", sa.Float, default=0.0),
    )
    op.create_index("ix_trades_backtest_id", "backtest_trades", ["backtest_id"])

    op.create_table(
        "portfolio_snapshots",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("backtest_id", sa.String(36), sa.ForeignKey("backtests.id"), nullable=False),
        sa.Column("timestamp", sa.DateTime, nullable=False),
        sa.Column("cash", sa.Float, nullable=False),
        sa.Column("holdings_value", sa.Float, nullable=False),
        sa.Column("total_value", sa.Float, nullable=False),
        sa.Column("position_qty", sa.Float, default=0.0),
    )
    op.create_index("ix_snapshots_backtest_id_ts", "portfolio_snapshots", ["backtest_id", "timestamp"])

    op.create_table(
        "optimization_runs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("strategy_key", sa.String(64), nullable=False),
        sa.Column("symbol", sa.String(32), nullable=False),
        sa.Column("param_grid", sa.JSON, nullable=False),
        sa.Column("results", sa.JSON, nullable=True),
        sa.Column("status", backtest_status, nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime, nullable=False),
    )


def downgrade() -> None:
    op.drop_table("optimization_runs")
    op.drop_table("portfolio_snapshots")
    op.drop_table("backtest_trades")
    op.drop_table("backtests")
    op.execute("DROP TYPE IF EXISTS backteststatus")
    op.drop_table("strategies")
    op.drop_table("market_data")
    op.drop_table("instruments")
    op.drop_table("users")
