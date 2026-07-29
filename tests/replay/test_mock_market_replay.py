"""Replay test for the deterministic bootstrap fixture."""

import pytest
from fastapi.testclient import TestClient

from tradeguard.mock_market_data.app import create_app


@pytest.mark.replay
def test_mock_market_response_replays_identically() -> None:
    client = TestClient(create_app())

    first = client.get("/v1/mock/bars/SPY")
    second = client.get("/v1/mock/bars/SPY")

    assert first.status_code == 200
    assert first.content == second.content
    assert first.json() == {
        "symbol": "SPY",
        "event_time_utc": "2024-01-02T21:00:00Z",
        "open": "100.00",
        "high": "101.00",
        "low": "99.50",
        "close": "100.50",
        "volume": "1000",
        "source": "synthetic-bootstrap-fixture",
    }


@pytest.mark.replay
def test_mock_market_rejects_malicious_symbol_path() -> None:
    response = TestClient(create_app()).get("/v1/mock/bars/..%2F..%2Fsecret")

    assert response.status_code in {404, 422}
