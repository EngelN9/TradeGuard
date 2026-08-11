"""Immutable contracts for the bounded R4 strategy research slice."""

from __future__ import annotations

from decimal import Decimal
from typing import Annotated, Final, Literal, Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, JsonValue, ValidationInfo, model_validator

from tradeguard.backtest.models import BacktestArtifact, BacktestPlan
from tradeguard.domain.events import AssetClass, Signal, TargetPosition, TradeProposal
from tradeguard.domain.serialization import (
    AuthorityDecimal,
    UtcDateTime,
    deterministic_checksum,
)

Checksum = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
NonEmptyText = Annotated[str, Field(min_length=1, max_length=512)]
PositiveDecimal = Annotated[AuthorityDecimal, Field(gt=0)]
StrategyOutput = Signal | TargetPosition | TradeProposal
R4_STRATEGY_ID: Final[Literal["buy-and-hold-btc-usd"]] = "buy-and-hold-btc-usd"
R4_DATASET_ID: Final[Literal["synthetic-normal"]] = "synthetic-normal"
R4_DATASET_VERSION: Final[Literal["1.0.0"]] = "1.0.0"
R4_MANIFEST_CHECKSUM: Final = "559e0e669ff3ab7d6bf37aaa192c8cba69c253361e2b640209320f5ffb0da750"
R4_FIXTURE_SHA256: Final = "babd3917bdafbe86cb840981be2d64a2c51a498f766a0aeb385a596e70aad578"
R4_VENUE: Final[Literal["SYNTH-CRYPTO"]] = "SYNTH-CRYPTO"
R4_SYMBOL: Final[Literal["BTC-USD"]] = "BTC-USD"
R4_OUTPUT_EVENT_COUNT: Final = 3


class StrategyModel(BaseModel):
    """Strict immutable strategy contract base."""

    model_config = ConfigDict(frozen=True, extra="forbid", validate_default=True)


class StrategyMarket(StrategyModel):
    asset_class: Literal[AssetClass.EQUITY, AssetClass.CRYPTO]
    venue: NonEmptyText
    symbol: NonEmptyText
    dataset_id: NonEmptyText
    dataset_version: NonEmptyText
    manifest_checksum: Checksum


class StrategySpecification(StrategyModel):
    schema_version: Literal["1.0.0"] = "1.0.0"
    strategy_id: NonEmptyText
    strategy_version: NonEmptyText
    supported_asset_classes: Annotated[tuple[AssetClass, ...], Field(min_length=1)]
    supported_markets: Annotated[tuple[StrategyMarket, ...], Field(min_length=1)]
    required_data: Annotated[tuple[NonEmptyText, ...], Field(min_length=1)]
    parameter_schema: dict[str, JsonValue]
    warmup_bars: Annotated[int, Field(ge=1)]
    allowed_outputs: tuple[Literal["Signal", "TargetPosition", "TradeProposal"], ...]
    assumptions: Annotated[tuple[NonEmptyText, ...], Field(min_length=1)]
    unsupported_markets: Annotated[tuple[NonEmptyText, ...], Field(min_length=1)]
    known_limitations: Annotated[tuple[NonEmptyText, ...], Field(min_length=1)]
    failure_modes: Annotated[tuple[NonEmptyText, ...], Field(min_length=1)]

    @model_validator(mode="after")
    def validate_declared_contract(self) -> Self:
        if len(set(self.supported_asset_classes)) != len(self.supported_asset_classes):
            raise ValueError("supported_asset_classes must be unique")
        if len(set(self.required_data)) != len(self.required_data):
            raise ValueError("required_data must be unique")
        if self.allowed_outputs != ("Signal", "TargetPosition", "TradeProposal"):
            raise ValueError("R4 strategies must use the complete bounded output sequence")
        market_asset_classes = {market.asset_class for market in self.supported_markets}
        if market_asset_classes != set(self.supported_asset_classes):
            raise ValueError("supported markets must match supported asset classes")
        return self


class BuyAndHoldParameters(StrategyModel):
    quantity: PositiveDecimal = Decimal("0.1000")

    @model_validator(mode="after")
    def validate_frozen_quantity(self) -> Self:
        if self.quantity != Decimal("0.1000"):
            raise ValueError("R4 buy-and-hold quantity is frozen at 0.1000 BTC")
        return self


class StrategyContext(StrategyModel):
    run_id: UUID
    correlation_id: UUID
    asset_class: Literal[AssetClass.CRYPTO]
    venue: Literal["SYNTH-CRYPTO"]
    symbol: Literal["BTC-USD"]
    dataset_id: Literal["synthetic-normal"]
    dataset_version: Literal["1.0.0"]
    manifest_checksum: Checksum
    strategy_version_hash: Checksum


