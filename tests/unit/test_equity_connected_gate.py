"""Offline tests for connected opt-in, review, quality, and redaction gates."""

from __future__ import annotations

import json
from collections.abc import Iterable
from datetime import UTC, datetime
from pathlib import Path

import pytest
from scripts import run_twelve_data_connected_smoke as connected_runner

from tradeguard.adapters.equity.calendar import (
    DeterministicMicCalendarRegistry,
    MarketCalendarUnavailableError,
    ReviewedCalendarDocument,
    fixture_calendar_registry,
)
from tradeguard.adapters.equity.configuration import load_release_configuration
from tradeguard.adapters.equity.connected import (
    CREDENTIAL_VARIABLE,
    RUN_CONNECTED_VARIABLE,
    ConnectedSmokeOutcome,
    ConnectedSmokeStatus,
    run_connected_smoke,
)
from tradeguard.adapters.equity.errors import AdapterFailureCode, EquityAdapterError
from tradeguard.adapters.equity.transport import HttpRequest, HttpResponse

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
OBSERVED_AT = datetime(2026, 7, 31, 0, 0, tzinfo=UTC)
FIXTURE_PATH = (
    REPOSITORY_ROOT
    / "tests"
    / "fixtures"
    / "adapters"
    / "twelve_data"
    / "time_series_aapl_1day_sanitized.json"
)
CALENDAR_PATH = REPOSITORY_ROOT / "configs" / "markets" / "equities_connected_sessions.json"
RELEASE_CONFIGURATION = load_release_configuration(
    REPOSITORY_ROOT / "configs" / "adapters" / "twelve_data_equity.json"
)


class SequencedTransport:
    def __init__(self, responses: Iterable[HttpResponse]) -> None:
        self._responses = iter(responses)
        self.requests: list[HttpRequest] = []

    def send(self, request: HttpRequest) -> HttpResponse:
        self.requests.append(request)
        return next(self._responses)


class FailingTransport:
    def __init__(self, code: AdapterFailureCode) -> None:
        self.code = code
        self.requests: list[HttpRequest] = []

    def send(self, request: HttpRequest) -> HttpResponse:
        self.requests.append(request)
        raise EquityAdapterError(self.code, "safe provider failure")


def _fixture_document() -> dict[str, object]:
    document = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))["response"]
    assert isinstance(document, dict)
    return document


def _fixture_response(
    *,
    status_code: int = 200,
    record_count: int | None = None,
    mutate: object | None = None,
) -> HttpResponse:
    response = _fixture_document()
    if record_count is not None:
        values = response["values"]
        assert isinstance(values, list)
        response["values"] = values[:record_count]
    if mutate is not None:
        assert callable(mutate)
        mutate(response)
    return HttpResponse(
        status_code=status_code,
        headers={"x-request-id": "safe-request-001"},
        body=json.dumps(response).encode(),
    )


def _run(
    *,
    environment: dict[str, str],
    calendar_registry: DeterministicMicCalendarRegistry | None = None,
    transport: object | None = None,
    observed_at: datetime = datetime(2024, 1, 11, 12, 0, tzinfo=UTC),
):
    return run_connected_smoke(
        environment=environment,
        calendar_registry=calendar_registry or fixture_calendar_registry(),
        release_configuration=RELEASE_CONFIGURATION,
        transport=transport,  # type: ignore[arg-type]
        clock=lambda: observed_at,
    )


@pytest.mark.unit
def test_connected_calendar_remains_pending_human_review() -> None:
    document = ReviewedCalendarDocument.model_validate_json(
        CALENDAR_PATH.read_text(encoding="utf-8")
    )

    assert document.status == "PENDING_REVIEW"
    assert document.reviewed_at is None
    assert document.reviewed_by is None
    assert document.sessions == ()
    with pytest.raises(MarketCalendarUnavailableError, match="not approved"):
        document.to_registry()


@pytest.mark.unit
def test_only_explicit_approved_session_document_builds_registry() -> None:
    sessions = fixture_calendar_registry().sessions_between(
        "XNAS",
        datetime(2024, 1, 2, tzinfo=UTC).date(),
        datetime(2024, 1, 10, tzinfo=UTC).date(),
    )
    document = ReviewedCalendarDocument(
        status="APPROVED",
        reviewed_by="human-maintainer",
        reviewed_at=datetime(2026, 7, 31, tzinfo=UTC),
        sessions=sessions,
    )

    registry = document.to_registry()
    assert (
        len(
            registry.sessions_between(
                "XNAS",
                datetime(2024, 1, 2, tzinfo=UTC).date(),
                datetime(2024, 1, 10, tzinfo=UTC).date(),
            )
        )
        == 7
    )


