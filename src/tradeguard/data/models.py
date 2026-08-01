"""Canonical, immutable market-data models used before strategy evaluation."""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter, model_validator

from tradeguard.domain.events import AssetClass
from tradeguard.domain.serialization import AuthorityDecimal, UtcDateTime

MARKET_DATA_SCHEMA_VERSION = "1.0.0"
NonEmptyText = Annotated[str, Field(min_length=1, max_length=512)]
PositiveDecimal = Annotated[AuthorityDecimal, Field(gt=0)]
SupportedAssetClass = Literal[AssetClass.EQUITY, AssetClass.CRYPTO]


class MarketDataModel(BaseModel):
    """Strict immutable base for canonical data contracts."""

    model_config = ConfigDict(frozen=True, extra="forbid", validate_default=True)


class RecordType(StrEnum):
    QUOTE = "quote"
    TRADE = "trade"
    BAR = "bar"


class MarketDataRecord(MarketDataModel):
    """Common canonical envelope for ordered market observations."""

    schema_version: Literal["1.0.0"] = "1.0.0"
    record_type: RecordType
    source: NonEmptyText
    asset_class: SupportedAssetClass
    venue: NonEmptyText
    symbol: NonEmptyText
    event_time_utc: UtcDateTime
    ingest_time_utc: UtcDateTime
    sequence_number: Annotated[int, Field(ge=0)]

    @model_validator(mode="after")
    def validate_ingest_order(self) -> Self:
        if self.ingest_time_utc < self.event_time_utc:
            raise ValueError("ingest_time_utc must not precede event_time_utc")
        return self


class Quote(MarketDataRecord):
    """Best bid and ask observation.

    Crossed quotes and invalid numeric values remain representable so the
    quality gate can quarantine the original observation without rewriting it.
    """

    record_type: Literal[RecordType.QUOTE] = RecordType.QUOTE
    bid_price: AuthorityDecimal
    ask_price: AuthorityDecimal
    bid_quantity: AuthorityDecimal
    ask_quantity: AuthorityDecimal
    quote_asset: str | None = None


class Trade(MarketDataRecord):
    """Individual trade observation."""

    record_type: Literal[RecordType.TRADE] = RecordType.TRADE
    trade_id: NonEmptyText
    price: AuthorityDecimal
    quantity: AuthorityDecimal
    quote_asset: str | None = None


class OHLCVBar(MarketDataRecord):
    """Time-bounded OHLCV observation."""

    record_type: Literal[RecordType.BAR] = RecordType.BAR
    interval_start_utc: UtcDateTime
    interval_end_utc: UtcDateTime
    open_price: AuthorityDecimal
    high_price: AuthorityDecimal
    low_price: AuthorityDecimal
    close_price: AuthorityDecimal
    volume: AuthorityDecimal

    @model_validator(mode="after")
    def validate_interval_identity(self) -> Self:
        if self.interval_end_utc <= self.interval_start_utc:
            raise ValueError("bar interval must have positive duration")
        if self.event_time_utc != self.interval_end_utc:
            raise ValueError("bar event_time_utc must equal interval_end_utc")
        return self


AnyMarketRecord = Annotated[Quote | Trade | OHLCVBar, Field(discriminator="record_type")]
MARKET_RECORD_ADAPTER: TypeAdapter[AnyMarketRecord] = TypeAdapter(AnyMarketRecord)


