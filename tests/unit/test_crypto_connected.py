"""Offline state tests for the opt-in Coinbase connected qualification."""

from __future__ import annotations

import json
from collections.abc import Iterable
from datetime import UTC, datetime
from pathlib import Path

import pytest

from tradeguard.adapters.crypto.configuration import load_release_configuration
from tradeguard.adapters.crypto.connected import (
    RUN_CONNECTED_VARIABLE,
    ConnectedSmokeOutcome,
    ConnectedSmokeStatus,
    CryptoConnectedSmokeResult,
    run_connected_smoke,
)
from tradeguard.adapters.crypto.stream import (
    WebSocketConnection,
    WebSocketConnector,
    WebSocketTransportError,
)
from tradeguard.adapters.crypto.transport import RestRequest, RestResponse, RestTransport

ROOT = Path(__file__).resolve().parents[2]
FIXTURE_ROOT = ROOT / "tests" / "fixtures" / "adapters" / "coinbase"
CONFIGURATION = load_release_configuration(ROOT / "configs" / "adapters" / "coinbase_crypto.json")
NOW = datetime(2024, 1, 1, 0, 5, tzinfo=UTC)


def _fixture(name: str, key: str = "response") -> object:
    return json.loads((FIXTURE_ROOT / name).read_text(encoding="utf-8"))[key]


def _response(name: str) -> RestResponse:
    return RestResponse(
        status_code=200,
        headers={},
        body=json.dumps(_fixture(name), separators=(",", ":"), sort_keys=True).encode(),
    )


class FakeRestTransport(RestTransport):
    def __init__(self, responses: Iterable[RestResponse]) -> None:
        self._responses = iter(responses)
        self.requests: list[RestRequest] = []

    def send(self, request: RestRequest) -> RestResponse:
        self.requests.append(request)
        return next(self._responses)


class FakeConnection(WebSocketConnection):
    def __init__(self, messages: Iterable[object]) -> None:
        self._messages = iter(messages)
        self.sent: list[str] = []
        self.closed = False

    def send(self, message: str) -> None:
        self.sent.append(message)

    def recv(self, timeout: float) -> str:
        try:
            return json.dumps(next(self._messages), separators=(",", ":"), sort_keys=True)
        except StopIteration:
            raise WebSocketTransportError("fixture exhausted") from None

    def close(self) -> None:
        self.closed = True


class FakeConnector(WebSocketConnector):
    def __init__(self, connection: FakeConnection) -> None:
        self.connection = connection
        self.opened = False

    def open(self, url: str) -> WebSocketConnection:
        assert url == "wss://advanced-trade-ws.coinbase.com"
        self.opened = True
        return self.connection


@pytest.mark.unit
def test_connected_smoke_safe_skip_contacts_nothing() -> None:
    result = run_connected_smoke(
        environment={},
        release_configuration=CONFIGURATION,
        rest_transport=FakeRestTransport(()),
        clock=lambda: NOW,
    )

    assert result.status is ConnectedSmokeStatus.SKIP_NOT_OPTED_IN
    assert result.provider_contacted is False
    assert result.authentication_used is False
    assert result.credential_required is False
    assert result.promotion_gate == "BLOCKED"


@pytest.mark.unit
def test_connected_evidence_model_rejects_inconsistent_states() -> None:
    common = {
        "status": ConnectedSmokeStatus.SKIP_NOT_OPTED_IN,
        "outcome": ConnectedSmokeOutcome.SKIP,
        "reason_code": "fixture",
        "passed": False,
        "provider_contacted": False,
        "observed_at": NOW,
        "rest_health": "NOT_RUN",
        "metadata_status": "NOT_RUN",
        "rest_trade_count": 0,
        "websocket_message_count": 0,
        "websocket_record_count": 0,
        "reconnect_count": 0,
        "sequence_validated": False,
        "clean_shutdown": False,
        "promotion_blockers": ("blocked",),
    }
    with pytest.raises(ValueError, match="passed"):
        CryptoConnectedSmokeResult(**{**common, "passed": True})
    with pytest.raises(ValueError, match="outcome"):
        CryptoConnectedSmokeResult(**{**common, "outcome": ConnectedSmokeOutcome.FAIL})
    with pytest.raises(ValueError, match="uncontacted"):
        CryptoConnectedSmokeResult(**{**common, "rest_trade_count": 1})
    with pytest.raises(ValueError, match="PASS requires"):
        CryptoConnectedSmokeResult(
            **{
                **common,
                "status": ConnectedSmokeStatus.PASS,
                "outcome": ConnectedSmokeOutcome.PASS,
                "passed": True,
                "provider_contacted": True,
            }
        )


@pytest.mark.unit
def test_opted_in_fixture_path_produces_complete_redacted_pass() -> None:
    transport = FakeRestTransport(
        (
            _response("server_time_sanitized.json"),
            _response("product_btc_usd_sanitized.json"),
            _response("product_btc_usd_sanitized.json"),
            _response("ticker_btc_usd_sanitized.json"),
            _response("ticker_btc_usd_sanitized.json"),
            _response("product_btc_usd_sanitized.json"),
        )
    )
    messages = _fixture("websocket_btc_usd_sanitized.json", "messages")
    assert isinstance(messages, list)
    connection = FakeConnection(messages)
    connector = FakeConnector(connection)

    result = run_connected_smoke(
        environment={RUN_CONNECTED_VARIABLE: "1"},
        release_configuration=CONFIGURATION,
        rest_transport=transport,
        websocket_connector=connector,
        clock=lambda: NOW,
    )

    assert result.status is ConnectedSmokeStatus.PASS
    assert result.passed is True
    assert result.provider_contacted is True
    assert result.authentication_used is False
    assert result.rest_health == "HEALTHY"
    assert result.metadata_status == "ONLINE"
    assert result.rest_trade_count == 2
    assert result.websocket_message_count == 4
    assert result.websocket_record_count == 2
    assert result.sequence_validated is True
    assert result.clean_shutdown is True
    assert result.rest_manifest_checksum
    assert result.websocket_manifest_checksum
    assert result.rest_response_bundle_sha256
    assert result.websocket_message_bundle_sha256
    assert result.raw_market_values_persisted is False
    assert result.raw_market_values_published is False
    assert result.promotion_gate == "BLOCKED"
    assert connector.opened is True
    assert connection.closed is True
    assert all("jwt" not in subscription.lower() for subscription in connection.sent)
