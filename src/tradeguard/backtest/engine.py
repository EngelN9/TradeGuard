"""Deterministic, offline-only backtest/replay orchestration."""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal

from tradeguard.backtest.event_loop import TimelineKind, build_timeline
from tradeguard.backtest.models import (
    BacktestArtifact,
    BacktestPlan,
    BacktestResult,
    CorporateActionLedgerEntry,
    FillLedgerEntry,
    OrderLedgerEntry,
    OrderStatus,
    PlannedOrder,
    PositionLedgerEntry,
    RunEnvironment,
)
from tradeguard.data.models import CorporateAction, InstrumentMetadata, OHLCVBar
from tradeguard.data.package import DatasetPackage
from tradeguard.data.quality import require_validation_evidence_eligible
from tradeguard.domain.serialization import deterministic_checksum
from tradeguard.execution_models.conservative import (
    ConservativeBarExecutionModel,
    ExecutionDisposition,
)
from tradeguard.experiments.manifest import (
    DatasetManifestReference,
    RunDateRange,
    RunManifest,
)
from tradeguard.portfolio.ledger import (
    InsufficientCashError,
    InsufficientPositionError,
    PortfolioLedger,
)


class BacktestRejectedError(ValueError):
    """Raised when an input or unknown state fails closed."""


@dataclass
class _OrderState:
    order: PlannedOrder
    filled_quantity: Decimal = Decimal("0")
    active: bool = False
    rejected: bool = False
    blocked: bool = False
    reasons: list[str] = field(default_factory=list)

    @property
    def remaining_quantity(self) -> Decimal:
        return self.order.quantity - self.filled_quantity


