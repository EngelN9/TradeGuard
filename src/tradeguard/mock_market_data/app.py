"""Deterministic market-data fixture service used by offline development."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from fastapi import FastAPI, Path
from pydantic import BaseModel, ConfigDict

from tradeguard.api.factory import create_service_app


class MockBar(BaseModel):
    """A fixed, non-provider market-data fixture."""

    model_config = ConfigDict(frozen=True)

    symbol: str
    event_time_utc: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal
    source: str


def create_app() -> FastAPI:
    """Create the offline-only mock market-data service."""

    application = create_service_app(
        service_name="mock-market-data",
        title="TradeGuard Mock Market Data",
    )

    @application.get("/v1/mock/bars/{symbol}", response_model=MockBar, tags=["mock"])
    def get_mock_bar(
        symbol: str = Path(pattern=r"^[A-Z0-9][A-Z0-9._-]{0,19}$"),
    ) -> MockBar:
        return MockBar(
            symbol=symbol,
            event_time_utc=datetime.fromisoformat("2024-01-02T21:00:00+00:00"),
            open=Decimal("100.00"),
            high=Decimal("101.00"),
            low=Decimal("99.50"),
            close=Decimal("100.50"),
            volume=Decimal("1000"),
            source="synthetic-bootstrap-fixture",
        )

    return application


app = create_app()
