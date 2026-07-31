"""Offline contract qualification for the sanitized Twelve Data response shape."""

from __future__ import annotations

import json
import logging
import traceback
from collections.abc import Iterable
from datetime import UTC, date, datetime
from pathlib import Path

import pytest
from pydantic import SecretStr

from tradeguard.adapters.equity.calendar import fixture_calendar_registry
from tradeguard.adapters.equity.configuration import load_release_configuration
from tradeguard.adapters.equity.errors import (
    AdapterFailureCode,
    EquityAdapterError,
    UnsupportedCapabilityError,
)
from tradeguard.adapters.equity.protocol import EquityMarketDataAdapter, HistoricalBarsRequest
from tradeguard.adapters.equity.transport import HttpRequest, HttpResponse, HttpTransport
from tradeguard.adapters.equity.twelve_data import TwelveDataEquityAdapter
from tradeguard.data.quality import QualityCode, QualityStatus

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
FIXTURE_PATH = (
    REPOSITORY_ROOT
    / "tests"
    / "fixtures"
    / "adapters"
    / "twelve_data"
    / "time_series_aapl_1day_sanitized.json"
)
RELEASE_CONFIGURATION_PATH = REPOSITORY_ROOT / "configs" / "adapters" / "twelve_data_equity.json"
RELEASE_CONFIGURATION = load_release_configuration(RELEASE_CONFIGURATION_PATH)
FIXED_NOW = datetime(2024, 1, 11, 12, 0, tzinfo=UTC)


class FakeTransport(HttpTransport):
    def __init__(self, responses: Iterable[HttpResponse]) -> None:
        self._responses = iter(responses)
        self.requests: list[HttpRequest] = []

    def send(self, request: HttpRequest) -> HttpResponse:
        self.requests.append(request)
        return next(self._responses)


def _fixture_document() -> dict[str, object]:
    value = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _success_response(
    *,
    mutate: object | None = None,
    status_code: int = 200,
) -> HttpResponse:
    document = _fixture_document()["response"]
    if mutate is not None:
        assert callable(mutate)
        mutate(document)
    return HttpResponse(
        status_code=status_code,
        headers={"x-request-id": "fixture-request-001"},
        body=json.dumps(document, sort_keys=True).encode(),
    )


def _adapter(
    transport: HttpTransport,
    *,
    sleeps: list[float] | None = None,
    api_key: str = "fixture-credential",
) -> TwelveDataEquityAdapter:
    return TwelveDataEquityAdapter(
        api_key=SecretStr(api_key),
        calendar_registry=fixture_calendar_registry(),
        release_configuration=RELEASE_CONFIGURATION,
        transport=transport,
        clock=lambda: FIXED_NOW,
        sleeper=(sleeps if sleeps is not None else []).append,
    )


@pytest.mark.contract
def test_sanitized_fixture_is_explicitly_non_distributable_and_synthetic() -> None:
    capture = _fixture_document()["capture"]

    assert capture == {
        "adjustment": "none",
        "fixture_schema_version": "1.0.0",
        "license_reviewed_at": "2026-07-31",
        "raw_payload_published": False,
        "raw_payload_retained": False,
        "redistribution_allowed": False,
        "sanitized": True,
        "source_window_end": "2024-01-10",
        "source_window_start": "2024-01-02",
        "terms_reviewed_version": "2026-01-01",
        "usage_class": "internal_non_display",
        "values_are_deterministic_synthetic": True,
    }


