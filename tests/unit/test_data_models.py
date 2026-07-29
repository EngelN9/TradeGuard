"""Unit tests for canonical market-data and point-in-time contracts."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from pydantic import ValidationError

from tradeguard.data.fixtures import build_fixture
from tradeguard.data.models import (
    InstrumentMetadata,
    MarketSession,
    OHLCVBar,
    Quote,
)


@pytest.mark.unit
def test_instrument_metadata_enforces_point_in_time_knowledge_and_activity() -> None:
    metadata = build_fixture("normal").instrument_metadata[0]
    effective = datetime(2024, 1, 2, tzinfo=UTC)

    assert metadata.is_point_in_time_valid(
        effective_at=effective,
        knowledge_time=datetime(2024, 1, 2, tzinfo=UTC),
    )
    assert not metadata.is_point_in_time_valid(
        effective_at=effective,
        knowledge_time=datetime(2019, 12, 31, tzinfo=UTC),
    )

    delisted = metadata.model_copy(update={"active_to": datetime(2024, 1, 1, tzinfo=UTC)})
    assert not delisted.is_active_at(effective)


@pytest.mark.unit
def test_instrument_metadata_is_immutable_and_market_specific() -> None:
    metadata = build_fixture("normal").instrument_metadata[0]

    with pytest.raises(ValidationError):
        metadata.symbol = "ETH-USD"  # type: ignore[misc]

    invalid = metadata.model_dump(mode="python")
    invalid["currency"] = "USD"
    with pytest.raises(ValidationError, match="crypto metadata requires"):
        InstrumentMetadata.model_validate(invalid)


@pytest.mark.unit
def test_authoritative_values_reject_float_and_naive_datetime() -> None:
    document = build_fixture("normal").instrument_metadata[0].model_dump(mode="python")
    document["tick_size"] = 0.01
    with pytest.raises(ValidationError, match="binary floats"):
        InstrumentMetadata.model_validate(document)

    document = build_fixture("normal").instrument_metadata[0].model_dump(mode="python")
    document["known_at"] = datetime(2024, 1, 1)  # noqa: DTZ001 - negative validation case
    with pytest.raises(ValidationError, match="timezone-aware"):
        InstrumentMetadata.model_validate(document)


@pytest.mark.unit
def test_bar_interval_identity_is_strict_but_bad_ohlc_remains_representable() -> None:
    bar_document = build_fixture("normal").records[0]
    bar = OHLCVBar.model_validate(bar_document)
    assert bar.event_time_utc == bar.interval_end_utc

    invalid_identity = dict(bar_document)
    invalid_identity["event_time_utc"] = (bar.event_time_utc + timedelta(seconds=1)).isoformat()
    invalid_identity["ingest_time_utc"] = invalid_identity["event_time_utc"]
    with pytest.raises(ValidationError, match="must equal interval_end"):
        OHLCVBar.model_validate(invalid_identity)

    bad_ohlc = dict(bar_document)
    bad_ohlc["high_price"] = "1"
    assert OHLCVBar.model_validate(bad_ohlc).high_price == Decimal("1")


@pytest.mark.unit
def test_crossed_quote_remains_available_for_quarantine() -> None:
    normal = build_fixture("normal")
    timestamp = normal.policy.evaluated_at
    quote = Quote(
        source="synthetic",
        asset_class=normal.manifest.asset_class,
        venue="SYNTH-CRYPTO",
        symbol="BTC-USD",
        event_time_utc=timestamp,
        ingest_time_utc=timestamp,
        sequence_number=1,
        bid_price=Decimal("101"),
        ask_price=Decimal("100"),
        bid_quantity=Decimal("1"),
        ask_quantity=Decimal("1"),
        quote_asset="USD",
    )

    assert quote.bid_price > quote.ask_price


@pytest.mark.unit
def test_market_session_uses_half_open_interval() -> None:
    session = build_fixture("stock_split").market_sessions[0]

    assert isinstance(session, MarketSession)
    assert session.contains(session.session_open_utc)
    assert not session.contains(session.session_close_utc)
