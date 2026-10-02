"""Fail-closed orchestration from a trusted strategy to the R3 simulator."""

from __future__ import annotations

from enum import StrEnum
from typing import cast
from uuid import uuid5

from tradeguard.backtest.engine import DeterministicBacktester
from tradeguard.backtest.models import BacktestPlan, PlannedOrder, RunEnvironment
from tradeguard.data.models import MARKET_RECORD_ADAPTER, OHLCVBar
from tradeguard.data.package import DatasetPackage
from tradeguard.data.quality import QualityStatus
from tradeguard.domain.events import AssetClass, Signal, TargetPosition, TradeProposal
from tradeguard.domain.serialization import deterministic_checksum
from tradeguard.experiments.manifest import RunType
from tradeguard.strategies.buy_and_hold import (
    EXPECTED_DATASET_ID,
    EXPECTED_DATASET_VERSION,
    EXPECTED_FIXTURE_SHA256,
    EXPECTED_MANIFEST_CHECKSUM,
    EXPECTED_SYMBOL,
    EXPECTED_VENUE,
    REQUIRED_DATA,
    STRATEGY_ID,
    STRATEGY_UUID_NAMESPACE,
    BuyAndHoldBtcUsd,
)
from tradeguard.strategies.models import (
    StrategyBar,
    StrategyContext,
    StrategyOutput,
    StrategyRunArtifact,
    StrategyRunRequest,
    StrategySyntheticReport,
    strategy_version_hash,
)
from tradeguard.strategies.protocol import StrategyProtocol


class StrategyRejectionCode(StrEnum):
    INVALID_CONTRACT = "invalid_contract"
    UNDECLARED_DATA = "undeclared_data"
    UNSUPPORTED_MARKET = "unsupported_market"
    DATA_QUALITY = "data_quality"
    INVALID_OUTPUT = "invalid_output"


class StrategyRejectedError(ValueError):
    """A stable fail-closed strategy boundary rejection."""

    def __init__(self, code: StrategyRejectionCode, message: str) -> None:
        self.code = code
        super().__init__(f"{code.value}: {message}")


class ResearchPlanCompiler:
    """Mechanically map one proposal into an R3 research-only plan."""

    @staticmethod
    def compile(
        *,
        request: StrategyRunRequest,
        strategy_id: str,
        strategy_hash: str,
        outputs: tuple[StrategyOutput, ...],
    ) -> BacktestPlan:
        proposals = tuple(output for output in outputs if isinstance(output, TradeProposal))
        if len(proposals) != 1:
            raise StrategyRejectedError(
                StrategyRejectionCode.INVALID_OUTPUT,
                "R4 requires exactly one trade proposal",
            )
        proposal = proposals[0]
        if proposal.asset_class is not AssetClass.CRYPTO:
            raise StrategyRejectedError(
                StrategyRejectionCode.UNSUPPORTED_MARKET,
                "R4 research plan accepts crypto proposals only",
            )
        order_id = deterministic_checksum(
            {
                "purpose": "r4-research-plan",
                "proposal_id": proposal.event_id,
                "proposal_checksum": proposal.payload_checksum,
                "strategy_version_hash": strategy_hash,
            }
        )
        order = PlannedOrder(
            order_id=order_id,
            asset_class=AssetClass.CRYPTO,
            venue=proposal.venue,
            symbol=proposal.symbol,
            side=proposal.side,
            order_type=proposal.order_type,
            quantity=proposal.quantity,
            limit_price=proposal.limit_price,
            decision_event_time_utc=proposal.event_time_utc,
            submitted_at_utc=proposal.event_time_utc,
            sequence_number=proposal.sequence_number,
        )
        return BacktestPlan(
            run_id=request.run_id,
            run_type=RunType.BACKTEST,
            strategy_id=strategy_id,
            strategy_version=strategy_hash,
            initial_cash=request.initial_cash,
            base_currency=request.base_currency,
            random_seed=request.random_seed,
            orders=(order,),
        )