@pytest.mark.contract
def test_adapter_normalizes_fixture_to_canonical_utc_and_manifest(
    caplog: pytest.LogCaptureFixture,
) -> None:
    transport = FakeTransport((_success_response(),))
    adapter = _adapter(transport)

    with caplog.at_level(logging.INFO):
        dataset = adapter.historical_bars(
            HistoricalBarsRequest(
                symbol=" aapl ",
                mic="XNAS",
                start_date=date(2024, 1, 2),
                end_date=date(2024, 1, 10),
            )
        )

    assert isinstance(adapter, EquityMarketDataAdapter)
    assert len(dataset.records) == 7
    assert tuple(record.sequence_number for record in dataset.records) == tuple(range(1, 8))
    assert dataset.records[0].interval_start_utc == datetime(2024, 1, 2, 14, 30, tzinfo=UTC)
    assert dataset.records[-1].interval_end_utc == datetime(2024, 1, 10, 21, 0, tzinfo=UTC)
    assert dataset.manifest.row_count == 7
    assert dataset.manifest.checksums["raw_response_sha256"]
    assert dataset.quality_report.status is QualityStatus.WARN
    assert QualityCode.CORPORATE_ACTIONS_UNSUPPORTED in {
        issue.code for issue in dataset.quality_report.issues
    }
    assert dataset.provider_call.request_id == "fixture-request-001"
    assert dataset.provider_call.raw_payload_published is False

    request = transport.requests[0]
    assert request.url.startswith("https://api.twelvedata.com/time_series?")
    assert "apikey" not in request.url.lower()
    assert "adjust=none" in request.url
    assert "interval=1day" in request.url
    assert request.headers["Authorization"] == "apikey fixture-credential"
    assert "fixture-credential" not in caplog.text


@pytest.mark.contract
def test_capabilities_match_the_approved_restricted_scope() -> None:
    adapter = _adapter(FakeTransport((_success_response(),)))
    capabilities = adapter.capabilities

    assert capabilities.approval_status == "APPROVED_WITH_CONDITIONS"
    assert capabilities.provider == "twelve_data"
    assert capabilities.authenticated is True
    assert capabilities.historical_bars is True
    assert capabilities.latest_bar_or_quote is True
    assert capabilities.instrument_metadata is True
    assert capabilities.real_time == "entitlement_dependent"
    assert capabilities.delayed == "entitlement_dependent"
    assert capabilities.corporate_actions is False
    assert capabilities.consolidated_feed is False
    assert capabilities.nbbo is False
    assert capabilities.full_market_volume is False
    assert capabilities.execution_grade is False
    assert capabilities.public_display is False
    assert capabilities.redistribution is False
    assert capabilities.provider_fallback is False
    assert capabilities.market_calendar_source == "internal_approved_sessions"
    assert capabilities.enabled_paths == ("/time_series",)
    assert capabilities.approved_symbols == ("AAPL",)
    assert RELEASE_CONFIGURATION.account.plan_name == "Basic"
    assert RELEASE_CONFIGURATION.account.account_type == "individual"
    assert RELEASE_CONFIGURATION.api_entitlement.api_credits_per_minute == 8
    assert RELEASE_CONFIGURATION.api_entitlement.daily_credit_limit == 800
    assert RELEASE_CONFIGURATION.model_dump()["api_entitlement"]["symbol_AAPL"] == "allowed"

    with pytest.raises(UnsupportedCapabilityError):
        adapter.corporate_actions(
            "AAPL",
            "XNAS",
            date(2024, 1, 2),
            date(2024, 1, 10),
        )


@pytest.mark.contract
def test_scope_allowlist_rejects_symbol_and_mic_without_network() -> None:
    transport = FakeTransport((_success_response(),))
    adapter = _adapter(transport)

    with pytest.raises(EquityAdapterError) as symbol_error:
        adapter.historical_bars(HistoricalBarsRequest(symbol="MSFT", mic="XNAS"))
    with pytest.raises(EquityAdapterError) as mic_error:
        adapter.historical_bars(HistoricalBarsRequest(symbol="AAPL", mic="XNYS"))

    assert symbol_error.value.code is AdapterFailureCode.FAIL_SCOPE_VIOLATION
    assert mic_error.value.code is AdapterFailureCode.FAIL_SCOPE_VIOLATION
    assert transport.requests == []


