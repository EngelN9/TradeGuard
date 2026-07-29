"""Unit tests for shared, equity, and crypto fail-closed quality gates."""

from datetime import timedelta
from decimal import Decimal

import pytest
from pydantic import ValidationError

from tradeguard.data.fixtures import FIXTURE_SCENARIOS, build_fixture
from tradeguard.data.models import MarketSession, Quote
from tradeguard.data.quality import (
    QualityCode,
    QualityContext,
    QualityGate,
    QualityReport,
    QualityStatus,
    ValidationEvidenceRejectedError,
    require_validation_evidence_eligible,
)
from tradeguard.domain.serialization import canonicalize

EXPECTED_STATUSES = {
    "normal": QualityStatus.PASS,
    "gap": QualityStatus.FAIL,
    "duplicate": QualityStatus.FAIL,
    "out_of_order": QualityStatus.FAIL,
    "bad_tick": QualityStatus.QUARANTINED,
    "stock_split": QualityStatus.WARN,
    "symbol_change": QualityStatus.PASS,
    "delisting": QualityStatus.QUARANTINED,
    "crypto_maintenance": QualityStatus.FAIL,
    "stale_timestamp": QualityStatus.FAIL,
    "fresh_timestamp_stale_content": QualityStatus.FAIL,
}
EXPECTED_QUALITY_CODES = {
    "missing",
    "duplicate",
    "out_of_order",
    "future_timestamp",
    "stale_content",
    "invalid_ohlc",
    "negative_volume",
    "abnormal_price_jump",
    "inconsistent_schema",
    "symbol_mapping_conflict",
    "trading_session_violation",
    "half_day_handling",
    "corporate_action_mismatch",
    "split_discontinuity",
    "delisted_symbol_handling",
    "point_in_time_universe_violation",
    "crypto_24_7_gap",
    "precision_mismatch",
    "minimum_notional_mismatch",
    "venue_maintenance_interval",
    "bid_greater_than_ask",
    "spread_anomaly",
    "quote_asset_inconsistency",
}


def _codes(report: QualityReport) -> set[QualityCode]:
    return {issue.code for issue in report.issues}


def _evaluate(
    scenario: str,
    *,
    records: tuple[dict[str, object], ...] | None = None,
    context: QualityContext | None = None,
) -> QualityReport:
    package = build_fixture(scenario)
    return QualityGate().validate(
        records or package.records,  # type: ignore[arg-type]
        context or package.quality_context(),
    )


@pytest.mark.unit
@pytest.mark.parametrize("scenario", FIXTURE_SCENARIOS)
def test_required_synthetic_scenarios_have_expected_status(scenario: str) -> None:
    report = build_fixture(scenario).validate_quality()

    assert report.status is EXPECTED_STATUSES[scenario]
    assert report.checksum() == build_fixture(scenario).validate_quality().checksum()


@pytest.mark.unit
def test_required_fixture_codes_are_explicit() -> None:
    assert {code.value for code in QualityCode} == EXPECTED_QUALITY_CODES
    assert {QualityCode.MISSING, QualityCode.CRYPTO_24_7_GAP} <= _codes(_evaluate("gap"))
    assert QualityCode.DUPLICATE in _codes(_evaluate("duplicate"))
    assert QualityCode.OUT_OF_ORDER in _codes(_evaluate("out_of_order"))
    assert {
        QualityCode.PRECISION_MISMATCH,
        QualityCode.MINIMUM_NOTIONAL_MISMATCH,
    } <= _codes(_evaluate("bad_tick"))
    assert QualityCode.ABNORMAL_PRICE_JUMP in _codes(_evaluate("stock_split"))
    assert QualityCode.DELISTED_SYMBOL_HANDLING in _codes(_evaluate("delisting"))
    assert QualityCode.VENUE_MAINTENANCE_INTERVAL in _codes(_evaluate("crypto_maintenance"))
    assert QualityCode.STALE_CONTENT in _codes(_evaluate("stale_timestamp"))
    fresh_stale = _evaluate("fresh_timestamp_stale_content")
    stale_issue = next(
        issue for issue in fresh_stale.issues if issue.code is QualityCode.STALE_CONTENT
    )
    assert stale_issue.context["fresh_ingest"] is True


@pytest.mark.unit
def test_fail_and_quarantined_datasets_cannot_enter_validation_evidence() -> None:
    for scenario in ("normal", "stock_split"):
        package = build_fixture(scenario)
        require_validation_evidence_eligible(package.manifest, package.validate_quality())

    for scenario in ("gap", "bad_tick"):
        package = build_fixture(scenario)
        with pytest.raises(ValidationEvidenceRejectedError):
            require_validation_evidence_eligible(package.manifest, package.validate_quality())

    package = build_fixture("normal")
    other_manifest = package.manifest.model_copy(update={"dataset_version": "2.0.0"})
    with pytest.raises(ValidationEvidenceRejectedError, match="not bound"):
        require_validation_evidence_eligible(other_manifest, package.validate_quality())


@pytest.mark.unit
def test_quality_report_status_is_derived_from_issues() -> None:
    report = build_fixture("gap").validate_quality()
    document = report.model_dump(mode="python")
    document["status"] = QualityStatus.PASS

    with pytest.raises(ValidationError, match="does not match"):
        QualityReport.model_validate(document)