class StrategyBar(StrategyModel):
    """The complete data view exposed to an R4 strategy."""

    asset_class: Literal[AssetClass.CRYPTO]
    venue: Literal["SYNTH-CRYPTO"]
    symbol: Literal["BTC-USD"]
    event_time_utc: UtcDateTime
    sequence_number: Annotated[int, Field(ge=0)]
    close_price: PositiveDecimal


class StrategyRunRequest(StrategyModel):
    schema_version: Literal["1.0.0"] = "1.0.0"
    run_id: UUID
    strategy_id: Literal["buy-and-hold-btc-usd"] = "buy-and-hold-btc-usd"
    parameters: BuyAndHoldParameters = BuyAndHoldParameters()
    initial_cash: PositiveDecimal = Decimal("100000")
    base_currency: Literal["USD"] = "USD"
    random_seed: Literal[0] = 0

    @model_validator(mode="after")
    def validate_frozen_research_budget(self) -> Self:
        if self.initial_cash != Decimal("100000"):
            raise ValueError("R4 initial cash is frozen at USD 100000")
        return self


class StrategySyntheticReport(StrategyModel):
    schema_version: Literal["1.0.0"] = "1.0.0"
    synthetic_only: Literal[True] = True
    classification: Literal["synthetic_research_baseline"] = "synthetic_research_baseline"
    promotion_status: Literal["NOT_EVALUATED"] = "NOT_EVALUATED"
    investment_advice: Literal[False] = False
    profitability_claim: Literal[False] = False
    strategy_id: Literal["buy-and-hold-btc-usd"]
    strategy_version_hash: Checksum
    dataset_manifest_checksum: Checksum
    output_events: Annotated[int, Field(ge=0)]
    planned_orders: Annotated[int, Field(ge=0)]
    fills: Annotated[int, Field(ge=0)]
    conserved: bool
    first_decision_time_utc: UtcDateTime
    first_fill_time_utc: UtcDateTime | None
    holding_at_end: bool
    backtest_result_checksum: Checksum
    warning: Literal[
        "Synthetic offline research only; not investment advice or promotion evidence."
    ] = "Synthetic offline research only; not investment advice or promotion evidence."
    report_checksum: Checksum

    @model_validator(mode="after")
    def validate_report(self, info: ValidationInfo) -> Self:
        expected = deterministic_checksum(self.model_dump(exclude={"report_checksum"}))
        if (
            not (info.context or {}).get("skip_report_checksum")
            and self.report_checksum != expected
        ):
            raise ValueError("report_checksum does not match synthetic report content")
        if not self.conserved or not self.holding_at_end:
            raise ValueError("R4 synthetic report requires conservation and an ending holding")
        if (
            self.output_events != R4_OUTPUT_EVENT_COUNT
            or self.planned_orders != 1
            or self.fills != 1
        ):
            raise ValueError("R4 synthetic report requires the frozen one-entry result")
        return self

    @classmethod
    def build(cls, **data: object) -> StrategySyntheticReport:
        candidate = cls.model_validate(
            {**data, "report_checksum": "0" * 64},
            context={"skip_report_checksum": True},
        )
        return candidate.model_copy(
            update={
                "report_checksum": deterministic_checksum(
                    candidate.model_dump(exclude={"report_checksum"})
                )
            }
        )


