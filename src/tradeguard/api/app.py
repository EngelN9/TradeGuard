"""Primary TradeGuard API bootstrap application."""

from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel, ConfigDict

from tradeguard.api.factory import create_service_app
from tradeguard.runtime import RuntimeEnvironment, load_environment


class ServiceInfo(BaseModel):
    """Non-sensitive service identity."""

    model_config = ConfigDict(frozen=True)

    name: str
    status: str
    environment: RuntimeEnvironment
    maximum_environment: RuntimeEnvironment
    live_trading_supported: bool


def create_app() -> FastAPI:
    """Create the backend API skeleton."""

    application = create_service_app(
        service_name="tradeguard-api",
        title="TradeGuard API",
    )

    @application.get("/", response_model=ServiceInfo, tags=["system"])
    def service_info() -> ServiceInfo:
        return ServiceInfo(
            name="TradeGuard",
            status="bootstrap",
            environment=load_environment(),
            maximum_environment=RuntimeEnvironment.SHADOW,
            live_trading_supported=False,
        )

    return application


app = create_app()
