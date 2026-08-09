"""Immutable contracts for deterministic orders, ledgers, and run artifacts."""

from __future__ import annotations

from decimal import Decimal
from enum import StrEnum
from typing import Annotated, Literal, Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, model_validator

from tradeguard.costs.models import CostBreakdown, CryptoCostModel, EquityCostModel
from tradeguard.domain.events import AssetClass, OrderType, Side
from tradeguard.domain.serialization import AuthorityDecimal, UtcDateTime, deterministic_checksum
from tradeguard.experiments.manifest import (
    DatasetManifestReference,
    RunDateRange,
    RunManifest,
    RunType,
)

Checksum = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
NonEmptyText = Annotated[str, Field(min_length=1, max_length=512)]
NonNegativeDecimal = Annotated[AuthorityDecimal, Field(ge=0)]
PositiveDecimal = Annotated[AuthorityDecimal, Field(gt=0)]


class BacktestModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", validate_default=True)


class OrderStatus(StrEnum):
    SUBMITTED = "submitted"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    REJECTED = "rejected"
    UNFILLED = "unfilled"
    BLOCKED = "blocked"


class PlannedOrder(BacktestModel):
    """An explicit research order; strategy generation arrives in Prompt 7."""

    order_id: NonEmptyText
    asset_class: Literal[AssetClass.EQUITY, AssetClass.CRYPTO]
    venue: NonEmptyText
    symbol: NonEmptyText
    side: Side
    order_type: OrderType
    quantity: PositiveDecimal
    limit_price: PositiveDecimal | None = None
    decision_event_time_utc: UtcDateTime
    submitted_at_utc: UtcDateTime
    sequence_number: Annotated[int, Field(ge=0)]

    @model_validator(mode="after")
    def validate_order(self) -> Self:
        if self.submitted_at_utc < self.decision_event_time_utc:
            raise ValueError("submitted_at_utc must not precede the decision event")
        if (self.order_type is OrderType.LIMIT) != (self.limit_price is not None):
            raise ValueError("limit_price must be present only for limit orders")
        return self


class ConservativeExecutionConfig(BacktestModel):
    version: Literal["conservative-bar-v1"] = "conservative-bar-v1"
    latency_seconds: Annotated[int, Field(ge=0)] = 1
    max_participation_rate: Annotated[AuthorityDecimal, Field(gt=0, le=1)] = Decimal("0.25")


class BacktestPlan(BacktestModel):
    """Complete deterministic input independent of workstation state."""

    schema_version: Literal["1.0.0"] = "1.0.0"
    run_id: UUID
    run_type: Literal[RunType.BACKTEST, RunType.REPLAY]
    strategy_id: NonEmptyText = "fixed-order-plan"
    strategy_version: NonEmptyText = "1.0.0"
    initial_cash: PositiveDecimal
    base_currency: NonEmptyText
    random_seed: Annotated[int, Field(ge=0)] = 0
    orders: tuple[PlannedOrder, ...]
    execution: ConservativeExecutionConfig = ConservativeExecutionConfig()
    equity_costs: EquityCostModel = EquityCostModel()
    crypto_costs: CryptoCostModel = CryptoCostModel()

    @model_validator(mode="after")
    def validate_unique_orders(self) -> Self:
        identifiers = [order.order_id for order in self.orders]
        if len(identifiers) != len(set(identifiers)):
            raise ValueError("order_id values must be unique")
        return self

    def checksum(self) -> str:
        return deterministic_checksum(self)


class RunEnvironment(BacktestModel):
    """Recorded runtime context; excluded from the deterministic result checksum."""

    git_sha: Annotated[str, Field(pattern=r"^[0-9a-f]{40}$")]
    dirty_worktree: bool
    python_version: NonEmptyText
    platform: NonEmptyText
    dependency_lock_hash: Checksum
    started_at: UtcDateTime
    completed_at: UtcDateTime | None = None

    @model_validator(mode="after")
    def validate_completion(self) -> Self:
        if self.completed_at is not None and self.completed_at < self.started_at:
            raise ValueError("completed_at must not precede started_at")
        return self


