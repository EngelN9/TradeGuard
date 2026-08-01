"""Provider-neutral contracts for public, read-only cryptocurrency market data."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Annotated, Literal, Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict, Field, model_validator

from tradeguard.data.manifest import DatasetManifest
from tradeguard.data.models import InstrumentMetadata, OHLCVBar, Quote, Trade
from tradeguard.data.quality import QualityReport
from tradeguard.domain.serialization import AuthorityDecimal, UtcDateTime

NonEmptyText = Annotated[str, Field(min_length=1, max_length=2048)]
Checksum = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
_MAX_REVIEWED_RANGE_SECONDS = 600


class CryptoContractModel(BaseModel):
    """Strict immutable adapter-boundary model."""

    model_config = ConfigDict(frozen=True, extra="forbid", validate_default=True)


class TradingStatus(StrEnum):
    ONLINE = "ONLINE"
    NOT_TRADABLE = "NOT_TRADABLE"
    UNKNOWN = "UNKNOWN"


class MaintenanceStatus(StrEnum):
    CLEAR = "CLEAR"
    MAINTENANCE = "MAINTENANCE"
    UNKNOWN = "UNKNOWN"


class RestHealthState(StrEnum):
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    UNAVAILABLE = "UNAVAILABLE"


class CryptoAdapterCapabilities(CryptoContractModel):
    """Machine-readable declaration of enabled capabilities and prohibited surfaces."""

    schema_version: Literal["1.0.0"] = "1.0.0"
    provider: Literal["coinbase_advanced_trade"]
    approval_status: Literal["APPROVED_WITH_CONDITIONS"]
    public_only: Literal[True]
    authenticated: Literal[False]
    instrument_metadata: Literal[True]
    supported_trading_pairs: Literal[True]
    historical_bars: Literal[True]
    public_trades: Literal[True]
    best_bid_ask: Literal[True]
    rest_health: Literal[True]
    websocket_stream: Literal[True]
    venue_maintenance_status: Literal[True]
    rate_limit_metadata: Literal[True]
    user_channel: Literal[False]
    accounts: Literal[False]
    orders: Literal[False]
    transfers: Literal[False]
    withdrawals: Literal[False]
    derivatives: Literal[False]
    leverage: Literal[False]
    execution_grade: Literal[False]
    provider_fallback: Literal[False]
    enabled_rest_host: Literal["api.coinbase.com"]
    enabled_websocket_host: Literal["advanced-trade-ws.coinbase.com"]
    enabled_rest_paths: tuple[
        Literal[
            "/api/v3/brokerage/time",
            "/api/v3/brokerage/market/products/BTC-USD",
            "/api/v3/brokerage/market/products/BTC-USD/candles",
            "/api/v3/brokerage/market/products/BTC-USD/ticker",
        ],
        ...,
    ]
    enabled_websocket_channels: tuple[
        Literal["heartbeats", "market_trades", "status", "ticker"],
        ...,
    ]
    approved_pairs: tuple[Literal["BTC-USD"], ...]
    licensing_constraints: tuple[NonEmptyText, ...]
    limitations: tuple[NonEmptyText, ...]


class CryptoBarsRequest(CryptoContractModel):
    product_id: Literal["BTC-USD"] = "BTC-USD"
    start: UtcDateTime
    end: UtcDateTime
    granularity: Literal["ONE_MINUTE"] = "ONE_MINUTE"
    limit: Annotated[int, Field(ge=1, le=10)] = 5

    @model_validator(mode="after")
    def validate_range(self) -> CryptoBarsRequest:
        if self.end <= self.start:
            raise ValueError("end must follow start")
        if (self.end - self.start).total_seconds() > _MAX_REVIEWED_RANGE_SECONDS:
            raise ValueError("reviewed connected range must not exceed ten minutes")
        return self


class TradingPairMetadata(CryptoContractModel):
    instrument: InstrumentMetadata
    base_asset: NonEmptyText
    quote_asset: NonEmptyText
    trading_status: TradingStatus
    provider_status: NonEmptyText
    metadata_timestamp: UtcDateTime

    @model_validator(mode="after")
    def validate_identity(self) -> TradingPairMetadata:
        if (
            self.instrument.symbol != f"{self.base_asset}-{self.quote_asset}"
            or self.instrument.quote_asset != self.quote_asset
        ):
            raise ValueError("trading-pair metadata identity is inconsistent")
        return self


class RateLimitMetadata(CryptoContractModel):
    rest_limit: Literal["provider_enforced_not_published_for_unauthenticated_public_endpoints"]
    http_429_handling: Literal["one_bounded_retry"]
    websocket_connections_per_second_per_ip: Literal[8]
    websocket_unauthenticated_messages_per_second_per_ip: Literal[8]
    reconnect_backoff_seconds: tuple[float, float, float]
    observed_documentation_at: UtcDateTime

    @model_validator(mode="after")
    def validate_backoff(self) -> RateLimitMetadata:
        if self.reconnect_backoff_seconds != (1.0, 2.0, 4.0):
            raise ValueError("reconnect backoff must match the reviewed bounded schedule")
        return self


class RestHealth(CryptoContractModel):
    state: RestHealthState
    observed_at: UtcDateTime
    provider_time_utc: UtcDateTime | None = None
    response_status: Annotated[int, Field(ge=100, le=599)]
    raw_response_sha256: Checksum
    attempts: Annotated[int, Field(ge=1, le=2)]


class VenueMaintenance(CryptoContractModel):
    status: MaintenanceStatus
    trading_status: TradingStatus
    observed_at: UtcDateTime
    reason: NonEmptyText


class ProviderCallRecord(CryptoContractModel):
    provider: Literal["coinbase_advanced_trade"] = "coinbase_advanced_trade"
    host: Literal["api.coinbase.com"] = "api.coinbase.com"
    path: NonEmptyText
    method: Literal["GET"] = "GET"
    attempts: Annotated[int, Field(ge=1, le=2)]
    response_status: Annotated[int, Field(ge=100, le=599)]
    raw_response_sha256: Checksum
    authorization_sent: Literal[False] = False
    raw_payload_retained: Literal[False] = False
    raw_payload_published: Literal[False] = False


class BestBidAsk(CryptoContractModel):
    product_id: Literal["BTC-USD"] = "BTC-USD"
    observed_at: UtcDateTime
    bid_price: AuthorityDecimal
    ask_price: AuthorityDecimal
    bid_quantity: None = None
    ask_quantity: None = None
    quantity_status: Literal["UNAVAILABLE_FROM_ENDPOINT"] = "UNAVAILABLE_FROM_ENDPOINT"
    provider_call: ProviderCallRecord

    @model_validator(mode="after")
    def validate_book(self) -> BestBidAsk:
        if self.bid_price <= 0 or self.ask_price <= 0 or self.bid_price > self.ask_price:
            raise ValueError("best bid/ask must be positive and uncrossed")
        return self


class CryptoDataset(CryptoContractModel):
    records: tuple[OHLCVBar | Quote | Trade, ...]
    manifest: DatasetManifest
    quality_report: QualityReport
    provider_calls: tuple[ProviderCallRecord, ...]
    warnings: tuple[NonEmptyText, ...] = ()

    @model_validator(mode="after")
    def validate_bindings(self) -> CryptoDataset:
        if len(self.records) != self.manifest.row_count:
            raise ValueError("record count must match dataset manifest")
        if self.quality_report.manifest_checksum != self.manifest.checksum():
            raise ValueError("quality report must be bound to dataset manifest")
        return self


@runtime_checkable
class CryptoMarketDataAdapter(Protocol):
    """Public market-data-only capability with no account or execution surface."""

    @property
    def capabilities(self) -> CryptoAdapterCapabilities:
        """Return the human-reviewed capability declaration."""

    @property
    def rate_limits(self) -> RateLimitMetadata:
        """Return reviewed provider rate-limit metadata."""

    def supported_pairs(self) -> tuple[str, ...]:
        """Return the narrow reviewed spot-pair allowlist."""

    def instrument_metadata(self, product_id: str) -> TradingPairMetadata:
        """Fetch and normalize public point-in-time product metadata."""

    def historical_bars(self, request: CryptoBarsRequest) -> CryptoDataset:
        """Fetch and normalize public historical bars."""

    def public_trades(self, product_id: str, *, limit: int = 5) -> CryptoDataset:
        """Fetch and normalize recent public trades."""

    def best_bid_ask(self, product_id: str) -> BestBidAsk:
        """Return the public best bid and ask snapshot."""

    def rest_health(self) -> RestHealth:
        """Probe only the public server-time endpoint."""

    def venue_maintenance_status(self, product_id: str) -> VenueMaintenance:
        """Return explicit status; unknown provider state must remain unknown."""

    def websocket_stream(
        self,
        product_id: str,
        *,
        stop_after_messages: int,
        deadline_utc: datetime,
    ) -> object:
        """Run a bounded public stream and return implementation-specific evidence."""
