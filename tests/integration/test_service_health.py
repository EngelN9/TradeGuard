"""Integration tests for the bootstrap services."""

import pytest
from fastapi.testclient import TestClient

from tradeguard.api.app import create_app as create_api_app
from tradeguard.mock_market_data.app import create_app as create_market_app
from tradeguard.paper_broker.app import create_app as create_broker_app


@pytest.mark.integration
@pytest.mark.parametrize(
    ("factory", "service_name"),
    [
        (create_api_app, "tradeguard-api"),
        (create_market_app, "mock-market-data"),
        (create_broker_app, "deterministic-paper-broker"),
    ],
)
def test_services_are_live_and_ready(factory, service_name: str) -> None:  # type: ignore[no-untyped-def]
    client = TestClient(factory())

    for path in ("/health/live", "/health/ready"):
        response = client.get(path)
        assert response.status_code == 200
        assert response.json() == {
            "status": "ok",
            "service": service_name,
            "environment": "research",
            "ready": True,
        }


@pytest.mark.integration
def test_api_discloses_non_live_boundary() -> None:
    response = TestClient(create_api_app()).get("/")

    assert response.status_code == 200
    assert response.json()["maximum_environment"] == "shadow"
    assert response.json()["live_trading_supported"] is False


@pytest.mark.integration
def test_paper_broker_has_no_order_submission_capability() -> None:
    client = TestClient(create_broker_app())

    capabilities = client.get("/v1/capabilities")

    assert capabilities.status_code == 200
    assert capabilities.json() == {
        "status": "skeleton",
        "deterministic": True,
        "simulated_orders_supported": False,
        "external_orders_supported": False,
        "live_orders_supported": False,
    }
    assert client.post("/v1/orders", json={}).status_code == 404