class StrategyRunner:
    """Run the sole built-in R4 baseline against the exact reviewed fixture."""

    def __init__(self, *, backtester: DeterministicBacktester | None = None) -> None:
        self._backtester = backtester or DeterministicBacktester()

    def run(
        self,
        *,
        package: DatasetPackage,
        fixture_file_sha256: str,
        request: StrategyRunRequest,
        environment: RunEnvironment,
        strategy: StrategyProtocol | None = None,
    ) -> StrategyRunArtifact:
        bars = self._validate_dataset(package, fixture_file_sha256)
        selected = strategy or BuyAndHoldBtcUsd(request.parameters)
        if not isinstance(selected, StrategyProtocol):
            raise StrategyRejectedError(
                StrategyRejectionCode.INVALID_CONTRACT,
                "strategy does not implement StrategyProtocol",
            )
        specification = selected.specification
        if specification.strategy_id != request.strategy_id:
            raise StrategyRejectedError(
                StrategyRejectionCode.INVALID_CONTRACT,
                "request strategy_id differs from the implementation",
            )
        if tuple(specification.required_data) != REQUIRED_DATA:
            raise StrategyRejectedError(
                StrategyRejectionCode.UNDECLARED_DATA,
                "strategy requested data outside the frozen StrategyBar projection",
            )
        version_hash = strategy_version_hash(specification, request.parameters)
        correlation_id = uuid5(
            STRATEGY_UUID_NAMESPACE,
            f"{request.run_id}:{version_hash}:{package.manifest.checksum()}:correlation",
        )
        context = StrategyContext(
            run_id=request.run_id,
            correlation_id=correlation_id,
            asset_class=AssetClass.CRYPTO,
            venue=EXPECTED_VENUE,
            symbol=EXPECTED_SYMBOL,
            dataset_id=EXPECTED_DATASET_ID,
            dataset_version=EXPECTED_DATASET_VERSION,
            manifest_checksum=EXPECTED_MANIFEST_CHECKSUM,
            strategy_version_hash=version_hash,
        )
        selected.initialize(context)
        outputs: list[StrategyOutput] = []
        for bar in bars:
            view = StrategyBar(
                asset_class=AssetClass.CRYPTO,
                venue=EXPECTED_VENUE,
                symbol=EXPECTED_SYMBOL,
                event_time_utc=bar.event_time_utc,
                sequence_number=bar.sequence_number,
                close_price=bar.close_price,
            )
            emitted = selected.on_event(view)
            self._validate_outputs(emitted, view, context)
            outputs.extend(emitted)
        finalized = selected.finalize()
        if finalized:
            raise StrategyRejectedError(
                StrategyRejectionCode.INVALID_OUTPUT,
                "the frozen buy-and-hold baseline cannot emit during finalization",
            )
        frozen_outputs = tuple(outputs)
        plan = ResearchPlanCompiler.compile(
            request=request,
            strategy_id=specification.strategy_id,
            strategy_hash=version_hash,
            outputs=frozen_outputs,
        )
        backtest = self._backtester.run(
            package=package,
            plan=plan,
            environment=environment,
        )
        if not backtest.result.fills:
            raise StrategyRejectedError(
                StrategyRejectionCode.INVALID_OUTPUT,
                "frozen R4 fixture did not produce the required later-bar fill",
            )
        first_proposal = next(
            output for output in frozen_outputs if isinstance(output, TradeProposal)
        )
        holding_at_end = any(
            quantity > 0 for quantity in backtest.result.ending_asset_balances.values()
        )
        report = StrategySyntheticReport.build(
            strategy_id=STRATEGY_ID,
            strategy_version_hash=version_hash,
            dataset_manifest_checksum=package.manifest.checksum(),
            output_events=len(frozen_outputs),
            planned_orders=len(plan.orders),
            fills=len(backtest.result.fills),
            conserved=backtest.result.conservation.conserved,
            first_decision_time_utc=first_proposal.event_time_utc,
            first_fill_time_utc=backtest.result.fills[0].event_time_utc,
            holding_at_end=holding_at_end,
            backtest_result_checksum=backtest.result.result_checksum,
        )
        return StrategyRunArtifact.build(
            fixture_file_sha256=fixture_file_sha256,
            specification=specification,
            parameters=request.parameters,
            strategy_version_hash=version_hash,
            dataset_manifest_checksum=package.manifest.checksum(),
            outputs=frozen_outputs,
            plan=plan,
            backtest=backtest,
            report=report,
        )

    @staticmethod
    def _validate_dataset(
        package: DatasetPackage,
        fixture_file_sha256: str,
    ) -> tuple[OHLCVBar, ...]:
        if fixture_file_sha256 != EXPECTED_FIXTURE_SHA256:
            raise StrategyRejectedError(
                StrategyRejectionCode.UNSUPPORTED_MARKET,
                "fixture file checksum differs from the reviewed R4 input",
            )
        manifest = package.manifest
        if (
            manifest.dataset_id != EXPECTED_DATASET_ID
            or manifest.dataset_version != EXPECTED_DATASET_VERSION
            or manifest.asset_class is not AssetClass.CRYPTO
            or manifest.symbols != (EXPECTED_SYMBOL,)
        ):
            raise StrategyRejectedError(
                StrategyRejectionCode.UNSUPPORTED_MARKET,
                "dataset manifest differs from the frozen R4 market contract",
            )
        if len(package.instrument_metadata) != 1:
            raise StrategyRejectedError(
                StrategyRejectionCode.UNSUPPORTED_MARKET,
                "R4 requires exactly one instrument metadata record",
            )
        metadata = package.instrument_metadata[0]
        if (
            metadata.asset_class is not AssetClass.CRYPTO
            or metadata.venue != EXPECTED_VENUE
            or metadata.symbol != EXPECTED_SYMBOL
        ):
            raise StrategyRejectedError(
                StrategyRejectionCode.UNSUPPORTED_MARKET,
                "instrument identity differs from synthetic BTC-USD",
            )
        quality = package.validate_quality()
        if quality.status is not QualityStatus.PASS:
            raise StrategyRejectedError(
                StrategyRejectionCode.DATA_QUALITY,
                f"dataset quality must be PASS, got {quality.status.value}",
            )
        if manifest.checksum() != EXPECTED_MANIFEST_CHECKSUM:
            raise StrategyRejectedError(
                StrategyRejectionCode.UNSUPPORTED_MARKET,
                "dataset manifest checksum differs from the reviewed R4 input",
            )
        parsed = tuple(MARKET_RECORD_ADAPTER.validate_python(record) for record in package.records)
        if not parsed or any(not isinstance(record, OHLCVBar) for record in parsed):
            raise StrategyRejectedError(
                StrategyRejectionCode.UNDECLARED_DATA,
                "R4 accepts completed OHLCV bars only",
            )
        bars = cast(tuple[OHLCVBar, ...], parsed)
        return tuple(
            sorted(
                bars,
                key=lambda bar: (
                    bar.event_time_utc,
                    bar.ingest_time_utc,
                    bar.sequence_number,
                    deterministic_checksum(bar),
                ),
            )
        )

    @staticmethod
    def _validate_outputs(
        outputs: tuple[StrategyOutput, ...],
        bar: StrategyBar,
        context: StrategyContext,
    ) -> None:
        allowed = (Signal, TargetPosition, TradeProposal)
        for output in outputs:
            if not isinstance(output, allowed):
                raise StrategyRejectedError(
                    StrategyRejectionCode.INVALID_OUTPUT,
                    "strategy emitted an unsupported output type",
                )
            if output.run_id != context.run_id or output.correlation_id != context.correlation_id:
                raise StrategyRejectedError(
                    StrategyRejectionCode.INVALID_OUTPUT,
                    "strategy output identity differs from the run context",
                )
            if (output.asset_class, output.venue, output.symbol) != (
                context.asset_class,
                context.venue,
                context.symbol,
            ):
                raise StrategyRejectedError(
                    StrategyRejectionCode.INVALID_OUTPUT,
                    "strategy output market differs from the run context",
                )
            if output.event_time_utc != bar.event_time_utc:
                raise StrategyRejectedError(
                    StrategyRejectionCode.INVALID_OUTPUT,
                    "strategy output cannot use a past or future event time",
                )
            if output.ingest_time_utc != output.event_time_utc:
                raise StrategyRejectedError(
                    StrategyRejectionCode.INVALID_OUTPUT,
                    "synthetic strategy output ingest time must equal its event time",
                )
            if output.sequence_number <= bar.sequence_number:
                raise StrategyRejectedError(
                    StrategyRejectionCode.INVALID_OUTPUT,
                    "strategy output must be sequenced after the observed bar",
                )
