"""Unit tests for fail-closed runtime configuration."""

import pytest

from tradeguard.runtime import (
    RuntimeEnvironment,
    UnsafeEnvironmentError,
    health_response,
    load_environment,
)


@pytest.mark.unit
def test_environment_defaults_to_research(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("TRADEGUARD_ENV", raising=False)

    assert load_environment() is RuntimeEnvironment.RESEARCH


@pytest.mark.unit
@pytest.mark.parametrize(
    "value",
    ["research", "backtest", "replay", "paper", "shadow", " SHADOW "],
)
def test_supported_environments_are_accepted(value: str) -> None:
    assert load_environment(value).value == value.strip().lower()


@pytest.mark.unit
@pytest.mark.parametrize("value", ["", "development", "production", "canary", "live"])
def test_unsupported_environments_are_rejected(value: str) -> None:
    with pytest.raises(UnsafeEnvironmentError, match="Unsupported TradeGuard environment"):
        load_environment(value)


@pytest.mark.unit
def test_health_response_is_bounded(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TRADEGUARD_ENV", "research")

    result = health_response(service="test", ready=False)

    assert result.model_dump(mode="json") == {
        "status": "not_ready",
        "service": "test",
        "environment": "research",
        "ready": False,
    }
