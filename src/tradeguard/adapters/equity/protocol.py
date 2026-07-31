"""Provider-neutral contracts for read-only equity market data."""

from __future__ import annotations

from datetime import date
from typing import Annotated, Literal, Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict, Field, model_validator

from tradeguard.data.manifest import DatasetManifest
from tradeguard.data.models import CorporateAction, InstrumentMetadata, MarketSession, OHLCVBar
from tradeguard.data.quality import QualityReport

NonEmptyText = Annotated[str, Field(min_length=1, max_length=2048)]
Checksum = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]


class AdapterContractModel(BaseModel):
    """Strict immutable base for adapter boundary contracts."""

    model_config = ConfigDict(frozen=True, extra="forbid", validate_default=True)


class RateLimitDeclaration(AdapterContractModel):
    """Documented limits; account dashboard remains authoritative."""

    model: NonEmptyText
    known_basic_api_credits_per_minute: Annotated[int, Field(gt=0)] | None = None
    known_basic_daily_credits: Annotated[int, Field(gt=0)] | None = None
    authoritative_source: NonEmptyText
    reviewed_at: date


class EquityAdapterCapabilities(AdapterContractModel):
    """Machine-readable declaration of enabled, not merely provider-offered, features."""

    schema_version: Literal["1.0.0"] = "1.0.0"
    provider: NonEmptyText
    approval_status: Literal["APPROVED_WITH_CONDITIONS"]
    public_market_data: bool
    authentication_required: bool
    historical_bars: bool
    latest_quote: bool
    latest_bar: bool
    delayed_or_end_of_day: bool
    real_time: bool
    market_calendar_source: Literal["internal_deterministic_registry"]
    timezone_source: Literal["provider_validated_against_internal_registry"]
    symbol_normalization: bool
    corporate_actions: bool
    enabled_host: Literal["api.twelvedata.com"]
    enabled_paths: tuple[Literal["/time_series"], ...]
    approved_symbols: tuple[Literal["AAPL"], ...]
    approved_mics: tuple[Literal["XNAS", "XNGS"], ...]
    rate_limits: RateLimitDeclaration
    licensing_constraints: tuple[NonEmptyText, ...]
    limitations: tuple[NonEmptyText, ...]


class HistoricalBarsRequest(AdapterContractModel):
    """Reviewed v0.1.0 historical-bar request envelope."""

    symbol: NonEmptyText
    mic: NonEmptyText
    interval: Literal["1day"] = "1day"
    output_size: Annotated[int, Field(ge=1, le=10)] = 10
    start_date: date | None = None
    end_date: date | None = None
    adjustment: Literal["none"] = "none"

    @model_validator(mode="after")
    def validate_date_range(self) -> HistoricalBarsRequest:
        if (
            self.start_date is not None
            and self.end_date is not None
            and self.end_date < self.start_date
        ):
            raise ValueError("end_date must not precede start_date")
        return self


class ProviderCallRecord(AdapterContractModel):
    """Redacted provider-call metadata safe for logs and public evidence."""

    provider: Literal["twelve_data"] = "twelve_data"
    host: Literal["api.twelvedata.com"] = "api.twelvedata.com"
    path: Literal["/time_series"] = "/time_series"
    method: Literal["GET"] = "GET"
    request_id: str | None = None
    attempts: Annotated[int, Field(ge=1, le=2)]
    response_status: Annotated[int, Field(ge=100, le=599)]
    raw_response_sha256: Checksum
    credential_in_url: Literal[False] = False
    raw_payload_retained: Literal[False] = False
    raw_payload_published: Literal[False] = False


class EquityDataset(AdapterContractModel):
    """Canonical provider result bound to provenance and quality evidence."""

    records: tuple[OHLCVBar, ...]
    manifest: DatasetManifest
    quality_report: QualityReport
    provider_call: ProviderCallRecord
    warnings: tuple[NonEmptyText, ...] = ()

    @model_validator(mode="after")
    def validate_bindings(self) -> EquityDataset:
        if len(self.records) != self.manifest.row_count:
            raise ValueError("record count must match dataset manifest")
        if self.quality_report.manifest_checksum != self.manifest.checksum():
            raise ValueError("quality report must be bound to dataset manifest")
        return self


@runtime_checkable
class EquityMarketDataAdapter(Protocol):
    """Provider-neutral, market-data-only equity capability."""

    @property
    def capabilities(self) -> EquityAdapterCapabilities:
        """Return the reviewed enabled capability declaration."""

    def normalize_symbol(self, symbol: str) -> str:
        """Return a canonical approved symbol or fail closed."""

    def instrument_metadata(self, symbol: str, mic: str) -> InstrumentMetadata:
        """Return reviewed point-in-time metadata without leaking provider schema."""

    def historical_bars(self, request: HistoricalBarsRequest) -> EquityDataset:
        """Fetch and normalize approved historical bars."""

    def latest_bar(self, symbol: str, mic: str) -> OHLCVBar:
        """Return the latest completed approved bar."""

    def market_calendar(
        self,
        mic: str,
        start_date: date,
        end_date: date,
    ) -> tuple[MarketSession, ...]:
        """Return only reviewed sessions from the internal registry."""

    def timezone(self, symbol: str, mic: str) -> str:
        """Return the reviewed IANA exchange timezone."""

    def corporate_actions(
        self,
        symbol: str,
        mic: str,
        start_date: date,
        end_date: date,
    ) -> tuple[CorporateAction, ...]:
        """Return corporate actions or explicitly reject unsupported capability."""
