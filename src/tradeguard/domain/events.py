"""Immutable, checksummed TradeGuard domain events."""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated, ClassVar, Literal, Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, JsonValue, ValidationInfo, model_validator

from tradeguard.domain.serialization import AuthorityDecimal, UtcDateTime, deterministic_checksum
from tradeguard.runtime import RuntimeEnvironment

CURRENT_EVENT_SCHEMA_VERSION = "1.0.0"
Checksum = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
NonEmptyText = Annotated[str, Field(min_length=1, max_length=512)]
NonNegativeDecimal = Annotated[AuthorityDecimal, Field(ge=0)]
PositiveDecimal = Annotated[AuthorityDecimal, Field(gt=0)]
UnitIntervalDecimal = Annotated[AuthorityDecimal, Field(ge=0, le=1)]


class AssetClass(StrEnum):
    """Supported event asset-class labels."""

    EQUITY = "equity"
    CRYPTO = "crypto"
    SYSTEM = "system"


class EventType(StrEnum):
    """Stable event discriminator values."""

    QUOTE = "Quote"
    TRADE_TICK = "TradeTick"
    BAR = "Bar"
    CORPORATE_ACTION = "CorporateAction"
    INSTRUMENT_METADATA_CHANGED = "InstrumentMetadataChanged"
    MARKET_SESSION_CHANGED = "MarketSessionChanged"
    DATA_QUALITY_ALERT = "DataQualityAlert"
    FEATURE_SNAPSHOT = "FeatureSnapshot"
    SIGNAL = "Signal"
    TARGET_POSITION = "TargetPosition"
    TRADE_PROPOSAL = "TradeProposal"
    RISK_DECISION = "RiskDecision"
    PAPER_ORDER = "PaperOrder"
    PAPER_FILL = "PaperFill"
    POSITION_SNAPSHOT = "PositionSnapshot"
    ACCOUNT_SNAPSHOT = "AccountSnapshot"
    PNL_SNAPSHOT = "PnLSnapshot"
    EXPOSURE_SNAPSHOT = "ExposureSnapshot"
    RECONCILIATION_DIFFERENCE = "ReconciliationDifference"
    DRIFT_ALERT = "DriftAlert"
    HEALTH_STATUS_CHANGED = "HealthStatusChanged"
    CONFIGURATION_CHANGED = "ConfigurationChanged"
    AUDIT_EVENT = "AuditEvent"


class Severity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class Side(StrEnum):
    BUY = "buy"
    SELL = "sell"


class OrderType(StrEnum):
    MARKET = "market"
    LIMIT = "limit"


class RiskDisposition(StrEnum):
    ACCEPT = "accept"
    ADJUST = "adjust"
    REJECT = "reject"
    PAUSE = "pause"
    REVIEW = "review"


class ReconciliationStatus(StrEnum):
    MATCHED = "MATCHED"
    MISMATCHED = "MISMATCHED"
    UNKNOWN = "UNKNOWN"
    STALE = "STALE"
    UNAVAILABLE = "UNAVAILABLE"


class EventModel(BaseModel):
    """Strict immutable model base."""

    model_config = ConfigDict(frozen=True, extra="forbid", validate_default=True)