class StrategyRunArtifact(StrategyModel):
    schema_version: Literal["1.0.0"] = "1.0.0"
    synthetic_only: Literal[True] = True
    fixture_file_sha256: Literal["babd3917bdafbe86cb840981be2d64a2c51a498f766a0aeb385a596e70aad578"]
    specification: StrategySpecification
    parameters: BuyAndHoldParameters
    strategy_version_hash: Checksum
    dataset_manifest_checksum: Checksum
    outputs: tuple[StrategyOutput, ...]
    plan: BacktestPlan
    backtest: BacktestArtifact
    report: StrategySyntheticReport
    artifact_checksum: Checksum

    @model_validator(mode="after")
    def validate_binding(self, info: ValidationInfo) -> Self:  # noqa: PLR0912
        if len(self.specification.supported_markets) != 1:
            raise ValueError("R4 artifact requires exactly one supported market")
        market = self.specification.supported_markets[0]
        if (
            self.specification.strategy_id != R4_STRATEGY_ID
            or self.specification.supported_asset_classes != (AssetClass.CRYPTO,)
            or market.asset_class is not AssetClass.CRYPTO
            or market.venue != R4_VENUE
            or market.symbol != R4_SYMBOL
            or market.dataset_id != R4_DATASET_ID
            or market.dataset_version != R4_DATASET_VERSION
            or market.manifest_checksum != R4_MANIFEST_CHECKSUM
            or self.dataset_manifest_checksum != R4_MANIFEST_CHECKSUM
        ):
            raise ValueError("strategy artifact differs from the frozen R4 market contract")
        expected_version = strategy_version_hash(self.specification, self.parameters)
        if self.strategy_version_hash != expected_version:
            raise ValueError("strategy version hash does not match specification and parameters")
        if self.plan.strategy_id != self.specification.strategy_id:
            raise ValueError("backtest plan strategy_id differs from the strategy specification")
        if self.plan.strategy_version != self.strategy_version_hash:
            raise ValueError("backtest plan is not bound to the strategy version hash")
        if self.backtest.result.run_id != self.plan.run_id:
            raise ValueError("strategy plan and backtest run_id values differ")
        if self.backtest.result.plan_checksum != self.plan.checksum():
            raise ValueError("backtest result is not bound to the generated strategy plan")
        if self.backtest.result.dataset_manifest_checksum != self.dataset_manifest_checksum:
            raise ValueError("strategy artifact dataset differs from the backtest dataset")
        if self.backtest.result.run_identity.strategy_id != self.specification.strategy_id:
            raise ValueError("backtest result strategy_id differs from the specification")
        if self.backtest.result.run_identity.strategy_version != self.strategy_version_hash:
            raise ValueError("backtest result is not bound to the strategy version hash")
        if [type(output) for output in self.outputs] != [
            Signal,
            TargetPosition,
            TradeProposal,
        ]:
            raise ValueError("R4 output sequence must be Signal, TargetPosition, TradeProposal")
        signal, target, proposal = self.outputs
        if (
            not isinstance(signal, Signal)
            or not isinstance(target, TargetPosition)
            or not isinstance(proposal, TradeProposal)
        ):
            raise ValueError("R4 output models do not match the required sequence")
        if target.causation_id != signal.event_id or proposal.causation_id != target.event_id:
            raise ValueError("strategy output causation chain is invalid")
        if any(output.run_id != self.plan.run_id for output in self.outputs):
            raise ValueError("strategy outputs and plan run_id values differ")
        if any(
            (output.asset_class, output.venue, output.symbol)
            != (market.asset_class, market.venue, market.symbol)
            for output in self.outputs
        ):
            raise ValueError("strategy output market differs from the specification")
        if len(self.plan.orders) != 1:
            raise ValueError("R4 strategy plan requires exactly one research order")
        order = self.plan.orders[0]
        if (
            order.side is not proposal.side
            or order.order_type is not proposal.order_type
            or order.quantity != proposal.quantity
            or order.limit_price != proposal.limit_price
            or order.decision_event_time_utc != proposal.event_time_utc
            or order.submitted_at_utc != proposal.event_time_utc
            or order.sequence_number != proposal.sequence_number
        ):
            raise ValueError("research order does not mechanically match the trade proposal")
        if self.report.strategy_version_hash != self.strategy_version_hash:
            raise ValueError("synthetic report strategy hash differs from the artifact")
        if self.report.dataset_manifest_checksum != self.dataset_manifest_checksum:
            raise ValueError("synthetic report dataset differs from the artifact")
        if self.report.backtest_result_checksum != self.backtest.result.result_checksum:
            raise ValueError("synthetic report is not bound to the backtest result")
        expected_checksum = deterministic_checksum(self.model_dump(exclude={"artifact_checksum"}))
        if (
            not (info.context or {}).get("skip_strategy_artifact_checksum")
            and self.artifact_checksum != expected_checksum
        ):
            raise ValueError("artifact_checksum does not match strategy artifact content")
        return self

    @classmethod
    def build(cls, **data: object) -> StrategyRunArtifact:
        candidate = cls.model_validate(
            {**data, "artifact_checksum": "0" * 64},
            context={"skip_strategy_artifact_checksum": True},
        )
        return candidate.model_copy(
            update={
                "artifact_checksum": deterministic_checksum(
                    candidate.model_dump(exclude={"artifact_checksum"})
                )
            }
        )


def strategy_version_hash(
    specification: StrategySpecification,
    parameters: BuyAndHoldParameters,
) -> str:
    """Bind the declared strategy contract and canonical parameters."""

    return deterministic_checksum({"specification": specification, "parameters": parameters})
