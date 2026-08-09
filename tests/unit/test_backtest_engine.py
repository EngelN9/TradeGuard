"""Unit tests for deterministic execution, look-ahead, and fail-closed gates."""

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from tests.backtest_factories import crypto_order, equity_order, fixed_environment, plan

from tradeguard.backtest.engine import BacktestRejectedError, DeterministicBacktester
from tradeguard.backtest.models import BacktestPlan, OrderStatus
from tradeguard.data.fixtures import build_fixture
from tradeguard.data.models import CorporateAction, CorporateActionType
from tradeguard.data.quality import ValidationEvidenceRejectedError
from tradeguard.domain.events import OrderType
from tradeguard.experiments.manifest import RunType


@pytest.mark.unit
def test_identical_inputs_produce_identical_result_checksum() -> None:
    package = build_fixture("normal")
    input_plan = plan(crypto_order())
    engine = DeterministicBacktester(
        completion_clock=lambda: datetime(2024, 1, 2, 1, 0, 1, tzinfo=UTC)
    )

    first = engine.run(package=package, plan=input_plan, environment=fixed_environment())
    second = engine.run(package=package, plan=input_plan, environment=fixed_environment())

    assert first == second
    assert len(first.result.result_checksum) == 64
    assert first.result.fills[0].price == Decimal("102.00")
    assert first.result.orders[0].status is OrderStatus.FILLED
    assert first.result.conservation.conserved is True
    assert "same-close fill rejected" in first.result.warnings[0]


@pytest.mark.unit
def test_participation_cap_creates_partial_fill() -> None:
    artifact = DeterministicBacktester().run(
        package=build_fixture("normal"),
        plan=plan(crypto_order(quantity="0.5000")),
        environment=fixed_environment(),
    )

    assert artifact.result.orders[0].status is OrderStatus.PARTIALLY_FILLED
    assert artifact.result.fills[0].quantity == Decimal("0.2500")
    assert artifact.result.orders[0].remaining_quantity == Decimal("0.2500")


@pytest.mark.unit
def test_participation_cap_is_shared_by_all_orders_on_the_same_bar() -> None:
    artifact = DeterministicBacktester().run(
        package=build_fixture("normal"),
        plan=plan(
            crypto_order(order_id="order-a", quantity="0.2500"),
            crypto_order(order_id="order-b", quantity="0.2500"),
        ),
        environment=fixed_environment(),
    )

    assert sum((fill.quantity for fill in artifact.result.fills), Decimal("0")) == Decimal("0.2500")


@pytest.mark.unit
def test_limit_order_requires_cross_and_never_gets_price_improvement() -> None:
    crossed = crypto_order(quantity="0.2000", order_type=OrderType.LIMIT, limit_price="99.50")
    missed = crypto_order(
        order_id="crypto-buy-2",
        quantity="0.2000",
        order_type=OrderType.LIMIT,
        limit_price="98.00",
    )
    artifact = DeterministicBacktester().run(
        package=build_fixture("normal"),
        plan=plan(crossed, missed),
        environment=fixed_environment(),
    )

    assert artifact.result.fills[0].price == Decimal("99.50")
    assert artifact.result.orders[0].status is OrderStatus.FILLED
    assert artifact.result.orders[1].status is OrderStatus.UNFILLED


@pytest.mark.unit
def test_same_close_only_order_is_never_filled() -> None:
    submitted = datetime(2024, 1, 2, 0, 5, tzinfo=UTC)
    artifact = DeterministicBacktester().run(
        package=build_fixture("normal"),
        plan=plan(crypto_order(submitted_at=submitted)),
        environment=fixed_environment(),
    )

    assert artifact.result.fills == ()
    assert artifact.result.orders[0].status is OrderStatus.UNFILLED
    assert "look_ahead_guard_same_bar" in artifact.result.orders[0].reasons


@pytest.mark.unit
def test_precision_minimum_and_cash_fail_closed() -> None:
    precision = DeterministicBacktester().run(
        package=build_fixture("normal"),
        plan=plan(crypto_order(quantity="0.10005")),
        environment=fixed_environment(),
    )
    minimum = DeterministicBacktester().run(
        package=build_fixture("normal"),
        plan=plan(crypto_order(quantity="0.0500")),
        environment=fixed_environment(),
    )
    cash = DeterministicBacktester().run(
        package=build_fixture("normal"),
        plan=plan(crypto_order(), initial_cash="10"),
        environment=fixed_environment(),
    )

    assert precision.result.orders[0].reasons[-1] == "order_precision_rejected"
    assert minimum.result.orders[0].reasons[-1] == "minimum_notional_rejected"
    assert "insufficient simulated cash" in cash.result.orders[0].reasons[-1]
    assert all(
        order.status is OrderStatus.REJECTED
        for order in (precision.result.orders[0], minimum.result.orders[0], cash.result.orders[0])
    )