class DomainEvent(EventModel):
    """Shared immutable event envelope with a deterministic integrity checksum."""

    expected_event_type: ClassVar[EventType]

    event_id: UUID
    schema_version: Literal["1.0.0"] = "1.0.0"
    event_type: EventType
    source: NonEmptyText
    asset_class: AssetClass
    venue: NonEmptyText
    symbol: NonEmptyText
    event_time_utc: UtcDateTime
    ingest_time_utc: UtcDateTime
    sequence_number: Annotated[int, Field(ge=0)]
    correlation_id: UUID
    causation_id: UUID | None = None
    run_id: UUID
    payload_checksum: Checksum

    @model_validator(mode="after")
    def validate_envelope(self, info: ValidationInfo) -> Self:
        """Reject type mismatches, time reversal, and checksum tampering."""

        if self.event_type is not self.expected_event_type:
            raise ValueError("event_type does not match the concrete event model")
        if self.ingest_time_utc < self.event_time_utc:
            raise ValueError("ingest_time_utc must not precede event_time_utc")
        if not (info.context or {}).get("skip_checksum"):
            expected_checksum = checksum_event_payload(self)
            if self.payload_checksum != expected_checksum:
                raise ValueError("payload_checksum does not match canonical event content")
        return self

    @classmethod
    def build(cls, **data: object) -> Self:
        """Build a validated event and derive its checksum deterministically."""

        if "payload_checksum" in data:
            raise ValueError("payload_checksum is derived and must not be supplied to build")
        candidate = cls.model_validate(
            {**data, "payload_checksum": "0" * 64},
            context={"skip_checksum": True},
        )
        return candidate.model_copy(update={"payload_checksum": checksum_event_payload(candidate)})


def checksum_event_payload(event: DomainEvent) -> str:
    """Checksum all immutable event content except the checksum field itself."""

    payload = event.model_dump(mode="python", exclude={"payload_checksum"})
    return deterministic_checksum(payload)


class Quote(DomainEvent):
    expected_event_type: ClassVar[EventType] = EventType.QUOTE
    event_type: Literal[EventType.QUOTE] = EventType.QUOTE
    bid_price: NonNegativeDecimal
    ask_price: NonNegativeDecimal
    bid_quantity: NonNegativeDecimal
    ask_quantity: NonNegativeDecimal

    @model_validator(mode="after")
    def validate_quote(self) -> Self:
        if self.bid_price > self.ask_price:
            raise ValueError("bid_price must not exceed ask_price")
        return self


class TradeTick(DomainEvent):
    expected_event_type: ClassVar[EventType] = EventType.TRADE_TICK
    event_type: Literal[EventType.TRADE_TICK] = EventType.TRADE_TICK
    trade_id: NonEmptyText
    price: NonNegativeDecimal
    quantity: PositiveDecimal


class Bar(DomainEvent):
    expected_event_type: ClassVar[EventType] = EventType.BAR
    event_type: Literal[EventType.BAR] = EventType.BAR
    interval_seconds: Annotated[int, Field(gt=0)]
    open_price: NonNegativeDecimal
    high_price: NonNegativeDecimal
    low_price: NonNegativeDecimal
    close_price: NonNegativeDecimal
    volume: NonNegativeDecimal

    @model_validator(mode="after")
    def validate_ohlcv(self) -> Self:
        if self.high_price < max(self.open_price, self.close_price, self.low_price):
            raise ValueError("high_price violates OHLC ordering")
        if self.low_price > min(self.open_price, self.close_price, self.high_price):
            raise ValueError("low_price violates OHLC ordering")
        return self


class CorporateAction(DomainEvent):
    expected_event_type: ClassVar[EventType] = EventType.CORPORATE_ACTION
    event_type: Literal[EventType.CORPORATE_ACTION] = EventType.CORPORATE_ACTION
    action_type: NonEmptyText
    effective_at: UtcDateTime
    known_at: UtcDateTime
    ratio: PositiveDecimal | None = None
    cash_amount: NonNegativeDecimal | None = None
    currency: str | None = None


class InstrumentMetadataChanged(DomainEvent):
    expected_event_type: ClassVar[EventType] = EventType.INSTRUMENT_METADATA_CHANGED
    event_type: Literal[EventType.INSTRUMENT_METADATA_CHANGED] = (
        EventType.INSTRUMENT_METADATA_CHANGED
    )
    effective_at: UtcDateTime
    known_at: UtcDateTime
    changes: dict[str, JsonValue]


