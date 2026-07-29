"""Unit tests for immutable versioned event contracts."""

from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from uuid import UUID

import pytest
from pydantic import SecretStr, ValidationError
from tests.factories import EVENT_TIME, event_fields, quote_event

from tradeguard.domain.events import Bar, MarketSessionChanged, PnLSnapshot, Quote
from tradeguard.domain.parser import EventParser, UnsupportedEventSchemaError
from tradeguard.domain.serialization import (
    CanonicalSerializationError,
    canonical_decimal,
    canonical_json,
    deterministic_checksum,
    validate_decimal_input,
)


@pytest.mark.unit
def test_event_build_is_immutable_and_deterministic() -> None:
    first = quote_event()
    second = quote_event()

    assert first == second
    assert first.payload_checksum == second.payload_checksum
    assert len(first.payload_checksum) == 64
    with pytest.raises(ValidationError):
        first.bid_price = Decimal("1")  # type: ignore[misc]


@pytest.mark.unit
def test_event_parser_rejects_checksum_tampering() -> None:
    payload = quote_event().model_dump(mode="python")
    payload["bid_price"] = Decimal("1")

    with pytest.raises(ValidationError, match="payload_checksum"):
        EventParser().parse(payload)


@pytest.mark.unit
def test_event_parser_requires_registered_legacy_migration() -> None:
    current = quote_event().model_dump(mode="python")
    legacy = {**current, "schema_version": "0.9.0"}

    with pytest.raises(UnsupportedEventSchemaError):
        EventParser().parse(legacy)

    parser = EventParser(
        {
            ("Quote", "0.9.0"): lambda _value: current,
        }
    )
    assert parser.parse(legacy) == quote_event()


@pytest.mark.unit
def test_event_parser_rejects_incomplete_and_bad_migration_output() -> None:
    with pytest.raises(UnsupportedEventSchemaError, match="required"):
        EventParser().parse({"event_type": "Quote"})

    legacy = {**quote_event().model_dump(mode="python"), "schema_version": "0.9.0"}
    parser = EventParser({("Quote", "0.9.0"): lambda value: value})
    with pytest.raises(UnsupportedEventSchemaError, match="current schema"):
        parser.parse(legacy)


@pytest.mark.unit
def test_quote_rejects_crossed_prices_and_binary_floats() -> None:
    with pytest.raises(ValidationError, match="bid_price"):
        Quote.build(
            **event_fields(),
            bid_price=Decimal("2"),
            ask_price=Decimal("1"),
            bid_quantity=Decimal("1"),
            ask_quantity=Decimal("1"),
        )

    with pytest.raises(ValidationError, match="binary floats"):
        Quote.build(
            **event_fields(),
            bid_price=1.0,
            ask_price="2",
            bid_quantity="1",
            ask_quantity="1",
        )


@pytest.mark.unit
def test_event_specific_time_and_numeric_invariants_fail_closed() -> None:
    with pytest.raises(ValidationError, match="high_price"):
        Bar.build(
            **event_fields(),
            interval_seconds=60,
            open_price="10",
            high_price="9",
            low_price="8",
            close_price="10",
            volume="1",
        )

    with pytest.raises(ValidationError, match="session_close_utc"):
        MarketSessionChanged.build(
            **event_fields(),
            session_status="open",
            session_open_utc=EVENT_TIME,
            session_close_utc=EVENT_TIME - timedelta(seconds=1),
        )

    with pytest.raises(ValidationError, match="total_pnl"):
        PnLSnapshot.build(
            **event_fields(),
            realized_pnl="1",
            unrealized_pnl="2",
            total_pnl="4",
        )


@pytest.mark.unit
def test_canonical_serialization_rejects_float_and_sorts_keys() -> None:
    assert canonical_json({"b": 2, "a": Decimal("1.00")}) == '{"a":"1","b":2}'
    assert deterministic_checksum({"a": 1}) == deterministic_checksum({"a": 1})
    with pytest.raises(CanonicalSerializationError, match="binary floats"):
        canonical_json({"unsafe": 1.1})


@pytest.mark.unit
def test_canonical_serialization_covers_supported_boundary_types() -> None:
    value = {
        "date": date(2024, 1, 2),
        "secret": SecretStr("must-not-appear"),
        "set": {"b", "a"},
        "uuid": UUID("00000000-0000-4000-8000-000000000001"),
        "zero": Decimal("-0.00"),
        "time": datetime(2024, 1, 2, 1, tzinfo=UTC),
    }
    rendered = canonical_json(value)

    assert "must-not-appear" not in rendered
    assert "<redacted>" in rendered
    assert canonical_decimal(Decimal("-0.00")) == "0"
    with pytest.raises(ValueError, match="finite"):
        validate_decimal_input("NaN")
    with pytest.raises(ValueError, match="invalid"):
        validate_decimal_input("not-a-decimal")
    with pytest.raises(CanonicalSerializationError, match="mapping keys"):
        canonical_json({1: "unsafe"})
    with pytest.raises(CanonicalSerializationError, match="unsupported"):
        canonical_json(object())
