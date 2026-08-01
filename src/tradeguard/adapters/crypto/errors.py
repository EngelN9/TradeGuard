"""Redacted, machine-classifiable cryptocurrency-adapter failures."""

from __future__ import annotations

from enum import StrEnum


class CryptoAdapterFailureCode(StrEnum):
    BLOCKED_RATE_LIMIT = "BLOCKED_RATE_LIMIT"
    BLOCKED_PROVIDER_UNAVAILABLE = "BLOCKED_PROVIDER_UNAVAILABLE"
    FAIL_SCHEMA_DRIFT = "FAIL_SCHEMA_DRIFT"
    FAIL_DATA_QUALITY = "FAIL_DATA_QUALITY"
    FAIL_REQUEST_REJECTED = "FAIL_REQUEST_REJECTED"
    FAIL_RESPONSE_TOO_LARGE = "FAIL_RESPONSE_TOO_LARGE"
    FAIL_SCOPE_VIOLATION = "FAIL_SCOPE_VIOLATION"
    FAIL_STREAM_STALE = "FAIL_STREAM_STALE"
    FAIL_SEQUENCE_GAP = "FAIL_SEQUENCE_GAP"
    FAIL_DUPLICATE_SEQUENCE = "FAIL_DUPLICATE_SEQUENCE"
    FAIL_OUT_OF_ORDER = "FAIL_OUT_OF_ORDER"
    FAIL_METADATA_CONFLICT = "FAIL_METADATA_CONFLICT"
    FAIL_RECONNECT_EXHAUSTED = "FAIL_RECONNECT_EXHAUSTED"


class CryptoAdapterError(RuntimeError):
    """Safe adapter error that never contains provider payloads or market values."""

    def __init__(self, code: CryptoAdapterFailureCode, safe_message: str) -> None:
        self.code = code
        super().__init__(f"{code.value}: {safe_message}")


class CryptoScopeViolationError(CryptoAdapterError):
    def __init__(self, safe_message: str) -> None:
        super().__init__(CryptoAdapterFailureCode.FAIL_SCOPE_VIOLATION, safe_message)
