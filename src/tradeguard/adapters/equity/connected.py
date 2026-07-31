"""Opt-in connected smoke state machine and redacted public evidence model."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from datetime import UTC, datetime
from enum import StrEnum
from typing import Annotated, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, SecretStr, model_validator

from tradeguard.adapters.equity.calendar import DeterministicMicCalendarRegistry
from tradeguard.adapters.equity.errors import AdapterFailureCode, EquityAdapterError
from tradeguard.adapters.equity.protocol import HistoricalBarsRequest
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
    FAIL = "FAIL"
    PASS = "PASS"  # noqa: S105 - qualification state, not a credential


class ConnectedSmokeResult(BaseModel):
    """No-secret, no-market-value connected qualification record."""

    model_config = ConfigDict(frozen=True, extra="forbid", validate_default=True)

    schema_version: Literal["1.0.0"] = "1.0.0"
    provider: Literal["twelve_data"] = "twelve_data"
    status: ConnectedSmokeStatus
    reason_code: str
    passed: bool
    provider_contacted: bool
    observed_at: UtcDateTime
    request_attempts: Annotated[int, Field(ge=0, le=2)]
    record_count: Annotated[int, Field(ge=0)]
    manifest_checksum: str | None = None
    quality_status: QualityStatus | None = None
    raw_payload_retained: Literal[False] = False
    raw_payload_published: Literal[False] = False
    promotion_gate: Literal["BLOCKED"] = "BLOCKED"
    promotion_blockers: tuple[str, ...] = (
        "exact subscription plan not recorded in ADR",
        "account owner/use classification not recorded in ADR",
        "public-display entitlement not confirmed; public display remains prohibited",
        "release promotion requires a human-reviewed PASS connected observation",
    )

    @model_validator(mode="after")
    def validate_state(self) -> Self:
        if self.passed is not (self.status is ConnectedSmokeStatus.PASS):
            raise ValueError("passed must be true exactly when status is PASS")
        if not self.provider_contacted and self.request_attempts != 0:
            raise ValueError("uncontacted provider cannot have request attempts")
        if self.status is ConnectedSmokeStatus.PASS and (
            not self.provider_contacted
            or self.request_attempts < 1
            or self.record_count < MINIMUM_COMPLETED_SESSIONS
            or self.manifest_checksum is None
            or self.quality_status not in {QualityStatus.PASS, QualityStatus.WARN}
        ):
            raise ValueError("PASS requires complete connected evidence")
        return self


def run_connected_smoke(
    *,
    environment: Mapping[str, str],
    calendar_registry: DeterministicMicCalendarRegistry,
    transport: HttpTransport | None = None,
    clock: Callable[[], datetime] | None = None,
) -> ConnectedSmokeResult:
    """Run at most one logical request, with one internal retry only for HTTP 429."""

    effective_clock = clock or (lambda: datetime.now(UTC))
    observed_at = _normalize_clock(effective_clock())
    if environment.get(RUN_CONNECTED_VARIABLE) != "1":
        return _result(
            status=ConnectedSmokeStatus.SKIP_NOT_OPTED_IN,
            reason_code=ConnectedSmokeStatus.SKIP_NOT_OPTED_IN.value,
            observed_at=observed_at,
            provider_contacted=False,
        )
    credential = environment.get(CREDENTIAL_VARIABLE, "").strip()
    if not credential:
        return _result(
            status=ConnectedSmokeStatus.BLOCKED_MISSING_CREDENTIAL,
            reason_code=ConnectedSmokeStatus.BLOCKED_MISSING_CREDENTIAL.value,
            observed_at=observed_at,
            provider_contacted=False,
        )
    adapter = TwelveDataEquityAdapter(
        api_key=SecretStr(credential),
        calendar_registry=calendar_registry,
        transport=transport,
        clock=lambda: observed_at,
    )
    try:
        dataset = adapter.historical_bars(
            HistoricalBarsRequest(symbol="AAPL", mic="XNAS", output_size=10)
        )
    except EquityAdapterError as exc:
        return _result(
            status=_status_for_failure(exc.code),
            reason_code=exc.code.value,
            observed_at=observed_at,
            provider_contacted=True,
            request_attempts=2 if exc.code is AdapterFailureCode.BLOCKED_RATE_LIMIT else 1,
        )
    if len(dataset.records) < MINIMUM_COMPLETED_SESSIONS:
        return _result(
            status=ConnectedSmokeStatus.FAIL,
            reason_code="FAIL_INSUFFICIENT_COMPLETED_SESSIONS",
            observed_at=observed_at,
            provider_contacted=True,
            request_attempts=dataset.provider_call.attempts,
            record_count=len(dataset.records),
            manifest_checksum=dataset.manifest.checksum(),
            quality_status=dataset.quality_report.status,
        )
    return _result(
        status=ConnectedSmokeStatus.PASS,
        reason_code=ConnectedSmokeStatus.PASS.value,
        observed_at=observed_at,
        provider_contacted=True,
        request_attempts=dataset.provider_call.attempts,
        record_count=len(dataset.records),
        manifest_checksum=dataset.manifest.checksum(),
        quality_status=dataset.quality_report.status,
    )


def _result(  # noqa: PLR0913 - explicit state evidence avoids ambiguous defaults
    *,
    status: ConnectedSmokeStatus,
    reason_code: str,
    observed_at: datetime,
    provider_contacted: bool,
    request_attempts: int = 0,
    record_count: int = 0,
    manifest_checksum: str | None = None,
    quality_status: QualityStatus | None = None,
) -> ConnectedSmokeResult:
    return ConnectedSmokeResult(
        status=status,
        reason_code=reason_code,
        passed=status is ConnectedSmokeStatus.PASS,
        provider_contacted=provider_contacted,
        observed_at=observed_at,
        request_attempts=request_attempts,
        record_count=record_count,
        manifest_checksum=manifest_checksum,
        quality_status=quality_status,
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
    }
    return mapping.get(code, ConnectedSmokeStatus.FAIL)


def _normalize_clock(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("connected clock must be timezone-aware")
    return value.astimezone(UTC)