@pytest.mark.contract
def test_schema_drift_and_unknown_calendar_fail_closed() -> None:
    def add_unknown_field(document: object) -> None:
        assert isinstance(document, dict)
        document["unexpected"] = "schema-drift"

    drift_adapter = _adapter(FakeTransport((_success_response(mutate=add_unknown_field),)))
    with pytest.raises(EquityAdapterError) as drift_error:
        drift_adapter.historical_bars(HistoricalBarsRequest(symbol="AAPL", mic="XNAS"))
    assert drift_error.value.code is AdapterFailureCode.FAIL_SCHEMA_DRIFT

    def unknown_date(document: object) -> None:
        assert isinstance(document, dict)
        values = document["values"]
        assert isinstance(values, list)
        values[0]["datetime"] = "2024-01-11"

    calendar_adapter = _adapter(FakeTransport((_success_response(mutate=unknown_date),)))
    with pytest.raises(EquityAdapterError) as calendar_error:
        calendar_adapter.historical_bars(HistoricalBarsRequest(symbol="AAPL", mic="XNAS"))
    assert calendar_error.value.code is AdapterFailureCode.BLOCKED_MARKET_CALENDAR

    row_count_adapter = _adapter(FakeTransport((_success_response(),)))
    with pytest.raises(EquityAdapterError) as row_count_error:
        row_count_adapter.historical_bars(
            HistoricalBarsRequest(symbol="AAPL", mic="XNAS", output_size=1)
        )
    assert row_count_error.value.code is AdapterFailureCode.FAIL_SCHEMA_DRIFT


@pytest.mark.contract
def test_unmodeled_discontinuity_is_quarantined() -> None:
    def discontinuity(document: object) -> None:
        assert isinstance(document, dict)
        values = document["values"]
        assert isinstance(values, list)
        target = next(item for item in values if item["datetime"] == "2024-01-08")
        target.update({"open": "50", "low": "49"})

    adapter = _adapter(FakeTransport((_success_response(mutate=discontinuity),)))
    with pytest.raises(EquityAdapterError) as error:
        adapter.historical_bars(HistoricalBarsRequest(symbol="AAPL", mic="XNAS"))

    assert error.value.code is AdapterFailureCode.FAIL_DATA_QUALITY


@pytest.mark.contract
def test_schema_failure_traceback_excludes_raw_provider_values() -> None:
    sensitive_value = "raw-market-value-must-not-escape"

    def invalid_field(document: object) -> None:
        assert isinstance(document, dict)
        values = document["values"]
        assert isinstance(values, list)
        values[0]["close"] = {"sensitive": sensitive_value}

    adapter = _adapter(FakeTransport((_success_response(mutate=invalid_field),)))
    with pytest.raises(EquityAdapterError) as error:
        adapter.historical_bars(HistoricalBarsRequest(symbol="AAPL", mic="XNAS"))

    formatted = "".join(traceback.format_exception(error.value))
    assert error.value.code is AdapterFailureCode.FAIL_SCHEMA_DRIFT
    assert sensitive_value not in formatted


@pytest.mark.contract
@pytest.mark.parametrize(
    ("status_code", "expected_code"),
    [
        (401, AdapterFailureCode.BLOCKED_INVALID_CREDENTIAL),
        (403, AdapterFailureCode.BLOCKED_ENTITLEMENT),
        (500, AdapterFailureCode.BLOCKED_PROVIDER_UNAVAILABLE),
    ],
)
def test_http_statuses_map_to_explicit_blocked_states(
    status_code: int,
    expected_code: AdapterFailureCode,
) -> None:
    response = HttpResponse(status_code=status_code, headers={}, body=b"{}")
    adapter = _adapter(FakeTransport((response,)))

    with pytest.raises(EquityAdapterError) as error:
        adapter.historical_bars(HistoricalBarsRequest(symbol="AAPL", mic="XNAS"))

    assert error.value.code is expected_code
    assert "fixture-credential" not in str(error.value)


@pytest.mark.contract
def test_429_has_exactly_one_bounded_retry() -> None:
    limited = HttpResponse(
        status_code=429,
        headers={"retry-after": "99"},
        body=b'{"status":"error","code":429,"message":"redacted"}',
    )
    transport = FakeTransport((limited, _success_response()))
    sleeps: list[float] = []
    dataset = _adapter(transport, sleeps=sleeps).historical_bars(
        HistoricalBarsRequest(symbol="AAPL", mic="XNAS")
    )

    assert dataset.provider_call.attempts == 2
    assert len(transport.requests) == 2
    assert sleeps == [2.0]

    exhausted_transport = FakeTransport((limited, limited))
    with pytest.raises(EquityAdapterError) as error:
        _adapter(exhausted_transport).historical_bars(
            HistoricalBarsRequest(symbol="AAPL", mic="XNAS")
        )
    assert error.value.code is AdapterFailureCode.BLOCKED_RATE_LIMIT
    assert len(exhausted_transport.requests) == 2
