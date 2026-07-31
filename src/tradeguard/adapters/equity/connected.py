"""Opt-in connected smoke state machine and redacted public evidence model."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from datetime import UTC, datetime
from enum import StrEnum
from typing import Annotated, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, SecretStr, model_validator

from tradeguard.adapters.equity.calendar import DeterministicMicCalendarRegistry
from tradeguard.adapters.equity.configuration import TwelveDataReleaseConfiguration
from tradeguard.adapters.equity.errors import AdapterFailureCode, EquityAdapterError
from tradeguard.adapters.equity.protocol import Checksum, HistoricalBarsRequest
from tradeguard.adapters.equity.transport import HttpTransport
from tradeguard.adapters.equity.twelve_data import TwelveDataEquityAdapter
from tradeguard.data.quality import QualityStatus
from tradeguard.domain.serialization import UtcDateTime

RUN_CONNECTED_VARIABLE = "TRADEGUARD_RUN_CONNECTED_TESTS"
CREDENTIAL_VARIABLE = "TRADEGUARD_TWELVE_DATA_API_KEY"
MINIMUM_COMPLETED_SESSIONS = 5


class ConnectedSmokeStatus(StrEnum):
    SKIP_NOT_OPTED_IN = "SKIP_NOT_OPTED_IN"
    BLOCKED_MISSING_CREDENTIAL = "BLOCKED_MISSING_CREDENTIAL"
    BLOCKED_INVALID_CREDENTIAL = "BLOCKED_INVALID_CREDENTIAL"
    BLOCKED_ENTITLEMENT = "BLOCKED_ENTITLEMENT"
    BLOCKED_RATE_LIMIT = "BLOCKED_RATE_LIMIT"
    BLOCKED_PROVIDER_UNAVAILABLE = "BLOCKED_PROVIDER_UNAVAILABLE"
    BLOCKED_MARKET_CALENDAR = "BLOCKED_MARKET_CALENDAR"
    FAIL_SCHEMA_DRIFT = "FAIL_SCHEMA_DRIFT"
    FAIL_DATA_QUALITY = "FAIL_DATA_QUALITY"
    FAIL_REQUEST_REJECTED = "FAIL_REQUEST_REJECTED"
    FAIL_SCOPE_VIOLATION = "FAIL_SCOPE_VIOLATION"
    PASS = "PASS"  # noqa: S105 - qualification state, not a credential


class ConnectedSmokeOutcome(StrEnum):
    SKIP = "SKIP"
    BLOCKED = "BLOCKED"
    FAIL = "FAIL"
    PASS = "PASS"  # noqa: S105 - qualification outcome, not a credential


class ConnectedSmokeResult(BaseModel):
    """No-secret, no-market-value connected qualification record."""

    model_config = ConfigDict(frozen=True, extra="forbid", validate_default=True)

    schema_version: Literal["1.1.0"] = "1.1.0"
    provider: Literal["twelve_data"] = "twelve_data"
    symbol: Literal["AAPL"] = "AAPL"
    interval: Literal["1day"] = "1day"
    adjustment: Literal["none"] = "none"
    status: ConnectedSmokeStatus
    outcome: ConnectedSmokeOutcome
    reason_code: str
    passed: bool
    provider_contacted: bool
    credential_present: bool
    credential_exposed: Literal[False] = False
    observed_at: UtcDateTime
    request_attempts: Annotated[int, Field(ge=0, le=2)]
    completed_session_count: Annotated[int, Field(ge=0)]
    provider_request_id: str | None = None
    raw_response_sha256: Checksum | None = None
    manifest_checksum: Checksum | None = None
    quality_result: Literal["PASS", "WARN", "FAIL"] | None = None
    manifest_generated: bool
    provider_fallback_used: Literal[False] = False
    raw_market_values_persisted: Literal[False] = False
    raw_market_values_published: Literal[False] = False
    promotion_gate: Literal["BLOCKED"] = "BLOCKED"
    promotion_blockers: tuple[str, ...]

    @model_validator(mode="after")
    def validate_state(self) -> Self:
        if self.passed is not (self.status is ConnectedSmokeStatus.PASS):
            raise ValueError("passed must be true exactly when status is PASS")
        if self.outcome is not _outcome_for_status(self.status):
            raise ValueError("outcome must match the detailed connected status")
        if not self.provider_contacted and self.request_attempts != 0:
            raise ValueError("uncontacted provider cannot have request attempts")
        if self.status is ConnectedSmokeStatus.PASS and (
            not self.provider_contacted
            or not self.credential_present
            or self.request_attempts < 1
            or self.completed_session_count < MINIMUM_COMPLETED_SESSIONS
            or self.manifest_checksum is None
            or self.raw_response_sha256 is None
            or self.quality_result not in {"PASS", "WARN"}
            or not self.manifest_generated
        ):
            raise ValueError("PASS requires complete connected evidence")
        return self


def run_connected_smoke(
    *,
    environment: Mapping[str, str],
    calendar_registry: DeterministicMicCalendarRegistry,
    release_configuration: TwelveDataReleaseConfiguration,
    transport: HttpTransport | None = None,
    clock: Callable[[], datetime] | None = None,
) -> ConnectedSmokeResult:
    """Run at most one logical request, with one internal retry only for HTTP 429."""

    effective_clock = clock or (lambda: datetime.now(UTC))
    observed_at = _normalize_clock(effective_clock())
    credential_present = bool(environment.get(CREDENTIAL_VARIABLE, "").strip())
    if environment.get(RUN_CONNECTED_VARIABLE) != "1":
        return _result(
            status=ConnectedSmokeStatus.SKIP_NOT_OPTED_IN,
            reason_code=ConnectedSmokeStatus.SKIP_NOT_OPTED_IN.value,
            observed_at=observed_at,
            provider_contacted=False,
            credential_present=credential_present,
        )
    credential = environment.get(CREDENTIAL_VARIABLE, "").strip()
    if not credential:
        return _result(
            status=ConnectedSmokeStatus.BLOCKED_MISSING_CREDENTIAL,
            reason_code=ConnectedSmokeStatus.BLOCKED_MISSING_CREDENTIAL.value,
            observed_at=observed_at,
            provider_contacted=False,
            credential_present=False,
        )
    adapter = TwelveDataEquityAdapter(
        api_key=SecretStr(credential),
        calendar_registry=calendar_registry,
        release_configuration=release_configuration,
        transport=transport,
        clock=lambda: observed_at,
    )
    boundary = release_configuration.connected_smoke
    try:
        dataset = adapter.historical_bars(
            HistoricalBarsRequest(
                symbol=boundary.symbol,
                mic=boundary.mic,
                interval=boundary.interval,
                output_size=boundary.outputsize,
                adjustment=boundary.adjustment,
            )
        )
    except EquityAdapterError as exc:
        return _result(
            status=_status_for_failure(exc.code),
            reason_code=exc.code.value,
            observed_at=observed_at,
            provider_contacted=True,
            credential_present=True,
            request_attempts=2 if exc.code is AdapterFailureCode.BLOCKED_RATE_LIMIT else 1,
        )
    completed_session_count = len(dataset.records)
    if completed_session_count < boundary.minimum_completed_sessions:
        return _result(
            status=ConnectedSmokeStatus.FAIL_DATA_QUALITY,
            reason_code="FAIL_INSUFFICIENT_COMPLETED_SESSIONS",
            observed_at=observed_at,
            provider_contacted=True,
            credential_present=True,
            request_attempts=dataset.provider_call.attempts,
            completed_session_count=completed_session_count,
            provider_request_id=dataset.provider_call.request_id,
            raw_response_sha256=dataset.provider_call.raw_response_sha256,
            manifest_checksum=dataset.manifest.checksum(),
            quality_result=_quality_result(dataset.quality_report.status),
        )
    return _result(
        status=ConnectedSmokeStatus.PASS,
        reason_code=ConnectedSmokeStatus.PASS.value,
        observed_at=observed_at,
        provider_contacted=True,
        credential_present=True,
        request_attempts=dataset.provider_call.attempts,
        completed_session_count=completed_session_count,
        provider_request_id=dataset.provider_call.request_id,
        raw_response_sha256=dataset.provider_call.raw_response_sha256,
        manifest_checksum=dataset.manifest.checksum(),
        quality_result=_quality_result(dataset.quality_report.status),
    )


def _result(  # noqa: PLR0913 - explicit state evidence avoids ambiguous defaults
    *,
    status: ConnectedSmokeStatus,
    reason_code: str,
    observed_at: datetime,
    provider_contacted: bool,
    credential_present: bool,
    request_attempts: int = 0,
    completed_session_count: int = 0,
    provider_request_id: str | None = None,
    raw_response_sha256: str | None = None,
    manifest_checksum: str | None = None,
    quality_result: Literal["PASS", "WARN", "FAIL"] | None = None,
    promotion_blockers: tuple[str, ...] | None = None,
) -> ConnectedSmokeResult:
    return ConnectedSmokeResult(
        status=status,
        outcome=_outcome_for_status(status),
        reason_code=reason_code,
        passed=status is ConnectedSmokeStatus.PASS,
        provider_contacted=provider_contacted,
        credential_present=credential_present,
        observed_at=observed_at,
        request_attempts=request_attempts,
        completed_session_count=completed_session_count,
        provider_request_id=provider_request_id,
        raw_response_sha256=raw_response_sha256,
        manifest_checksum=manifest_checksum,
        quality_result=quality_result,
        manifest_generated=manifest_checksum is not None,
        promotion_blockers=promotion_blockers or _promotion_blockers(status),
    )


def _status_for_failure(code: AdapterFailureCode) -> ConnectedSmokeStatus:
    mapping = {
        AdapterFailureCode.BLOCKED_INVALID_CREDENTIAL: (
            ConnectedSmokeStatus.BLOCKED_INVALID_CREDENTIAL
        ),
        AdapterFailureCode.BLOCKED_ENTITLEMENT: ConnectedSmokeStatus.BLOCKED_ENTITLEMENT,
        AdapterFailureCode.BLOCKED_RATE_LIMIT: ConnectedSmokeStatus.BLOCKED_RATE_LIMIT,
        AdapterFailureCode.BLOCKED_PROVIDER_UNAVAILABLE: (
            ConnectedSmokeStatus.BLOCKED_PROVIDER_UNAVAILABLE
        ),
        AdapterFailureCode.BLOCKED_MARKET_CALENDAR: (ConnectedSmokeStatus.BLOCKED_MARKET_CALENDAR),
        AdapterFailureCode.FAIL_SCHEMA_DRIFT: ConnectedSmokeStatus.FAIL_SCHEMA_DRIFT,
        AdapterFailureCode.FAIL_DATA_QUALITY: ConnectedSmokeStatus.FAIL_DATA_QUALITY,
        AdapterFailureCode.FAIL_SCOPE_VIOLATION: ConnectedSmokeStatus.FAIL_SCOPE_VIOLATION,
    }
    return mapping.get(code, ConnectedSmokeStatus.FAIL_REQUEST_REJECTED)


def _outcome_for_status(status: ConnectedSmokeStatus) -> ConnectedSmokeOutcome:
    if status is ConnectedSmokeStatus.SKIP_NOT_OPTED_IN:
        return ConnectedSmokeOutcome.SKIP
    if status.value.startswith("BLOCKED_"):
        return ConnectedSmokeOutcome.BLOCKED
    if status.value.startswith("FAIL_"):
        return ConnectedSmokeOutcome.FAIL
    return ConnectedSmokeOutcome.PASS


def _promotion_blockers(status: ConnectedSmokeStatus) -> tuple[str, ...]:
    human_blockers = (
        "human review of connected evidence is required",
        "explicit human promotion approval is required",
    )
    if status is ConnectedSmokeStatus.PASS:
        return human_blockers
    return ("a release-candidate connected smoke PASS is required", *human_blockers)


def _quality_result(status: QualityStatus) -> Literal["PASS", "WARN", "FAIL"]:
    if status is QualityStatus.PASS:
        return "PASS"
    if status is QualityStatus.WARN:
        return "WARN"
    return "FAIL"


def _normalize_clock(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("connected clock must be timezone-aware")
    return value.astimezone(UTC)
