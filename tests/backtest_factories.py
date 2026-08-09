"""Fixed Prompt 6 inputs shared by backtest tests."""

from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from tradeguard.backtest.models import BacktestPlan, PlannedOrder, RunEnvironment
from tradeguard.domain.events import AssetClass, OrderType, Side
from tradeguard.experiments.manifest import RunType


def fixed_environment() -> RunEnvironment:
    timestamp = datetime(2024, 1, 2, 1, 0, tzinfo=UTC)
    return RunEnvironment(
        git_sha="1" * 40,
        dirty_worktree=False,
        python_version="3.12.0",
        platform="test-platform",
        dependency_lock_hash="2" * 64,
        started_at=timestamp,
    )


def crypto_order(  # noqa: PLR0913 - explicit fixture overrides keep tests readable
    *,
    order_id: str = "crypto-buy-1",
    quantity: str = "0.1000",
    submitted_at: datetime | None = None,
    side: Side = Side.BUY,
    order_type: OrderType = OrderType.MARKET,
    limit_price: str | None = None,
) -> PlannedOrder:
    submitted = submitted_at or datetime(2024, 1, 2, 0, 4, tzinfo=UTC)
    return PlannedOrder(
        order_id=order_id,
        asset_class=AssetClass.CRYPTO,
        venue="SYNTH-CRYPTO",
        symbol="BTC-USD",
        side=side,
        order_type=order_type,
        quantity=Decimal(quantity),
        limit_price=Decimal(limit_price) if limit_price is not None else None,
        decision_event_time_utc=submitted,
        submitted_at_utc=submitted,
        sequence_number=1,
    )


def equity_order(*, quantity: str = "10") -> PlannedOrder:
    submitted = datetime(2024, 1, 1, 20, 57, tzinfo=UTC)
    return PlannedOrder(
        order_id="equity-buy-1",
        asset_class=AssetClass.EQUITY,
        venue="SYNTH-XNYS",
        symbol="ACME",
        side=Side.BUY,
        order_type=OrderType.MARKET,
        quantity=Decimal(quantity),
        decision_event_time_utc=submitted,
        submitted_at_utc=submitted,
        sequence_number=1,
    )


def plan(
    *orders: PlannedOrder,
    run_type: RunType = RunType.BACKTEST,
    initial_cash: str = "100000",
) -> BacktestPlan:
    return BacktestPlan(
        run_id=UUID("00000000-0000-4000-8000-000000000060"),
        run_type=run_type,
        initial_cash=Decimal(initial_cash),
        base_currency="USD",
        orders=orders,
    )