class InstrumentMetadata(MarketDataModel):
    """Point-in-time instrument definition."""

    schema_version: Literal["1.0.0"] = "1.0.0"
    source: NonEmptyText
    asset_class: SupportedAssetClass
    venue: NonEmptyText
    symbol: NonEmptyText
    canonical_symbol: NonEmptyText
    currency: str | None = None
    quote_asset: str | None = None
    tick_size: PositiveDecimal
    step_size: PositiveDecimal
    lot_size: PositiveDecimal
    minimum_quantity: Annotated[AuthorityDecimal, Field(ge=0)]
    minimum_notional: Annotated[AuthorityDecimal, Field(ge=0)]
    timezone: NonEmptyText
    session_calendar: str | None = None
    active_from: UtcDateTime
    active_to: UtcDateTime | None = None
    known_at: UtcDateTime
    metadata_version: NonEmptyText

    @model_validator(mode="after")
    def validate_market_identity(self) -> Self:
        if self.active_to is not None and self.active_to <= self.active_from:
            raise ValueError("active_to must follow active_from")
        if self.asset_class is AssetClass.EQUITY:
            if not self.currency or self.quote_asset is not None:
                raise ValueError("equity metadata requires currency and no quote_asset")
            if not self.session_calendar:
                raise ValueError("equity metadata requires a session_calendar")
        elif not self.quote_asset or self.currency is not None:
            raise ValueError("crypto metadata requires quote_asset and no currency")
        return self

    def is_active_at(self, effective_at: UtcDateTime) -> bool:
        """Return whether the instrument was active at the effective time."""

        return self.active_from <= effective_at and (
            self.active_to is None or effective_at < self.active_to
        )

    def is_known_at(self, knowledge_time: UtcDateTime) -> bool:
        """Return whether this metadata was available at the knowledge time."""

        return self.known_at <= knowledge_time

    def is_point_in_time_valid(
        self,
        *,
        effective_at: UtcDateTime,
        knowledge_time: UtcDateTime,
    ) -> bool:
        """Require both effective-time activity and knowledge-time availability."""

        return self.is_active_at(effective_at) and self.is_known_at(knowledge_time)


class SessionStatus(StrEnum):
    OPEN = "open"
    CLOSED = "closed"
    HALTED = "halted"


class MarketSession(MarketDataModel):
    """Point-in-time equity session definition, including half days."""

    schema_version: Literal["1.0.0"] = "1.0.0"
    source: NonEmptyText
    venue: NonEmptyText
    session_calendar: NonEmptyText
    session_open_utc: UtcDateTime
    session_close_utc: UtcDateTime
    known_at: UtcDateTime
    status: SessionStatus
    half_day: bool = False

    @model_validator(mode="after")
    def validate_window(self) -> Self:
        if self.session_close_utc <= self.session_open_utc:
            raise ValueError("session_close_utc must follow session_open_utc")
        return self

    def contains(self, timestamp: UtcDateTime) -> bool:
        """Use a half-open session interval to avoid double counting closes."""

        return self.session_open_utc <= timestamp < self.session_close_utc


class CorporateActionType(StrEnum):
    SPLIT = "split"
    REVERSE_SPLIT = "reverse_split"
    CASH_DIVIDEND = "cash_dividend"
    SYMBOL_CHANGE = "symbol_change"
    DELISTING = "delisting"


class CorporateAction(MarketDataModel):
    """Point-in-time equity corporate action."""

    schema_version: Literal["1.0.0"] = "1.0.0"
    source: NonEmptyText
    venue: NonEmptyText
    symbol: NonEmptyText
    action_type: CorporateActionType
    effective_at: UtcDateTime
    known_at: UtcDateTime
    action_version: NonEmptyText
    ratio: AuthorityDecimal | None = None
    cash_amount: AuthorityDecimal | None = None
    currency: str | None = None
    new_symbol: str | None = None


class MaintenanceInterval(MarketDataModel):
    """Known crypto venue-maintenance interval."""

    venue: NonEmptyText
    start_utc: UtcDateTime
    end_utc: UtcDateTime
    known_at: UtcDateTime
    reason: NonEmptyText

    @model_validator(mode="after")
    def validate_window(self) -> Self:
        if self.end_utc <= self.start_utc:
            raise ValueError("maintenance end must follow start")
        return self

    def contains(self, timestamp: UtcDateTime) -> bool:
        return self.start_utc <= timestamp < self.end_utc