@pytest.mark.unit
def test_stock_split_updates_quantity_before_next_mark() -> None:
    artifact = DeterministicBacktester().run(
        package=build_fixture("stock_split"),
        plan=plan(equity_order()),
        environment=fixed_environment(),
    )

    assert len(artifact.result.corporate_actions) == 1
    assert artifact.result.corporate_actions[0].quantity_after == Decimal("20")
    assert artifact.result.positions[-2].market_value == Decimal("1000")
    assert artifact.result.positions[-1].quantity == Decimal("20")
    assert artifact.result.positions[-1].mark_price == Decimal("50.00")
    assert artifact.result.conservation.conserved is True


@pytest.mark.unit
def test_corporate_action_after_last_bar_updates_final_pnl_and_conservation() -> None:
    package = build_fixture("stock_split")
    dividend = CorporateAction(
        source="synthetic",
        venue="SYNTH-XNYS",
        symbol="ACME",
        action_type=CorporateActionType.CASH_DIVIDEND,
        effective_at=datetime(2024, 1, 2, 14, 31, 30, tzinfo=UTC),
        known_at=datetime(2024, 1, 2, 14, 31, 30, tzinfo=UTC),
        action_version="synthetic-v1",
        cash_amount=Decimal("1"),
        currency="USD",
    )
    extended_range = package.manifest.date_range.model_copy(
        update={"end_utc": datetime(2024, 1, 2, 14, 32, tzinfo=UTC)}
    )
    package = package.model_copy(
        update={
            "manifest": package.manifest.model_copy(update={"date_range": extended_range}),
            "corporate_actions": (*package.corporate_actions, dividend),
        }
    )

    artifact = DeterministicBacktester().run(
        package=package,
        plan=plan(equity_order()),
        environment=fixed_environment(),
    )

    assert artifact.result.corporate_actions[-1].cash_delta == Decimal("20")
    assert artifact.result.ending_currency_balances["USD"] == artifact.result.pnl_series[-1].cash
    assert artifact.result.conservation.conserved is True


@pytest.mark.unit
def test_completion_time_is_captured_after_execution() -> None:
    started_at = datetime(2024, 1, 2, 1, 0, tzinfo=UTC)
    completed_at = datetime(2024, 1, 2, 1, 0, 1, tzinfo=UTC)
    environment = fixed_environment().model_copy(
        update={"started_at": started_at, "completed_at": None}
    )

    artifact = DeterministicBacktester(completion_clock=lambda: completed_at).run(
        package=build_fixture("normal"),
        plan=plan(crypto_order()),
        environment=environment,
    )

    assert artifact.manifest.started_at == started_at
    assert artifact.manifest.completed_at == completed_at


@pytest.mark.unit
def test_prefilled_completion_time_is_rejected() -> None:
    environment = fixed_environment().model_copy(
        update={"completed_at": datetime(2024, 1, 2, 1, 0, tzinfo=UTC)}
    )
    with pytest.raises(BacktestRejectedError, match="engine-owned"):
        DeterministicBacktester(
            completion_clock=lambda: datetime(2024, 1, 2, 1, 0, 1, tzinfo=UTC)
        ).run(
            package=build_fixture("normal"),
            plan=plan(crypto_order()),
            environment=environment,
        )


@pytest.mark.unit
def test_unsafe_quality_and_plan_mismatch_are_rejected() -> None:
    engine = DeterministicBacktester()
    with pytest.raises(ValidationEvidenceRejectedError):
        engine.run(
            package=build_fixture("crypto_maintenance"),
            plan=plan(crypto_order()),
            environment=fixed_environment(),
        )
    mismatched = plan(crypto_order()).model_copy(update={"base_currency": "EUR"})
    with pytest.raises(BacktestRejectedError, match="base currency"):
        engine.run(
            package=build_fixture("normal"),
            plan=mismatched,
            environment=fixed_environment(),
        )
    wrong_venue_order = crypto_order().model_copy(update={"venue": "UNKNOWN"})
    with pytest.raises(BacktestRejectedError, match="venue"):
        engine.run(
            package=build_fixture("normal"),
            plan=plan(wrong_venue_order),
            environment=fixed_environment(),
        )


@pytest.mark.unit
def test_replay_manifest_records_replay_type() -> None:
    replay_plan = BacktestPlan.model_validate(
        plan(crypto_order()).model_dump() | {"run_type": RunType.REPLAY}
    )
    artifact = DeterministicBacktester().run(
        package=build_fixture("normal"),
        plan=replay_plan,
        environment=fixed_environment(),
    )

    assert artifact.manifest.run_type is RunType.REPLAY
    assert artifact.result.run_type is RunType.REPLAY
