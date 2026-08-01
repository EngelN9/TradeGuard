"""Canonical serialization and authority-boundary validation."""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Mapping, Sequence
from datetime import UTC, date, datetime
from decimal import Decimal, InvalidOperation
from enum import Enum
from typing import Annotated
from uuid import UUID

from pydantic import AfterValidator, BaseModel, BeforeValidator, SecretStr


class CanonicalSerializationError(ValueError):
    """Raised when a value cannot be represented canonically."""


def validate_decimal_input(value: object) -> Decimal:
    """Accept exact Decimal-compatible inputs while rejecting binary floats."""

    if isinstance(value, (bool, float)):
        raise ValueError("authoritative decimal values must not use binary floats")
    try:
        decimal_value = value if isinstance(value, Decimal) else Decimal(value)  # type: ignore[arg-type]
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValueError("invalid authoritative decimal value") from exc
    if not decimal_value.is_finite():
        raise ValueError("authoritative decimal values must be finite")
    return decimal_value


def normalize_utc(value: datetime) -> datetime:
    """Require a timezone-aware datetime and normalize it to UTC."""

    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("datetime must be timezone-aware")
    return value.astimezone(UTC)


AuthorityDecimal = Annotated[Decimal, BeforeValidator(validate_decimal_input)]
UtcDateTime = Annotated[datetime, AfterValidator(normalize_utc)]


def canonical_decimal(value: Decimal) -> str:
    """Return a stable non-exponent decimal representation."""

    if not value.is_finite():
        raise CanonicalSerializationError("non-finite decimals are not canonical")
    if value == 0:
        return "0"
    return format(value.normalize(), "f")


def _canonical_datetime(value: datetime) -> str:
    normalized = normalize_utc(value)
    return normalized.isoformat(timespec="microseconds").replace("+00:00", "Z")


def canonicalize(value: object) -> object:  # noqa: PLR0911, PLR0912
    """Convert supported values to a stable JSON-compatible representation."""

    if isinstance(value, SecretStr):
        return "<redacted>"
    if isinstance(value, BaseModel):
        return canonicalize(value.model_dump(mode="python"))
    if isinstance(value, Enum):
        return canonicalize(value.value)
    if isinstance(value, Decimal):
        return canonical_decimal(value)
    if isinstance(value, datetime):
        return _canonical_datetime(value)
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, UUID):
        return str(value)
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise CanonicalSerializationError("non-finite floats are not canonical")
        raise CanonicalSerializationError("binary floats are prohibited at authority boundaries")
    if isinstance(value, Mapping):
        converted: dict[str, object] = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise CanonicalSerializationError("canonical mapping keys must be strings")
            converted[key] = canonicalize(item)
        return {key: converted[key] for key in sorted(converted)}
    if isinstance(value, (set, frozenset)):
        converted_items = [canonicalize(item) for item in value]
        return sorted(converted_items, key=canonical_json)
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [canonicalize(item) for item in value]
    raise CanonicalSerializationError(f"unsupported canonical type: {type(value).__name__}")


def canonical_json(value: object) -> str:
    """Serialize a value as deterministic UTF-8 JSON text."""

    return json.dumps(
        canonicalize(value),
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    )


def deterministic_checksum(value: object) -> str:
    """Return the SHA-256 checksum of canonical JSON."""

    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()
