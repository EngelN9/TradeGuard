"""Unit tests for the bounded trusted-local strategy contract."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from uuid import UUID

import pytest
from tests.strategy_factories import (
    NORMAL_FIXTURE,
    strategy_artifact,
    strategy_environment,
    strategy_request,
)

from tradeguard.backtest.engine import DeterministicBacktester
from tradeguard.data.fixtures import build_fixture
from tradeguard.data.package import load_dataset_package
from tradeguard.domain.events import AssetClass, Signal
from tradeguard.strategies.buy_and_hold import (
    EXPECTED_FIXTURE_SHA256,
    BuyAndHoldBtcUsd,
    buy_and_hold_specification,
)
from tradeguard.strategies.models import (
    BuyAndHoldParameters,
    StrategyBar,
    StrategyContext,
    strategy_version_hash,
)
from tradeguard.strategies.runner import (
    StrategyRejectedError,
    StrategyRejectionCode,
    StrategyRunner,
)


def test_strategy_version_hash_is_canonical_and_semantic() -> None:
    first = BuyAndHoldParameters.model_validate({"quantity": "0.1000"})
    second = BuyAndHoldParameters.model_validate_json('{"quantity":"0.1000"}')
    specification = buy_and_hold_specification()

    assert strategy_version_hash(specification, first) == strategy_version_hash(
        specification, second
    )
    changed = specification.model_copy(update={"strategy_version": "1.0.1"})
    assert strategy_version_hash(changed, first) != strategy_version_hash(specification, first)
    changed_parameters = first.model_copy(update={"quantity": Decimal("0.2000")})
    assert strategy_version_hash(specification, changed_parameters) != strategy_version_hash(
        specification, first
    )


def test_strategy_receives_only_the_declared_bar_projection() -> None:
    assert set(StrategyBar.model_fields) == {
        "asset_class",
        "venue",
        "symbol",
        "event_time_utc",
        "sequence_number",
        "close_price",
    }
    assert not {
        "credentials",
        "provider",
        "network",
        "risk_config",
        "broker",
        "orders",
        "volume",
    } & set(StrategyBar.model_fields)
    assert not {"credentials", "provider", "risk_config", "broker"} & set(
        StrategyContext.model_fields
    )


def test_builtin_strategy_has_no_dynamic_loader_or_external_client_imports() -> None:
    root = Path(__file__).resolve().parents[2] / "src" / "tradeguard" / "strategies"
    public_sources = "\n".join(
        (root / name).read_text(encoding="utf-8")
        for name in ("buy_and_hold.py", "protocol.py", "cli.py")
    )
    for forbidden in (
        "importlib",
        "entry_points",
        "httpx",
        "requests",
        "tradeguard.adapters",
        "SecretStr",
    ):
        assert forbidden not in public_sources


def test_buy_and_hold_emits_once_and_holds() -> None:
    artifact = strategy_artifact()

    assert [type(output).__name__ for output in artifact.outputs] == [
        "Signal",
        "TargetPosition",
        "TradeProposal",
    ]
    assert artifact.plan.orders[0].submitted_at_utc == artifact.outputs[-1].event_time_utc
    assert artifact.backtest.result.fills[0].event_time_utc > artifact.outputs[-1].event_time_utc
    assert artifact.report.holding_at_end is True
    assert artifact.report.investment_advice is False
    assert artifact.report.profitability_claim is False


def test_buy_and_hold_lifecycle_and_market_guard_fail_closed() -> None:
    parameters = BuyAndHoldParameters()
    strategy = BuyAndHoldBtcUsd(parameters)
    bar = StrategyBar(
        asset_class=AssetClass.CRYPTO,
        venue="SYNTH-CRYPTO",
        symbol="BTC-USD",
        event_time_utc=datetime(2024, 1, 2, 0, 4, tzinfo=UTC),
        sequence_number=4,
        close_price=Decimal("40100"),
    )

    with pytest.raises(RuntimeError, match="initialized before receiving"):
        strategy.on_event(bar)
    with pytest.raises(RuntimeError, match="initialized before finalization"):
        strategy.finalize()

    specification = buy_and_hold_specification()
    context = StrategyContext(
        run_id=UUID("00000000-0000-4000-8000-000000000070"),
        correlation_id=UUID("00000000-0000-4000-8000-000000000071"),
        asset_class=AssetClass.CRYPTO,
        venue="SYNTH-CRYPTO",
        symbol="BTC-USD",
        dataset_id="synthetic-normal",
        dataset_version="1.0.0",
        manifest_checksum=("559e0e669ff3ab7d6bf37aaa192c8cba69c253361e2b640209320f5ffb0da750"),
        strategy_version_hash=strategy_version_hash(specification, parameters),
    )
    strategy.initialize(context)
    with pytest.raises(RuntimeError, match="initialized twice"):
        strategy.initialize(context)
    with pytest.raises(ValueError, match="event market differs"):
        strategy.on_event(bar.model_copy(update={"symbol": "ETH-USD"}))


def test_unsupported_market_and_non_pass_data_fail_closed() -> None:
    runner = StrategyRunner()
    with pytest.raises(StrategyRejectedError) as unsupported:
        runner.run(
            package=build_fixture("stock_split"),
            fixture_file_sha256=EXPECTED_FIXTURE_SHA256,
            request=strategy_request(),
            environment=strategy_environment(),
        )
    assert unsupported.value.code is StrategyRejectionCode.UNSUPPORTED_MARKET

    normal = load_dataset_package(NORMAL_FIXTURE)
    duplicated_records = normal.model_copy(
        update={
            "records": (normal.records[-1], normal.records[-1]),
            "expected_quality_status": None,
        }
    )
    with pytest.raises(StrategyRejectedError) as quality:
        runner.run(
            package=duplicated_records,
            fixture_file_sha256=EXPECTED_FIXTURE_SHA256,
            request=strategy_request(),
            environment=strategy_environment(),
        )
    assert quality.value.code is StrategyRejectionCode.DATA_QUALITY

    normal = load_dataset_package(NORMAL_FIXTURE)
    wrong_metadata = normal.instrument_metadata[0].model_copy(update={"venue": "OTHER"})
    with pytest.raises(StrategyRejectedError) as wrong_venue:
        runner.run(
            package=normal.model_copy(update={"instrument_metadata": (wrong_metadata,)}),
            fixture_file_sha256=EXPECTED_FIXTURE_SHA256,
            request=strategy_request(),
            environment=strategy_environment(),
        )
    assert wrong_venue.value.code is StrategyRejectionCode.UNSUPPORTED_MARKET


def test_undeclared_data_requirement_fails_before_strategy_initialization() -> None:
    class UndeclaredDataStrategy(BuyAndHoldBtcUsd):
        @property
        def specification(self):  # type: ignore[no-untyped-def]
            base = buy_and_hold_specification()
            return base.model_copy(update={"required_data": (*base.required_data, "volume")})

        def initialize(self, context):  # type: ignore[no-untyped-def]
            raise AssertionError("undeclared strategy must be rejected before initialization")

    with pytest.raises(StrategyRejectedError) as rejected:
        StrategyRunner().run(
            package=load_dataset_package(NORMAL_FIXTURE),
            fixture_file_sha256=EXPECTED_FIXTURE_SHA256,
            request=strategy_request(),
            environment=strategy_environment(),
            strategy=UndeclaredDataStrategy(BuyAndHoldParameters()),
        )
    assert rejected.value.code is StrategyRejectionCode.UNDECLARED_DATA


def test_future_dated_output_is_rejected() -> None:
    class FutureOutputStrategy(BuyAndHoldBtcUsd):
        def on_event(self, event: StrategyBar):  # type: ignore[no-untyped-def]
            outputs = super().on_event(event)
            if not outputs:
                return outputs
            signal = outputs[0]
            assert isinstance(signal, Signal)
            return (
                signal.model_copy(
                    update={"event_time_utc": signal.event_time_utc + timedelta(minutes=1)}
                ),
                *outputs[1:],
            )

    with pytest.raises(StrategyRejectedError) as rejected:
        StrategyRunner(backtester=DeterministicBacktester()).run(
            package=load_dataset_package(NORMAL_FIXTURE),
            fixture_file_sha256=EXPECTED_FIXTURE_SHA256,
            request=strategy_request(),
            environment=strategy_environment(),
            strategy=FutureOutputStrategy(BuyAndHoldParameters()),
        )
    assert rejected.value.code is StrategyRejectionCode.INVALID_OUTPUT
