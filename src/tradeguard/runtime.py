"""Runtime boundary shared by the bootstrap services."""

from __future__ import annotations

import os
from enum import StrEnum

from pydantic import BaseModel, ConfigDict


class UnsafeEnvironmentError(RuntimeError):
    """Raised when an unsupported environment is requested."""


class RuntimeEnvironment(StrEnum):
    """The complete v0.1.0 environment allowlist."""

    RESEARCH = "research"
    BACKTEST = "backtest"
    REPLAY = "replay"
    PAPER = "paper"
    SHADOW = "shadow"


class HealthResponse(BaseModel):
    """Public health response with no secrets or internal exception data."""

    model_config = ConfigDict(frozen=True)

    status: str
    service: str
    environment: RuntimeEnvironment
    ready: bool


def load_environment(raw_value: str | None = None) -> RuntimeEnvironment:
    """Load and validate the runtime environment, defaulting to research."""

    candidate = raw_value
    if candidate is None:
        candidate = os.getenv("TRADEGUARD_ENV", RuntimeEnvironment.RESEARCH.value)
    normalized = candidate.strip().lower()
    try:
        return RuntimeEnvironment(normalized)
    except ValueError as exc:
        allowed = ", ".join(environment.value for environment in RuntimeEnvironment)
        message = f"Unsupported TradeGuard environment. Allowed values: {allowed}"
        raise UnsafeEnvironmentError(message) from exc


def health_response(*, service: str, ready: bool) -> HealthResponse:
    """Create a bounded health response for a named service."""

    return HealthResponse(
        status="ok" if ready else "not_ready",
        service=service,
        environment=load_environment(),
        ready=ready,
    )