class MarketSessionChanged(DomainEvent):
    expected_event_type: ClassVar[EventType] = EventType.MARKET_SESSION_CHANGED
    event_type: Literal[EventType.MARKET_SESSION_CHANGED] = EventType.MARKET_SESSION_CHANGED
    session_status: NonEmptyText
    session_open_utc: UtcDateTime | None = None
    session_close_utc: UtcDateTime | None = None

    @model_validator(mode="after")
    def validate_session_window(self) -> Self:
        if (
            self.session_open_utc is not None
            and self.session_close_utc is not None
            and self.session_close_utc < self.session_open_utc
        ):
            raise ValueError("session_close_utc must not precede session_open_utc")
        return self


class DataQualityAlert(DomainEvent):
    expected_event_type: ClassVar[EventType] = EventType.DATA_QUALITY_ALERT
    event_type: Literal[EventType.DATA_QUALITY_ALERT] = EventType.DATA_QUALITY_ALERT
    code: NonEmptyText
    severity: Severity
    message: NonEmptyText
    quarantined: bool


class FeatureSnapshot(DomainEvent):
    expected_event_type: ClassVar[EventType] = EventType.FEATURE_SNAPSHOT
    event_type: Literal[EventType.FEATURE_SNAPSHOT] = EventType.FEATURE_SNAPSHOT
    features: dict[str, AuthorityDecimal]


class Signal(DomainEvent):
    expected_event_type: ClassVar[EventType] = EventType.SIGNAL
    event_type: Literal[EventType.SIGNAL] = EventType.SIGNAL
    signal_name: NonEmptyText
    direction: Annotated[int, Field(ge=-1, le=1)]
    strength: UnitIntervalDecimal


class TargetPosition(DomainEvent):
    expected_event_type: ClassVar[EventType] = EventType.TARGET_POSITION
    event_type: Literal[EventType.TARGET_POSITION] = EventType.TARGET_POSITION
    target_quantity: AuthorityDecimal
    rationale: NonEmptyText


class TradeProposal(DomainEvent):
    expected_event_type: ClassVar[EventType] = EventType.TRADE_PROPOSAL
    event_type: Literal[EventType.TRADE_PROPOSAL] = EventType.TRADE_PROPOSAL
    side: Side
    order_type: OrderType
    quantity: PositiveDecimal
    limit_price: NonNegativeDecimal | None = None


class RiskDecision(DomainEvent):
    expected_event_type: ClassVar[EventType] = EventType.RISK_DECISION
    event_type: Literal[EventType.RISK_DECISION] = EventType.RISK_DECISION
    disposition: RiskDisposition
    reasons: tuple[NonEmptyText, ...]
    adjusted_quantity: AuthorityDecimal | None = None


class PaperOrder(DomainEvent):
    expected_event_type: ClassVar[EventType] = EventType.PAPER_ORDER
    event_type: Literal[EventType.PAPER_ORDER] = EventType.PAPER_ORDER
    paper_order_id: UUID
    side: Side
    order_type: OrderType
    quantity: PositiveDecimal
    limit_price: NonNegativeDecimal | None = None
    status: NonEmptyText


class PaperFill(DomainEvent):
    expected_event_type: ClassVar[EventType] = EventType.PAPER_FILL
    event_type: Literal[EventType.PAPER_FILL] = EventType.PAPER_FILL
    paper_order_id: UUID
    fill_id: UUID
    price: NonNegativeDecimal
    quantity: PositiveDecimal
    fee: NonNegativeDecimal


class PositionSnapshot(DomainEvent):
    expected_event_type: ClassVar[EventType] = EventType.POSITION_SNAPSHOT
    event_type: Literal[EventType.POSITION_SNAPSHOT] = EventType.POSITION_SNAPSHOT
    quantity: AuthorityDecimal
    average_price: NonNegativeDecimal
    market_value: AuthorityDecimal


class AccountSnapshot(DomainEvent):
    expected_event_type: ClassVar[EventType] = EventType.ACCOUNT_SNAPSHOT
    event_type: Literal[EventType.ACCOUNT_SNAPSHOT] = EventType.ACCOUNT_SNAPSHOT
    cash: NonNegativeDecimal
    equity: NonNegativeDecimal
    currency: NonEmptyText


