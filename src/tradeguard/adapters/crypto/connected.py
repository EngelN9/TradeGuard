"""Opt-in Coinbase public REST/WebSocket qualification with redacted evidence."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import Annotated, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from tradeguard.adapters.crypto.coinbase import CoinbaseCryptoMarketDataAdapter
from tradeguard.adapters.crypto.configuration import CoinbaseReleaseConfiguration
from tradeguard.adapters.crypto.errors import CryptoAdapterError, CryptoAdapterFailureCode
from tradeguard.adapters.crypto.protocol import Checksum, RestHealthState, TradingStatus
from tradeguard.adapters.crypto.stream import StreamRunResult, StreamState, WebSocketConnector
from tradeguard.adapters.crypto.transport import RestTransport
from tradeguard.data.quality import QualityStatus
from tradeguard.domain.serialization import UtcDateTime, deterministic_checksum

RUN_CONNECTED_VARIABLE = "TRADEGUARD_RUN_COINBASE_CONNECTED_TESTS"
_MINIMUM_CONNECTED_WEBSOCKET_MESSAGES = 4
RestHealthEvidence = Literal["HEALTHY", "DEGRADED", "UNAVAILABLE", "NOT_RUN"]
MetadataStatusEvidence = Literal["ONLINE", "NOT_TRADABLE", "UNKNOWN", "NOT_RUN"]


class ConnectedSmokeStatus(StrEnum):
    SKIP_NOT_OPTED_IN = "SKIP_NOT_OPTED_IN"
    BLOCKED_RATE_LIMIT = "BLOCKED_RATE_LIMIT"
    BLOCKED_PROVIDER_UNAVAILABLE = "BLOCKED_PROVIDER_UNAVAILABLE"
    FAIL_SCHEMA_DRIFT = "FAIL_SCHEMA_DRIFT"
    FAIL_DATA_QUALITY = "FAIL_DATA_QUALITY"
    FAIL_REQUEST_REJECTED = "FAIL_REQUEST_REJECTED"
    FAIL_SCOPE_VIOLATION = "FAIL_SCOPE_VIOLATION"
    FAIL_STREAM_NOT_TRADABLE = "FAIL_STREAM_NOT_TRADABLE"
    FAIL_CLEAN_SHUTDOWN = "FAIL_CLEAN_SHUTDOWN"
    PASS = "PASS"  # noqa: S105 - qualification state, not a credential


class ConnectedSmokeOutcome(StrEnum):
    SKIP = "SKIP"
    BLOCKED = "BLOCKED"
    FAIL = "FAIL"
    PASS = "PASS"  # noqa: S105 - qualification outcome, not a credential


class CryptoConnectedSmokeResult(BaseModel):
    """No-credential, no-market-value public qualification record."""

    model_config = ConfigDict(frozen=True, extra="forbid", validate_default=True)

    schema_version: Literal["1.0.0"] = "1.0.0"
    provider: Literal["coinbase_advanced_trade"] = "coinbase_advanced_trade"
    product_id: Literal["BTC-USD"] = "BTC-USD"
    status: ConnectedSmokeStatus
    outcome: ConnectedSmokeOutcome
    reason_code: str
    passed: bool
    provider_contacted: bool
    authentication_used: Literal[False] = False
    credential_required: Literal[False] = False
    observed_at: UtcDateTime
    rest_health: RestHealthEvidence
    metadata_status: MetadataStatusEvidence
    rest_trade_count: Annotated[int, Field(ge=0, le=10)]
    websocket_message_count: Annotated[int, Field(ge=0, le=20)]
    websocket_record_count: Annotated[int, Field(ge=0)]
    reconnect_count: Annotated[int, Field(ge=0, le=3)]
    sequence_validated: bool
    clean_shutdown: bool
    rest_manifest_checksum: Checksum | None = None
    websocket_manifest_checksum: Checksum | None = None
    rest_response_bundle_sha256: Checksum | None = None
    websocket_message_bundle_sha256: Checksum | None = None
    rest_quality_result: Literal["PASS", "WARN", "FAIL"] | None = None
    websocket_quality_result: Literal["PASS", "WARN", "FAIL"] | None = None
    provider_fallback_used: Literal[False] = False
    raw_market_values_persisted: Literal[False] = False
    raw_market_values_published: Literal[False] = False
    promotion_gate: Literal["BLOCKED"] = "BLOCKED"
    promotion_blockers: tuple[str, ...]

    @model_validator(mode="after")
    def validate_state(self) -> Self:
        if self.passed is not (self.status is ConnectedSmokeStatus.PASS):
            raise ValueError("passed must be true exactly for PASS")
        if self.outcome is not _outcome_for(self.status):
            raise ValueError("outcome must match detailed status")
        if not self.provider_contacted and (
            self.rest_health != "NOT_RUN"
            or self.metadata_status != "NOT_RUN"
            or self.websocket_message_count
            or self.rest_trade_count
        ):
            raise ValueError("uncontacted provider cannot have connected observations")
        if self.status is ConnectedSmokeStatus.PASS and (
            not self.provider_contacted
            or self.rest_health != "HEALTHY"
            or self.metadata_status != "ONLINE"
            or self.rest_trade_count < 1
            or self.websocket_message_count < _MINIMUM_CONNECTED_WEBSOCKET_MESSAGES
            or self.websocket_record_count < 1
            or not self.sequence_validated
            or not self.clean_shutdown
            or self.rest_manifest_checksum is None
            or self.websocket_manifest_checksum is None
            or self.rest_response_bundle_sha256 is None
            or self.websocket_message_bundle_sha256 is None
            or self.rest_quality_result not in {"PASS", "WARN"}
            or self.websocket_quality_result not in {"PASS", "WARN"}
        ):
            raise ValueError("PASS requires complete public REST and WebSocket evidence")
        return self


def run_connected_smoke(
    *,
    environment: Mapping[str, str],
    release_configuration: CoinbaseReleaseConfiguration,
    rest_transport: RestTransport | None = None,
    websocket_connector: WebSocketConnector | None = None,
    clock: Callable[[], datetime] | None = None,
) -> CryptoConnectedSmokeResult:
    """Run a bounded public-only smoke only after an explicit local opt-in."""

    effective_clock = clock or (lambda: datetime.now(UTC))
    observed_at = _normalize_clock(effective_clock())
    if environment.get(RUN_CONNECTED_VARIABLE) != "1":
        return _result(
            status=ConnectedSmokeStatus.SKIP_NOT_OPTED_IN,
            observed_at=observed_at,
            provider_contacted=False,
        )
    adapter = CoinbaseCryptoMarketDataAdapter(
        release_configuration=release_configuration,
        rest_transport=rest_transport,
        websocket_connector=websocket_connector,
        clock=effective_clock,
    )
    boundary = release_configuration.connected_smoke
    try:
        health = adapter.rest_health()
        metadata = adapter.instrument_metadata(boundary.product_id)
        trades = adapter.public_trades(
            boundary.product_id,
            limit=boundary.rest_trade_limit,
        )
        quote = adapter.best_bid_ask(boundary.product_id)
        stream = adapter.websocket_stream(
            boundary.product_id,
            stop_after_messages=boundary.websocket_maximum_messages,
            deadline_utc=observed_at + timedelta(seconds=boundary.websocket_deadline_seconds),
        )
        if not isinstance(stream, StreamRunResult):
            raise TypeError("stream adapter returned an invalid result")
    except CryptoAdapterError as exc:
        return _result(
            status=_status_for_error(exc.code),
            observed_at=observed_at,
            provider_contacted=True,
            reason_code=exc.code.value,
        )
    if health.state is not RestHealthState.HEALTHY:
        return _result(
            status=ConnectedSmokeStatus.FAIL_DATA_QUALITY,
            observed_at=observed_at,
            provider_contacted=True,
            reason_code="FAIL_REST_HEALTH",
            rest_health=_health_evidence(health.state),
            metadata_status=_metadata_evidence(metadata.trading_status),
        )
    if metadata.trading_status is not TradingStatus.ONLINE:
        return _result(
            status=ConnectedSmokeStatus.FAIL_DATA_QUALITY,
            observed_at=observed_at,
            provider_contacted=True,
            reason_code="FAIL_METADATA_NOT_TRADABLE",
            rest_health=_health_evidence(health.state),
            metadata_status=_metadata_evidence(metadata.trading_status),
        )
    if not stream.clean_shutdown:
        status = ConnectedSmokeStatus.FAIL_CLEAN_SHUTDOWN
        reason = status.value
    elif (
        stream.final_state is not StreamState.STOPPED
        or stream.alerts
        or stream.messages_received < boundary.websocket_minimum_messages
        or not stream.records
        or stream.manifest is None
        or stream.quality_report is None
    ):
        status = ConnectedSmokeStatus.FAIL_STREAM_NOT_TRADABLE
        reason = status.value
    else:
        status = ConnectedSmokeStatus.PASS
        reason = status.value
    rest_raw_checksums = (
        health.raw_response_sha256,
        *(call.raw_response_sha256 for call in trades.provider_calls),
        quote.provider_call.raw_response_sha256,
    )
    return _result(
        status=status,
        observed_at=observed_at,
        provider_contacted=True,
        reason_code=reason,
        rest_health=_health_evidence(health.state),
        metadata_status=_metadata_evidence(metadata.trading_status),
        rest_trade_count=len(trades.records),
        websocket_message_count=stream.messages_received,
        websocket_record_count=len(stream.records),
        reconnect_count=stream.reconnect_count,
        sequence_validated=not stream.alerts,
        clean_shutdown=stream.clean_shutdown,
        rest_manifest_checksum=trades.manifest.checksum(),
        websocket_manifest_checksum=(
            stream.manifest.checksum() if stream.manifest is not None else None
        ),
        rest_response_bundle_sha256=deterministic_checksum(rest_raw_checksums),
        websocket_message_bundle_sha256=deterministic_checksum(stream.raw_message_sha256),
        rest_quality_result=_quality(trades.quality_report.status),
        websocket_quality_result=(
            _quality(stream.quality_report.status) if stream.quality_report is not None else None
        ),
    )


def _result(  # noqa: PLR0913 - every public evidence field remains explicit
    *,
    status: ConnectedSmokeStatus,
    observed_at: datetime,
    provider_contacted: bool,
    reason_code: str | None = None,
    rest_health: RestHealthEvidence = "NOT_RUN",
    metadata_status: MetadataStatusEvidence = "NOT_RUN",
    rest_trade_count: int = 0,
    websocket_message_count: int = 0,
    websocket_record_count: int = 0,
    reconnect_count: int = 0,
    sequence_validated: bool = False,
    clean_shutdown: bool = False,
    rest_manifest_checksum: str | None = None,
    websocket_manifest_checksum: str | None = None,
    rest_response_bundle_sha256: str | None = None,
    websocket_message_bundle_sha256: str | None = None,
    rest_quality_result: Literal["PASS", "WARN", "FAIL"] | None = None,
    websocket_quality_result: Literal["PASS", "WARN", "FAIL"] | None = None,
) -> CryptoConnectedSmokeResult:
    return CryptoConnectedSmokeResult(
        status=status,
        outcome=_outcome_for(status),
        reason_code=reason_code or status.value,
        passed=status is ConnectedSmokeStatus.PASS,
        provider_contacted=provider_contacted,
        observed_at=observed_at,
        rest_health=rest_health,
        metadata_status=metadata_status,
        rest_trade_count=rest_trade_count,
        websocket_message_count=websocket_message_count,
        websocket_record_count=websocket_record_count,
        reconnect_count=reconnect_count,
        sequence_validated=sequence_validated,
        clean_shutdown=clean_shutdown,
        rest_manifest_checksum=rest_manifest_checksum,
        websocket_manifest_checksum=websocket_manifest_checksum,
        rest_response_bundle_sha256=rest_response_bundle_sha256,
        websocket_message_bundle_sha256=websocket_message_bundle_sha256,
        rest_quality_result=rest_quality_result,
        websocket_quality_result=websocket_quality_result,
        promotion_blockers=_promotion_blockers(status),
    )


def _status_for_error(code: CryptoAdapterFailureCode) -> ConnectedSmokeStatus:
    if code is CryptoAdapterFailureCode.BLOCKED_RATE_LIMIT:
        return ConnectedSmokeStatus.BLOCKED_RATE_LIMIT
    if code is CryptoAdapterFailureCode.BLOCKED_PROVIDER_UNAVAILABLE:
        return ConnectedSmokeStatus.BLOCKED_PROVIDER_UNAVAILABLE
    if code is CryptoAdapterFailureCode.FAIL_SCHEMA_DRIFT:
        return ConnectedSmokeStatus.FAIL_SCHEMA_DRIFT
    if code is CryptoAdapterFailureCode.FAIL_DATA_QUALITY:
        return ConnectedSmokeStatus.FAIL_DATA_QUALITY
    if code is CryptoAdapterFailureCode.FAIL_SCOPE_VIOLATION:
        return ConnectedSmokeStatus.FAIL_SCOPE_VIOLATION
    return ConnectedSmokeStatus.FAIL_REQUEST_REJECTED


def _outcome_for(status: ConnectedSmokeStatus) -> ConnectedSmokeOutcome:
    if status is ConnectedSmokeStatus.SKIP_NOT_OPTED_IN:
        return ConnectedSmokeOutcome.SKIP
    if status.value.startswith("BLOCKED_"):
        return ConnectedSmokeOutcome.BLOCKED
    if status.value.startswith("FAIL_"):
        return ConnectedSmokeOutcome.FAIL
    return ConnectedSmokeOutcome.PASS


def _promotion_blockers(status: ConnectedSmokeStatus) -> tuple[str, ...]:
    human = (
        "human review of connected Coinbase evidence is required",
        "explicit human promotion approval is required",
    )
    if status is ConnectedSmokeStatus.PASS:
        return human
    return ("a release-candidate Coinbase connected smoke PASS is required", *human)


def _quality(status: QualityStatus) -> Literal["PASS", "WARN", "FAIL"]:
    if status is QualityStatus.PASS:
        return "PASS"
    if status is QualityStatus.WARN:
        return "WARN"
    return "FAIL"


def _health_evidence(state: RestHealthState) -> RestHealthEvidence:
    if state is RestHealthState.HEALTHY:
        return "HEALTHY"
    if state is RestHealthState.DEGRADED:
        return "DEGRADED"
    return "UNAVAILABLE"


def _metadata_evidence(state: TradingStatus) -> MetadataStatusEvidence:
    if state is TradingStatus.ONLINE:
        return "ONLINE"
    if state is TradingStatus.NOT_TRADABLE:
        return "NOT_TRADABLE"
    return "UNKNOWN"


def _normalize_clock(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("connected clock must be timezone-aware")
    return value.astimezone(UTC)
