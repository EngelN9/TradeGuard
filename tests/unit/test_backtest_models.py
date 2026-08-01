"""Validation tests for Prompt 6 immutable contracts."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import UUID

import pytest
from pydantic import ValidationError
from tests.backtest_factories import crypto_order, fixed_environment, plan

from tradeguard.backtest.engine import DeterministicBacktester
from tradeguard.backtest.models import (
    BacktestArtifact,
    BacktestPlan,
    BacktestResult,
    ConservationReport,
    OrderLedgerEntry,
    OrderStatus,
    PlannedOrder,
    PnLLedgerEntry,
    RunEnvironment,
)
from tradeguard.data.fixtures import build_fixture
from tradeguard.domain.events import AssetClass, OrderType, Side
from tradeguard.experiments.manifest import RunType


@pytest.mark.unit
def test_order_rejects_time_reversal_and_invalid_limit_pair() -> None:
    valid = crypto_order()
    payload = valid.model_dump()
    payload["submitted_at_utc"] = valid.decision_event_time_utc - timedelta(seconds=1)
    with pytest.raises(ValidationError, match="must not precede"):
        PlannedOrder.model_validate(payload)
    payload = valid.model_dump()
    payload["limit_price"] = Decimal("100")
    with pytest.raises(ValidationError, match="limit_price"):
        PlannedOrder.model_validate(payload)
    payload = valid.model_dump()
    payload.update({"order_type": OrderType.LIMIT, "limit_price": None})
    with pytest.raises(ValidationError, match="limit_price"):
        PlannedOrder.model_validate(payload)


@pytest.mark.unit
def test_plan_environment_and_ledger_totals_are_strict() -> None:
    with pytest.raises(ValidationError, match="unique"):
        BacktestPlan(
            run_id=UUID("00000000-0000-4000-8000-000000000061"),
            run_type=RunType.BACKTEST,
            initial_cash=Decimal("100"),
            base_currency="USD",
            orders=(crypto_order(), crypto_order()),
        )
    environment = fixed_environment().model_dump()
    environment["completed_at"] = environment["started_at"] - timedelta(seconds=1)
    with pytest.raises(ValidationError, match="must not precede"):
        RunEnvironment.model_validate(environment)
    with pytest.raises(ValidationError, match="must equal requested"):
        OrderLedgerEntry(
            order_id="bad-total",
            status=OrderStatus.PARTIALLY_FILLED,
            requested_quantity=Decimal("1"),
            filled_quantity=Decimal("0.4"),
            remaining_quantity=Decimal("0.5"),
        )


@pytest.mark.unit
def test_pnl_conservation_and_checksums_reject_tampering() -> None:
    with pytest.raises(ValidationError, match="total_pnl"):
        PnLLedgerEntry(
            event_time_utc=datetime(2024, 1, 1, tzinfo=UTC),
            cash=Decimal("100"),
            market_value=Decimal("0"),
            realized_pnl=Decimal("1"),
            unrealized_pnl=Decimal("1"),
            total_pnl=Decimal("3"),
            total_equity=Decimal("100"),
        )
    with pytest.raises(ValidationError, match="conserved"):
        ConservationReport(
            cash_equity_difference=Decimal("1"),
            asset_quantity_differences={},
            duplicate_fill_ids_ignored=0,
            conserved=True,
        )
    artifact = DeterministicBacktester().run(
        package=build_fixture("normal"),
        plan=plan(crypto_order()),
        environment=fixed_environment(),
    )
    payload = artifact.result.model_dump()
    payload["warnings"] = ("tampered",)
    with pytest.raises(ValidationError, match="result_checksum"):
        BacktestResult.model_validate(payload)


@pytest.mark.unit
def test_artifact_must_bind_manifest_to_result() -> None:
    artifact = DeterministicBacktester().run(
        package=build_fixture("normal"),
        plan=plan(crypto_order()),
        environment=fixed_environment(),
    )
    result_payload = artifact.result.model_dump(exclude={"result_checksum"})
    result_payload["run_id"] = UUID("00000000-0000-4000-8000-000000000099")
    result = BacktestResult.build(**result_payload)
    with pytest.raises(ValidationError, match="run_id"):
        BacktestArtifact(manifest=artifact.manifest, result=result)
    manifest = artifact.manifest.model_copy(update={"result_checksum": "f" * 64})
    with pytest.raises(ValidationError, match="not bound"):
        BacktestArtifact(manifest=manifest, result=artifact.result)


@pytest.mark.unit
def test_float_and_unsupported_asset_input_are_rejected() -> None:
    payload = plan(crypto_order()).model_dump()
    payload["initial_cash"] = 1.5
    with pytest.raises(ValidationError, match="binary floats"):
        BacktestPlan.model_validate(payload)
    with pytest.raises(ValidationError):
        PlannedOrder(
            order_id="system-order",
            asset_class=AssetClass.SYSTEM,
            venue="system",
            symbol="system",
            side=Side.BUY,
            order_type=OrderType.MARKET,
            quantity=Decimal("1"),
            decision_event_time_utc=datetime(2024, 1, 1, tzinfo=UTC),
            submitted_at_utc=datetime(2024, 1, 1, tzinfo=UTC),
            sequence_number=0,
        )
