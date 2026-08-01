"""Paper-broker capability skeleton with no order-submission route."""

from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel, ConfigDict

from tradeguard.api.factory import create_service_app


class PaperBrokerCapabilities(BaseModel):
    """Explicitly bounded capabilities for the bootstrap service."""

    model_config = ConfigDict(frozen=True)

    status: str
    deterministic: bool
    simulated_orders_supported: bool
    external_orders_supported: bool
    live_orders_supported: bool


def create_app() -> FastAPI:
    """Create the internal paper-broker skeleton."""

    application = create_service_app(
        service_name="deterministic-paper-broker",
        title="TradeGuard Deterministic Paper Broker",
    )

    @application.get(
        "/v1/capabilities",
        response_model=PaperBrokerCapabilities,
        tags=["paper"],
    )
    def capabilities() -> PaperBrokerCapabilities:
        return PaperBrokerCapabilities(
            status="skeleton",
            deterministic=True,
            simulated_orders_supported=False,
            external_orders_supported=False,
            live_orders_supported=False,
        )

    return application


app = create_app()