class PnLSnapshot(DomainEvent):
    expected_event_type: ClassVar[EventType] = EventType.PNL_SNAPSHOT
    event_type: Literal[EventType.PNL_SNAPSHOT] = EventType.PNL_SNAPSHOT
    realized_pnl: AuthorityDecimal
    unrealized_pnl: AuthorityDecimal
    total_pnl: AuthorityDecimal

    @model_validator(mode="after")
    def validate_total(self) -> Self:
        if self.total_pnl != self.realized_pnl + self.unrealized_pnl:
            raise ValueError("total_pnl must equal realized_pnl plus unrealized_pnl")
        return self


class ExposureSnapshot(DomainEvent):
    expected_event_type: ClassVar[EventType] = EventType.EXPOSURE_SNAPSHOT
    event_type: Literal[EventType.EXPOSURE_SNAPSHOT] = EventType.EXPOSURE_SNAPSHOT
    gross_exposure: NonNegativeDecimal
    net_exposure: AuthorityDecimal
    concentrations: dict[str, NonNegativeDecimal]


class ReconciliationDifference(DomainEvent):
    expected_event_type: ClassVar[EventType] = EventType.RECONCILIATION_DIFFERENCE
    event_type: Literal[EventType.RECONCILIATION_DIFFERENCE] = EventType.RECONCILIATION_DIFFERENCE
    reconciliation_status: ReconciliationStatus
    field_name: NonEmptyText
    expected_value: AuthorityDecimal | None = None
    observed_value: AuthorityDecimal | None = None
    detail: NonEmptyText


class DriftAlert(DomainEvent):
    expected_event_type: ClassVar[EventType] = EventType.DRIFT_ALERT
    event_type: Literal[EventType.DRIFT_ALERT] = EventType.DRIFT_ALERT
    drift_type: NonEmptyText
    baseline_value: AuthorityDecimal
    current_value: AuthorityDecimal
    threshold: AuthorityDecimal
    observation_window: NonEmptyText
    severity: Severity
    possible_causes: tuple[NonEmptyText, ...]
    recommended_action: NonEmptyText


class HealthStatusChanged(DomainEvent):
    expected_event_type: ClassVar[EventType] = EventType.HEALTH_STATUS_CHANGED
    event_type: Literal[EventType.HEALTH_STATUS_CHANGED] = EventType.HEALTH_STATUS_CHANGED
    component: NonEmptyText
    status: NonEmptyText
    ready: bool


class ConfigurationChanged(DomainEvent):
    expected_event_type: ClassVar[EventType] = EventType.CONFIGURATION_CHANGED
    event_type: Literal[EventType.CONFIGURATION_CHANGED] = EventType.CONFIGURATION_CHANGED
    config_version: NonEmptyText
    before_hash: Checksum
    after_hash: Checksum
    changed_by: NonEmptyText
    reason: NonEmptyText


class AuditEvent(DomainEvent):
    expected_event_type: ClassVar[EventType] = EventType.AUDIT_EVENT
    event_type: Literal[EventType.AUDIT_EVENT] = EventType.AUDIT_EVENT
    actor_id: NonEmptyText
    actor_type: NonEmptyText
    action: NonEmptyText
    resource_type: NonEmptyText
    resource_id: NonEmptyText
    environment: RuntimeEnvironment
    reason: NonEmptyText
    before_hash: Checksum | None = None
    after_hash: Checksum | None = None
    result: NonEmptyText


AnyDomainEvent = Annotated[
    Quote
    | TradeTick
    | Bar
    | CorporateAction
    | InstrumentMetadataChanged
    | MarketSessionChanged
    | DataQualityAlert
    | FeatureSnapshot
    | Signal
    | TargetPosition
    | TradeProposal
    | RiskDecision
    | PaperOrder
    | PaperFill
    | PositionSnapshot
    | AccountSnapshot
    | PnLSnapshot
    | ExposureSnapshot
    | ReconciliationDifference
    | DriftAlert
    | HealthStatusChanged
    | ConfigurationChanged
    | AuditEvent,
    Field(discriminator="event_type"),
]
