"""Offline tests for connected opt-in and credential state transitions."""

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from tradeguard.adapters.equity.calendar import (
    DeterministicMicCalendarRegistry,
    fixture_calendar_registry,
)
from tradeguard.adapters.equity.connected import (
    CREDENTIAL_VARIABLE,
    RUN_CONNECTED_VARIABLE,
    ConnectedSmokeStatus,
    run_connected_smoke,
)
from tradeguard.adapters.equity.transport import HttpRequest, HttpResponse

OBSERVED_AT = datetime(2026, 7, 31, 0, 0, tzinfo=UTC)
FIXTURE_PATH = (
    Path(__file__).resolve().parents[1]
    / "fixtures"
    / "adapters"
    / "twelve_data"
    / "time_series_aapl_1day_sanitized.json"
)


class OneResponseTransport:
    def __init__(self, response: HttpResponse) -> None:
        self.response = response
        self.calls = 0

    def send(self, _: HttpRequest) -> HttpResponse:
        self.calls += 1
        return self.response


def _fixture_response(*, status_code: int = 200) -> HttpResponse:
    fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    return HttpResponse(
        status_code=status_code,
        headers={},
        body=json.dumps(fixture["response"]).encode(),
    )


@pytest.mark.unit
def test_connected_smoke_skips_without_opt_in_and_never_contacts_provider() -> None:
    result = run_connected_smoke(
        environment={},
        calendar_registry=DeterministicMicCalendarRegistry(),
        clock=lambda: OBSERVED_AT,
    )

    assert result.status is ConnectedSmokeStatus.SKIP_NOT_OPTED_IN
    assert result.passed is False
    assert result.provider_contacted is False
    assert result.request_attempts == 0
    assert result.raw_payload_published is False


@pytest.mark.unit
def test_connected_smoke_blocks_missing_credential_without_provider_contact() -> None:
    result = run_connected_smoke(
        environment={RUN_CONNECTED_VARIABLE: "1"},
        calendar_registry=DeterministicMicCalendarRegistry(),
        clock=lambda: OBSERVED_AT,
    )

    assert result.status is ConnectedSmokeStatus.BLOCKED_MISSING_CREDENTIAL
    assert result.provider_contacted is False
    assert result.promotion_gate == "BLOCKED"
    assert CREDENTIAL_VARIABLE not in result.model_dump_json()


@pytest.mark.unit
def test_connected_smoke_can_pass_offline_state_machine_but_not_promotion_gate() -> None:
    transport = OneResponseTransport(_fixture_response())
    result = run_connected_smoke(
        environment={
            RUN_CONNECTED_VARIABLE: "1",
            CREDENTIAL_VARIABLE: "fixture-credential",
        },
        calendar_registry=fixture_calendar_registry(),
        transport=transport,
        clock=lambda: datetime(2024, 1, 11, 12, 0, tzinfo=UTC),
    )

    assert result.status is ConnectedSmokeStatus.PASS
    assert result.passed is True
    assert result.provider_contacted is True
    assert result.record_count == 7
    assert result.promotion_gate == "BLOCKED"
    assert transport.calls == 1


@pytest.mark.unit
def test_connected_smoke_preserves_explicit_entitlement_block() -> None:
    transport = OneResponseTransport(_fixture_response(status_code=403))
    result = run_connected_smoke(
        environment={
            RUN_CONNECTED_VARIABLE: "1",
            CREDENTIAL_VARIABLE: "fixture-credential",
        },
        calendar_registry=fixture_calendar_registry(),
        transport=transport,
        clock=lambda: datetime(2024, 1, 11, 12, 0, tzinfo=UTC),
    )

    assert result.status is ConnectedSmokeStatus.BLOCKED_ENTITLEMENT
    assert result.passed is False
    assert result.provider_contacted is True
    assert result.reason_code == "BLOCKED_ENTITLEMENT"