class BacktestRunIdentity(BacktestModel):
    """Reproducible manifest identity bound into the deterministic result."""

    schema_version: Literal["1.0.0"] = "1.0.0"
    strategy_id: NonEmptyText
    strategy_version: NonEmptyText
    git_sha: Annotated[str, Field(pattern=r"^[0-9a-f]{40}$")]
    dirty_worktree: bool
    config_hash: Checksum
    dataset_manifests: Annotated[tuple[DatasetManifestReference, ...], Field(min_length=1)]
    date_range: RunDateRange
    universe: Annotated[tuple[NonEmptyText, ...], Field(min_length=1)]
    random_seed: Annotated[int, Field(ge=0)]
    dependency_lock_hash: Checksum
    cost_model_version: NonEmptyText
    execution_model_version: NonEmptyText

    @classmethod
    def from_manifest(cls, manifest: RunManifest) -> BacktestRunIdentity:
        return cls(
            strategy_id=manifest.strategy_id,
            strategy_version=manifest.strategy_version,
            git_sha=manifest.git_sha,
            dirty_worktree=manifest.dirty_worktree,
            config_hash=manifest.config_hash,
            dataset_manifests=manifest.dataset_manifests,
            date_range=manifest.date_range,
            universe=manifest.universe,
            random_seed=manifest.random_seed,
            dependency_lock_hash=manifest.dependency_lock_hash,
            cost_model_version=manifest.cost_model_version,
            execution_model_version=manifest.execution_model_version,
        )


class OrderLedgerEntry(BacktestModel):
    order_id: NonEmptyText
    status: OrderStatus
    requested_quantity: PositiveDecimal
    filled_quantity: NonNegativeDecimal
    remaining_quantity: NonNegativeDecimal
    reasons: tuple[NonEmptyText, ...] = ()

    @model_validator(mode="after")
    def validate_quantities(self) -> Self:
        if self.filled_quantity + self.remaining_quantity != self.requested_quantity:
            raise ValueError("filled and remaining quantities must equal requested quantity")
        return self


class FillLedgerEntry(BacktestModel):
    fill_id: Checksum
    order_id: NonEmptyText
    asset_class: Literal[AssetClass.EQUITY, AssetClass.CRYPTO]
    venue: NonEmptyText
    symbol: NonEmptyText
    side: Side
    order_type: OrderType
    event_time_utc: UtcDateTime
    price: PositiveDecimal
    quantity: PositiveDecimal
    costs: CostBreakdown

    @property
    def notional(self) -> AuthorityDecimal:
        return self.price * self.quantity


class CorporateActionLedgerEntry(BacktestModel):
    action_checksum: Checksum
    symbol_before: NonEmptyText
    symbol_after: NonEmptyText
    action_type: NonEmptyText
    effective_at: UtcDateTime
    quantity_before: NonNegativeDecimal
    quantity_after: NonNegativeDecimal
    cash_delta: AuthorityDecimal


class PositionLedgerEntry(BacktestModel):
    event_time_utc: UtcDateTime
    asset_class: Literal[AssetClass.EQUITY, AssetClass.CRYPTO]
    venue: NonEmptyText
    symbol: NonEmptyText
    quantity: NonNegativeDecimal
    average_cost: NonNegativeDecimal
    mark_price: NonNegativeDecimal
    market_value: NonNegativeDecimal
    unrealized_pnl: AuthorityDecimal


class PnLLedgerEntry(BacktestModel):
    event_time_utc: UtcDateTime
    cash: NonNegativeDecimal
    market_value: NonNegativeDecimal
    realized_pnl: AuthorityDecimal
    unrealized_pnl: AuthorityDecimal
    total_pnl: AuthorityDecimal
    total_equity: NonNegativeDecimal

    @model_validator(mode="after")
    def validate_totals(self) -> Self:
        if self.total_pnl != self.realized_pnl + self.unrealized_pnl:
            raise ValueError("total_pnl must equal realized plus unrealized pnl")
        if self.total_equity != self.cash + self.market_value:
            raise ValueError("total_equity must equal cash plus market value")
        return self


class ConservationReport(BacktestModel):
    cash_equity_difference: AuthorityDecimal
    asset_quantity_differences: dict[str, AuthorityDecimal]
    duplicate_fill_ids_ignored: Annotated[int, Field(ge=0)]
    conserved: bool

    @model_validator(mode="after")
    def validate_status(self) -> Self:
        expected = self.cash_equity_difference == 0 and all(
            difference == 0 for difference in self.asset_quantity_differences.values()
        )
        if self.conserved is not expected:
            raise ValueError("conserved must reflect all reported differences")
        return self