@pytest.mark.unit
def test_pending_sessions_block_runner_before_provider_contact(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    output_path = tmp_path / "connected-smoke-result.json"
    monkeypatch.setattr(connected_runner, "OUTPUT_PATH", output_path)
    monkeypatch.setenv(RUN_CONNECTED_VARIABLE, "1")
    monkeypatch.setenv(CREDENTIAL_VARIABLE, "fixture-credential")

    assert connected_runner.main() == 2
    result = json.loads(output_path.read_text(encoding="utf-8"))
    assert result["status"] == "BLOCKED_MARKET_CALENDAR"
    assert result["provider_contacted"] is False
    assert result["promotion_blockers"][0] == (
        "APPROVED connected-session configuration is missing"
    )


@pytest.mark.unit
def test_connected_smoke_skips_without_opt_in_and_never_contacts_provider() -> None:
    result = _run(
        environment={},
        calendar_registry=DeterministicMicCalendarRegistry(),
    )

    assert result.status is ConnectedSmokeStatus.SKIP_NOT_OPTED_IN
    assert result.outcome is ConnectedSmokeOutcome.SKIP
    assert result.passed is False
    assert result.provider_contacted is False
    assert result.request_attempts == 0
    assert result.raw_market_values_published is False
    assert result.promotion_gate == "BLOCKED"


@pytest.mark.unit
def test_connected_smoke_blocks_missing_credential_without_provider_contact() -> None:
    result = _run(
        environment={RUN_CONNECTED_VARIABLE: "1"},
        calendar_registry=DeterministicMicCalendarRegistry(),
    )

    assert result.status is ConnectedSmokeStatus.BLOCKED_MISSING_CREDENTIAL
    assert result.outcome is ConnectedSmokeOutcome.BLOCKED
    assert result.provider_contacted is False
    assert result.credential_present is False
    assert result.promotion_gate == "BLOCKED"
    assert CREDENTIAL_VARIABLE not in result.model_dump_json()


@pytest.mark.unit
def test_connected_smoke_uses_the_reviewed_aapl_daily_boundary() -> None:
    transport = SequencedTransport((_fixture_response(),))
    result = _run(
        environment={
            RUN_CONNECTED_VARIABLE: "1",
            CREDENTIAL_VARIABLE: "fixture-credential",
        },
        transport=transport,
    )

    assert result.status is ConnectedSmokeStatus.PASS
    assert result.outcome is ConnectedSmokeOutcome.PASS
    assert result.passed is True
    assert result.provider_contacted is True
    assert result.credential_present is True
    assert result.credential_exposed is False
    assert result.completed_session_count == 7
    assert result.manifest_generated is True
    assert result.quality_result == "WARN"
    assert result.provider_fallback_used is False
    assert result.raw_market_values_persisted is False
    assert result.raw_market_values_published is False
    assert result.promotion_gate == "BLOCKED"
    assert result.promotion_blockers == (
        "human review of connected evidence is required",
        "explicit human promotion approval is required",
    )
    assert len(transport.requests) == 1
    request_url = transport.requests[0].url
    assert "symbol=AAPL" in request_url
    assert "interval=1day" in request_url
    assert "outputsize=10" in request_url
    assert "adjust=none" in request_url


@pytest.mark.unit
def test_fewer_than_five_completed_sessions_fails_data_quality() -> None:
    result = _run(
        environment={
            RUN_CONNECTED_VARIABLE: "1",
            CREDENTIAL_VARIABLE: "fixture-credential",
        },
        transport=SequencedTransport((_fixture_response(record_count=4),)),
    )

    assert result.status is ConnectedSmokeStatus.FAIL_DATA_QUALITY
    assert result.outcome is ConnectedSmokeOutcome.FAIL
    assert result.reason_code == "FAIL_INSUFFICIENT_COMPLETED_SESSIONS"
    assert result.completed_session_count == 4
    assert result.passed is False
    assert result.manifest_generated is True


@pytest.mark.unit
def test_unfinished_current_session_is_not_counted() -> None:
    result = _run(
        environment={
            RUN_CONNECTED_VARIABLE: "1",
            CREDENTIAL_VARIABLE: "fixture-credential",
        },
        transport=SequencedTransport((_fixture_response(),)),
        observed_at=datetime(2024, 1, 10, 18, 0, tzinfo=UTC),
    )

    assert result.status is ConnectedSmokeStatus.PASS
    assert result.completed_session_count == 6


@pytest.mark.unit
@pytest.mark.parametrize(
    ("status_code", "expected"),
    [
        (401, ConnectedSmokeStatus.BLOCKED_INVALID_CREDENTIAL),
        (403, ConnectedSmokeStatus.BLOCKED_ENTITLEMENT),
        (500, ConnectedSmokeStatus.BLOCKED_PROVIDER_UNAVAILABLE),
    ],
)
def test_http_failures_map_to_exact_connected_states(
    status_code: int,
    expected: ConnectedSmokeStatus,
) -> None:
    result = _run(
        environment={
            RUN_CONNECTED_VARIABLE: "1",
            CREDENTIAL_VARIABLE: "fixture-credential",
        },
        transport=SequencedTransport((_fixture_response(status_code=status_code),)),
    )

    assert result.status is expected
    assert result.outcome is ConnectedSmokeOutcome.BLOCKED
    assert result.passed is False


@pytest.mark.unit
def test_429_retries_once_then_blocks() -> None:
    limited = _fixture_response(status_code=429)
    transport = SequencedTransport((limited, limited))
    result = _run(
        environment={
            RUN_CONNECTED_VARIABLE: "1",
            CREDENTIAL_VARIABLE: "fixture-credential",
        },
        transport=transport,
    )

    assert result.status is ConnectedSmokeStatus.BLOCKED_RATE_LIMIT
    assert result.request_attempts == 2
    assert len(transport.requests) == 2


@pytest.mark.unit
def test_timeout_maps_to_provider_unavailable() -> None:
    transport = FailingTransport(AdapterFailureCode.BLOCKED_PROVIDER_UNAVAILABLE)
    result = _run(
        environment={
            RUN_CONNECTED_VARIABLE: "1",
            CREDENTIAL_VARIABLE: "fixture-credential",
        },
        transport=transport,
    )

    assert result.status is ConnectedSmokeStatus.BLOCKED_PROVIDER_UNAVAILABLE
    assert len(transport.requests) == 1


@pytest.mark.unit
def test_schema_drift_maps_to_exact_failure() -> None:
    def add_unknown_field(document: object) -> None:
        assert isinstance(document, dict)
        document["unexpected"] = True

    result = _run(
        environment={
            RUN_CONNECTED_VARIABLE: "1",
            CREDENTIAL_VARIABLE: "fixture-credential",
        },
        transport=SequencedTransport((_fixture_response(mutate=add_unknown_field),)),
    )

    assert result.status is ConnectedSmokeStatus.FAIL_SCHEMA_DRIFT
    assert result.outcome is ConnectedSmokeOutcome.FAIL
    assert result.passed is False


@pytest.mark.unit
def test_quality_failure_maps_to_exact_failure() -> None:
    def discontinuity(document: object) -> None:
        assert isinstance(document, dict)
        values = document["values"]
        assert isinstance(values, list)
        target = next(item for item in values if item["datetime"] == "2024-01-08")
        target.update({"open": "50", "low": "49"})

    result = _run(
        environment={
            RUN_CONNECTED_VARIABLE: "1",
            CREDENTIAL_VARIABLE: "fixture-credential",
        },
        transport=SequencedTransport((_fixture_response(mutate=discontinuity),)),
    )

    assert result.status is ConnectedSmokeStatus.FAIL_DATA_QUALITY
    assert result.outcome is ConnectedSmokeOutcome.FAIL
    assert result.passed is False


@pytest.mark.unit
def test_connected_evidence_contains_neither_credential_nor_raw_ohlcv() -> None:
    result = _run(
        environment={
            RUN_CONNECTED_VARIABLE: "1",
            CREDENTIAL_VARIABLE: "fixture-credential",
        },
        transport=SequencedTransport((_fixture_response(),)),
    )
    serialized = result.model_dump_json()
    fixture = _fixture_document()
    values = fixture["values"]
    assert isinstance(values, list)

    assert "fixture-credential" not in serialized
    for row in values:
        for field in ("open", "high", "low", "close", "volume"):
            assert row[field] not in serialized
