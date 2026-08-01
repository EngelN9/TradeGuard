"""Redacted, machine-classifiable equity-adapter failures."""

from __future__ import annotations

from enum import StrEnum


class AdapterFailureCode(StrEnum):
    BLOCKED_INVALID_CREDENTIAL = "BLOCKED_INVALID_CREDENTIAL"
    BLOCKED_ENTITLEMENT = "BLOCKED_ENTITLEMENT"
    BLOCKED_RATE_LIMIT = "BLOCKED_RATE_LIMIT"
    BLOCKED_PROVIDER_UNAVAILABLE = "BLOCKED_PROVIDER_UNAVAILABLE"
    BLOCKED_MARKET_CALENDAR = "BLOCKED_MARKET_CALENDAR"
    FAIL_SCHEMA_DRIFT = "FAIL_SCHEMA_DRIFT"
    FAIL_DATA_QUALITY = "FAIL_DATA_QUALITY"
    FAIL_REQUEST_REJECTED = "FAIL_REQUEST_REJECTED"
    FAIL_RESPONSE_TOO_LARGE = "FAIL_RESPONSE_TOO_LARGE"
    FAIL_UNSUPPORTED_CAPABILITY = "FAIL_UNSUPPORTED_CAPABILITY"
    FAIL_SCOPE_VIOLATION = "FAIL_SCOPE_VIOLATION"


class EquityAdapterError(RuntimeError):
    """Safe adapter error that never contains a credential or raw response."""

    def __init__(self, code: AdapterFailureCode, safe_message: str) -> None:
        self.code = code
        super().__init__(f"{code.value}: {safe_message}")


class UnsupportedCapabilityError(EquityAdapterError):
    def __init__(self, capability: str) -> None:
        super().__init__(
            AdapterFailureCode.FAIL_UNSUPPORTED_CAPABILITY,
            f"{capability} is disabled for the approved v0.1.0 scope",
        )


class ScopeViolationError(EquityAdapterError):
    def __init__(self, safe_message: str) -> None:
        super().__init__(AdapterFailureCode.FAIL_SCOPE_VIOLATION, safe_message)