class BacktestResult(BacktestModel):
    schema_version: Literal["1.1.0"] = "1.1.0"
    run_id: UUID
    run_type: Literal[RunType.BACKTEST, RunType.REPLAY]
    run_identity: BacktestRunIdentity
    plan_checksum: Checksum
    dataset_manifest_checksum: Checksum
    orders: tuple[OrderLedgerEntry, ...]
    fills: tuple[FillLedgerEntry, ...]
    corporate_actions: tuple[CorporateActionLedgerEntry, ...]
    positions: tuple[PositionLedgerEntry, ...]
    pnl_series: Annotated[tuple[PnLLedgerEntry, ...], Field(min_length=1)]
    ending_asset_balances: dict[NonEmptyText, NonNegativeDecimal]
    ending_currency_balances: Annotated[dict[NonEmptyText, NonNegativeDecimal], Field(min_length=1)]
    conservation: ConservationReport
    warnings: tuple[NonEmptyText, ...]
    result_checksum: Checksum

    @model_validator(mode="after")
    def validate_final_ledger_state(self) -> Self:
        if self.run_identity.config_hash != self.plan_checksum:
            raise ValueError("run identity config hash does not match the backtest plan")
        if (
            len(self.run_identity.dataset_manifests) != 1
            or self.run_identity.dataset_manifests[0].checksum != self.dataset_manifest_checksum
        ):
            raise ValueError("run identity dataset does not match the backtest result")
        if len(self.ending_currency_balances) != 1:
            raise ValueError("R3 requires exactly one ending base-currency balance")
        ending_cash = next(iter(self.ending_currency_balances.values()))
        if ending_cash != self.pnl_series[-1].cash:
            raise ValueError("ending currency balance does not match the final PnL cash")
        if not self.conservation.conserved:
            raise ValueError("a backtest result must pass conservation")
        return self

    @model_validator(mode="after")
    def validate_checksum(self, info: ValidationInfo) -> Self:
        if (info.context or {}).get("skip_result_checksum"):
            return self
        expected = deterministic_checksum(self.model_dump(exclude={"result_checksum"}))
        if self.result_checksum != expected:
            raise ValueError("result_checksum does not match deterministic result content")
        return self

    @classmethod
    def build(cls, **data: object) -> BacktestResult:
        candidate = cls.model_validate(
            {**data, "result_checksum": "0" * 64},
            context={"skip_result_checksum": True},
        )
        checksum = deterministic_checksum(candidate.model_dump(exclude={"result_checksum"}))
        return candidate.model_copy(update={"result_checksum": checksum})


class BacktestArtifact(BacktestModel):
    schema_version: Literal["1.1.0"] = "1.1.0"
    manifest: RunManifest
    result: BacktestResult
    manifest_checksum: Checksum

    @model_validator(mode="after")
    def validate_binding(self, info: ValidationInfo) -> Self:
        if self.manifest.run_id != self.result.run_id:
            raise ValueError("manifest and result run_id values differ")
        if self.manifest.run_type is not self.result.run_type:
            raise ValueError("manifest and result run_type values differ")
        if self.manifest.result_checksum != self.result.result_checksum:
            raise ValueError("manifest is not bound to the deterministic result")
        if self.manifest.config_hash != self.result.plan_checksum:
            raise ValueError("manifest config hash is not bound to the backtest plan")
        if (
            len(self.manifest.dataset_manifests) != 1
            or self.manifest.dataset_manifests[0].checksum != self.result.dataset_manifest_checksum
        ):
            raise ValueError("manifest dataset identity is not bound to the result")
        if self.manifest.warnings != self.result.warnings:
            raise ValueError("manifest warnings differ from result warnings")
        if not (info.context or {}).get("skip_manifest_checksum"):
            expected = deterministic_checksum(self.manifest)
            if self.manifest_checksum != expected:
                raise ValueError("manifest checksum does not match the complete run manifest")
        if BacktestRunIdentity.from_manifest(self.manifest) != self.result.run_identity:
            raise ValueError("manifest run identity is not bound to the backtest result")
        return self

    @classmethod
    def build(cls, *, manifest: RunManifest, result: BacktestResult) -> BacktestArtifact:
        candidate = cls.model_validate(
            {
                "manifest": manifest,
                "result": result,
                "manifest_checksum": "0" * 64,
            },
            context={"skip_manifest_checksum": True},
        )
        return candidate.model_copy(
            update={"manifest_checksum": deterministic_checksum(candidate.manifest)}
        )