@pytest.mark.unit
def test_shared_gate_detects_future_schema_ohlc_and_volume_failures() -> None:
    package = build_fixture("normal")

    future_records = [dict(record) for record in package.records]
    future_records[1]["event_time_utc"] = (
        package.policy.evaluated_at + timedelta(minutes=1)
    ).isoformat()
    future_records[1]["interval_end_utc"] = future_records[1]["event_time_utc"]
    future_records[1]["ingest_time_utc"] = future_records[1]["event_time_utc"]
    assert QualityCode.FUTURE_TIMESTAMP in _codes(
        _evaluate("normal", records=tuple(future_records))
    )

    bad_schema = [dict(record) for record in package.records]
    del bad_schema[0]["close_price"]
    assert QualityCode.INCONSISTENT_SCHEMA in _codes(_evaluate("normal", records=tuple(bad_schema)))

    binary_float = [dict(record) for record in package.records]
    binary_float[0]["open_price"] = 100.0
    assert QualityCode.INCONSISTENT_SCHEMA in _codes(
        _evaluate("normal", records=tuple(binary_float))
    )

    bad_bar = [dict(record) for record in package.records]
    bad_bar[0]["high_price"] = "1"
    bad_bar[1]["volume"] = "-1"
    bar_codes = _codes(_evaluate("normal", records=tuple(bad_bar)))
    assert {QualityCode.INVALID_OHLC, QualityCode.NEGATIVE_VOLUME} <= bar_codes


@pytest.mark.unit
def test_metadata_conflicts_and_future_knowledge_are_quarantined() -> None:
    package = build_fixture("normal")
    metadata = package.instrument_metadata[0]
    conflicting = metadata.model_copy(
        update={"canonical_symbol": "OTHER/BTC", "metadata_version": "synthetic-v2"}
    )
    conflict_context = package.quality_context().model_copy(
        update={"instrument_metadata": (metadata, conflicting)}
    )
    assert QualityCode.SYMBOL_MAPPING_CONFLICT in _codes(
        _evaluate("normal", context=conflict_context)
    )

    future_metadata = metadata.model_copy(
        update={"known_at": package.policy.knowledge_time_utc + timedelta(days=1)}
    )
    future_context = package.quality_context().model_copy(
        update={"instrument_metadata": (future_metadata,)}
    )
    assert QualityCode.POINT_IN_TIME_UNIVERSE_VIOLATION in _codes(
        _evaluate("normal", context=future_context)
    )


@pytest.mark.unit
def test_equity_session_half_day_and_corporate_action_checks() -> None:
    package = build_fixture("symbol_change")
    no_session_context = package.quality_context().model_copy(update={"market_sessions": ()})
    assert QualityCode.TRADING_SESSION_VIOLATION in _codes(
        _evaluate("symbol_change", context=no_session_context)
    )

    original_session = package.market_sessions[0]
    half_day = MarketSession.model_validate(
        {
            **original_session.model_dump(mode="python"),
            "session_close_utc": original_session.session_close_utc - timedelta(minutes=2),
            "half_day": True,
        }
    )
    half_day_context = package.quality_context().model_copy(update={"market_sessions": (half_day,)})
    assert QualityCode.HALF_DAY_HANDLING in _codes(
        _evaluate("symbol_change", context=half_day_context)
    )

    split = build_fixture("stock_split")
    invalid_action = split.corporate_actions[0].model_copy(update={"ratio": None})
    action_context = split.quality_context().model_copy(
        update={"corporate_actions": (invalid_action,)}
    )
    assert QualityCode.CORPORATE_ACTION_MISMATCH in _codes(
        _evaluate("stock_split", context=action_context)
    )

    discontinuous = [dict(record) for record in split.records]
    discontinuous[1].update(
        {
            "open_price": "80",
            "high_price": "81",
            "low_price": "79",
            "close_price": "80",
        }
    )
    assert QualityCode.SPLIT_DISCONTINUITY in _codes(
        _evaluate("stock_split", records=tuple(discontinuous))
    )


def _quote_document(
    package_name: str,
    *,
    bid: str,
    ask: str,
    quote_asset: str,
) -> dict[str, object]:
    package = build_fixture(package_name)
    timestamp = package.records[0]["event_time_utc"]
    quote = Quote(
        source="synthetic",
        asset_class=package.manifest.asset_class,
        venue="SYNTH-CRYPTO",
        symbol="BTC-USD",
        event_time_utc=timestamp,
        ingest_time_utc=timestamp,
        sequence_number=1,
        bid_price=Decimal(bid),
        ask_price=Decimal(ask),
        bid_quantity=Decimal("1"),
        ask_quantity=Decimal("1"),
        quote_asset=quote_asset,
    )
    document = canonicalize(quote)
    assert isinstance(document, dict)
    return document


@pytest.mark.unit
def test_crypto_quote_checks_are_market_specific() -> None:
    package = build_fixture("normal")

    crossed = (_quote_document("normal", bid="101", ask="100", quote_asset="USD"),)
    crossed_context = package.quality_context()
    assert QualityCode.BID_GREATER_THAN_ASK in _codes(
        _evaluate("normal", records=crossed, context=crossed_context)
    )

    wide = (_quote_document("normal", bid="90", ask="110", quote_asset="USD"),)
    assert QualityCode.SPREAD_ANOMALY in _codes(
        _evaluate("normal", records=wide, context=crossed_context)
    )

    inconsistent = (_quote_document("normal", bid="99", ask="100", quote_asset="USDT"),)
    assert QualityCode.QUOTE_ASSET_INCONSISTENCY in _codes(
        _evaluate("normal", records=inconsistent, context=crossed_context)
    )
