"""Contract tests for the bootstrap API surfaces."""

import pytest

from tradeguard.api.app import create_app as create_api_app
from tradeguard.mock_market_data.app import create_app as create_market_app
from tradeguard.paper_broker.app import create_app as create_broker_app


@pytest.mark.contract
@pytest.mark.parametrize(
    ("factory", "required_paths"),
    [
        (create_api_app, {"/", "/health/live", "/health/ready"}),
        (create_market_app, {"/health/live", "/health/ready", "/v1/mock/bars/{symbol}"}),
        (create_broker_app, {"/health/live", "/health/ready", "/v1/capabilities"}),
    ],
)
def test_openapi_contains_only_expected_bootstrap_paths(factory, required_paths) -> None:  # type: ignore[no-untyped-def]
    paths = set(factory().openapi()["paths"])

    assert paths == required_paths
    assert all("live-order" not in path for path in paths)
    assert all("withdraw" not in path for path in paths)
    assert all("transfer" not in path for path in paths)
