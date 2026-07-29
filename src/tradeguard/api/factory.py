"""Factories for small bootstrap services."""

from __future__ import annotations

from collections.abc import Callable

from fastapi import FastAPI

from tradeguard import __version__
from tradeguard.runtime import HealthResponse, health_response, load_environment

ReadinessCheck = Callable[[], bool]


def create_service_app(
    *,
    service_name: str,
    title: str,
    readiness_check: ReadinessCheck | None = None,
) -> FastAPI:
    """Create a service with consistent fail-closed environment and health routes."""

    environment = load_environment()
    check = readiness_check or (lambda: True)
    application = FastAPI(
        title=title,
        version=__version__,
        docs_url="/docs",
        redoc_url=None,
    )
    application.state.environment = environment
    application.state.service_name = service_name

    @application.get("/health/live", response_model=HealthResponse, tags=["health"])
    def live() -> HealthResponse:
        return health_response(service=service_name, ready=True)

    @application.get("/health/ready", response_model=HealthResponse, tags=["health"])
    def ready() -> HealthResponse:
        return health_response(service=service_name, ready=check())

    return application