class DeterministicBacktester:
    """Pure historical simulation; it has no network or order-submission path."""

    def __init__(self) -> None:
        self._execution = ConservativeBarExecutionModel()

    def run(
        self,
        *,
        package: DatasetPackage,
        plan: BacktestPlan,
        environment: RunEnvironment,
    ) -> BacktestArtifact:
        report = package.validate_quality()
        require_validation_evidence_eligible(package.manifest, report)
        self._validate_plan(package, plan)
        timeline, ignored_records = build_timeline(package, plan)
        states = {order.order_id: _OrderState(order=order) for order in plan.orders}
        ledger = PortfolioLedger(
            initial_cash=plan.initial_cash,
            base_currency=plan.base_currency,
        )
        fills: list[FillLedgerEntry] = []
        actions: list[CorporateActionLedgerEntry] = []
        positions: list[PositionLedgerEntry] = []
        pnl_series = []
        marks: dict[tuple[str, str], Decimal] = {}
        warnings: set[str] = set()
        if report.status.value == "WARN":
            warnings.add("dataset quality gate returned WARN")
        if ignored_records:
            warnings.add(f"ignored {ignored_records} non-bar market records")

        for event in timeline:
            if event.kind is TimelineKind.ORDER:
                order = event.payload
                if not isinstance(order, PlannedOrder):
                    raise TypeError("order timeline payload type mismatch")
                states[order.order_id].active = True
            elif event.kind is TimelineKind.CORPORATE_ACTION:
                action = event.payload
                if not isinstance(action, CorporateAction):
                    raise TypeError("corporate-action timeline payload type mismatch")
                applied = ledger.apply_corporate_action(action)
                if applied is not None:
                    actions.append(applied)
            else:
                bar = event.payload
                if not isinstance(bar, OHLCVBar):
                    raise TypeError("bar timeline payload type mismatch")
                marks[(bar.venue, bar.symbol)] = bar.close_price
                self._process_bar(
                    package=package,
                    plan=plan,
                    bar=bar,
                    states=states,
                    ledger=ledger,
                    fills=fills,
                    warnings=warnings,
                )
                position_snapshot, pnl = ledger.mark(
                    event_time_utc=bar.event_time_utc,
                    marks=marks,
                )
                positions.extend(position_snapshot)
                pnl_series.append(pnl)

        if not pnl_series:
            position_snapshot, pnl = ledger.mark(
                event_time_utc=package.manifest.date_range.end_utc,
                marks=marks,
            )
            positions.extend(position_snapshot)
            pnl_series.append(pnl)
        order_ledger = tuple(self._finalize_order(state) for state in states.values())
        conservation = ledger.conservation_report(pnl_series[-1])
        if not conservation.conserved:
            raise BacktestRejectedError("portfolio conservation check failed")
        result = BacktestResult.build(
            run_id=plan.run_id,
            run_type=plan.run_type,
            plan_checksum=plan.checksum(),
            dataset_manifest_checksum=package.manifest.checksum(),
            orders=order_ledger,
            fills=tuple(fills),
            corporate_actions=tuple(actions),
            positions=tuple(positions),
            pnl_series=tuple(pnl_series),
            ending_asset_balances=ledger.asset_balances(),
            ending_currency_balances=ledger.currency_balances(),
            conservation=conservation,
            warnings=tuple(sorted(warnings)),
        )
        manifest = self._build_manifest(package, plan, environment, result)
        return BacktestArtifact(manifest=manifest, result=result)

    @staticmethod
    def _validate_plan(package: DatasetPackage, plan: BacktestPlan) -> None:
        venues = {metadata.venue for metadata in package.instrument_metadata}
        for order in plan.orders:
            if order.asset_class is not package.manifest.asset_class:
                raise BacktestRejectedError("order asset class differs from the dataset")
            if order.symbol not in package.manifest.symbols:
                raise BacktestRejectedError("order symbol is outside the dataset universe")
            if order.venue not in venues:
                raise BacktestRejectedError("order venue is outside the dataset metadata")
        currencies = {
            metadata.currency or metadata.quote_asset
            for metadata in package.instrument_metadata
            if metadata.symbol in package.manifest.symbols
        }
        if currencies != {plan.base_currency}:
            raise BacktestRejectedError("plan base currency differs from instrument metadata")

    def _process_bar(  # noqa: PLR0913 - deterministic dependencies remain explicit
        self,
        *,
        package: DatasetPackage,
        plan: BacktestPlan,
        bar: OHLCVBar,
        states: dict[str, _OrderState],
        ledger: PortfolioLedger,
        fills: list[FillLedgerEntry],
        warnings: set[str],
    ) -> None:
        metadata = self._metadata_for(package, bar)
        for order_id in sorted(states):
            state = states[order_id]
            if not state.active or state.rejected or state.remaining_quantity <= 0:
                continue
            decision = self._execution.evaluate(
                order=state.order,
                remaining_quantity=state.remaining_quantity,
                bar=bar,
                metadata=metadata,
                knowledge_time_utc=package.policy.knowledge_time_utc,
                latency_seconds=plan.execution.latency_seconds,
                max_participation_rate=plan.execution.max_participation_rate,
                equity_costs=plan.equity_costs,
                crypto_costs=plan.crypto_costs,
                market_sessions=package.market_sessions,
                maintenance_intervals=package.maintenance_intervals,
            )
            if decision.disposition is ExecutionDisposition.WAIT:
                if decision.reason == "look_ahead_guard_same_bar":
                    warnings.add(f"{state.order.order_id}: same-close fill rejected")
                    state.reasons.append(decision.reason)
                continue
            if decision.disposition is ExecutionDisposition.BLOCK:
                state.blocked = True
                state.reasons.append(decision.reason)
                warnings.add(f"{state.order.order_id}: {decision.reason}")
                continue
            if decision.disposition is ExecutionDisposition.REJECT:
                state.rejected = True
                state.active = False
                state.reasons.append(decision.reason)
                continue
            if decision.costs is None:
                raise TypeError("fill decision omitted cost evidence")
            fill = FillLedgerEntry(
                fill_id=deterministic_checksum(
                    {
                        "order_id": state.order.order_id,
                        "bar": deterministic_checksum(bar),
                        "filled_before": state.filled_quantity,
                        "quantity": decision.quantity,
                    }
                ),
                order_id=state.order.order_id,
                asset_class=state.order.asset_class,
                venue=state.order.venue,
                symbol=state.order.symbol,
                side=state.order.side,
                order_type=state.order.order_type,
                event_time_utc=bar.event_time_utc,
                price=decision.price,
                quantity=decision.quantity,
                costs=decision.costs,
            )
            try:
                ledger.apply_fill(fill)
            except (InsufficientCashError, InsufficientPositionError) as exc:
                state.rejected = True
                state.active = False
                state.reasons.append(str(exc))
                continue
            fills.append(fill)
            state.filled_quantity += fill.quantity
            if state.remaining_quantity == 0:
                state.active = False

    @staticmethod
    def _metadata_for(package: DatasetPackage, bar: OHLCVBar) -> InstrumentMetadata:
        matches = [
            metadata
            for metadata in package.instrument_metadata
            if metadata.asset_class is bar.asset_class
            and metadata.venue == bar.venue
            and metadata.symbol == bar.symbol
            and metadata.is_point_in_time_valid(
                effective_at=bar.event_time_utc,
                knowledge_time=package.policy.knowledge_time_utc,
            )
        ]
        if len(matches) != 1:
            raise BacktestRejectedError("exactly one point-in-time metadata record is required")
        return matches[0]

    @staticmethod
    def _finalize_order(state: _OrderState) -> OrderLedgerEntry:
        if state.rejected:
            status = OrderStatus.REJECTED
        elif state.remaining_quantity == 0:
            status = OrderStatus.FILLED
        elif state.filled_quantity > 0:
            status = OrderStatus.PARTIALLY_FILLED
        elif state.blocked:
            status = OrderStatus.BLOCKED
        else:
            status = OrderStatus.UNFILLED
        return OrderLedgerEntry(
            order_id=state.order.order_id,
            status=status,
            requested_quantity=state.order.quantity,
            filled_quantity=state.filled_quantity,
            remaining_quantity=state.remaining_quantity,
            reasons=tuple(dict.fromkeys(state.reasons)),
        )

    @staticmethod
    def _build_manifest(
        package: DatasetPackage,
        plan: BacktestPlan,
        environment: RunEnvironment,
        result: BacktestResult,
    ) -> RunManifest:
        cost_version = (
            plan.equity_costs.version
            if package.manifest.asset_class.value == "equity"
            else plan.crypto_costs.version
        )
        return RunManifest(
            run_id=plan.run_id,
            run_type=plan.run_type,
            strategy_id=plan.strategy_id,
            strategy_version=plan.strategy_version,
            git_sha=environment.git_sha,
            dirty_worktree=environment.dirty_worktree,
            config_hash=plan.checksum(),
            dataset_manifests=(
                DatasetManifestReference(
                    dataset_id=package.manifest.dataset_id,
                    dataset_version=package.manifest.dataset_version,
                    checksum=package.manifest.checksum(),
                ),
            ),
            date_range=RunDateRange(
                start_utc=package.manifest.date_range.start_utc,
                end_utc=package.manifest.date_range.end_utc,
            ),
            universe=package.manifest.symbols,
            random_seed=plan.random_seed,
            python_version=environment.python_version,
            platform=environment.platform,
            dependency_lock_hash=environment.dependency_lock_hash,
            cost_model_version=cost_version,
            execution_model_version=plan.execution.version,
            started_at=environment.started_at,
            completed_at=environment.completed_at,
            result_checksum=result.result_checksum,
            warnings=result.warnings,
            validation_failures=(),
        )
