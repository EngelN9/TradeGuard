"""Manually opted-in Twelve Data smoke kept outside deterministic CI."""

import os

import pytest
from scripts.run_twelve_data_connected_smoke import (
    CALENDAR_PATH,
    RELEASE_CONFIGURATION_PATH,
)

from tradeguard.adapters.equity.calendar import (
    MarketCalendarUnavailableError,
    ReviewedCalendarDocument,
)
from tradeguard.adapters.equity.configuration import load_release_configuration
from tradeguard.adapters.equity.connected import (
    RUN_CONNECTED_VARIABLE,
    ConnectedSmokeStatus,
    run_connected_smoke,
)


@pytest.mark.connected
def test_twelve_data_connected_smoke_requires_explicit_opt_in_and_reviewed_calendar() -> None:
    if os.getenv(RUN_CONNECTED_VARIABLE) != "1":
        pytest.skip(f"connected tests require {RUN_CONNECTED_VARIABLE}=1")
    document = ReviewedCalendarDocument.model_validate_json(
        CALENDAR_PATH.read_text(encoding="utf-8")
    )
    try:
        calendar_registry = document.to_registry()
    except MarketCalendarUnavailableError as exc:
        pytest.fail(str(exc))
    result = run_connected_smoke(
        environment=os.environ,
        calendar_registry=calendar_registry,
        release_configuration=load_release_configuration(RELEASE_CONFIGURATION_PATH),
    )
    assert result.status is ConnectedSmokeStatus.PASS, result.model_dump_json()
