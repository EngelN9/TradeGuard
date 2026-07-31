"""Manually opted-in Coinbase public REST/WebSocket smoke outside default CI."""

import os
from pathlib import Path

import pytest

from tradeguard.adapters.crypto.configuration import load_release_configuration
from tradeguard.adapters.crypto.connected import (
    RUN_CONNECTED_VARIABLE,
    ConnectedSmokeStatus,
    run_connected_smoke,
)

ROOT = Path(__file__).resolve().parents[2]
CONFIGURATION_PATH = ROOT / "configs" / "adapters" / "coinbase_crypto.json"


@pytest.mark.connected
def test_coinbase_connected_smoke_requires_explicit_opt_in() -> None:
    if os.getenv(RUN_CONNECTED_VARIABLE) != "1":
        pytest.skip(f"connected tests require {RUN_CONNECTED_VARIABLE}=1")
    result = run_connected_smoke(
        environment=os.environ,
        release_configuration=load_release_configuration(CONFIGURATION_PATH),
    )
    assert result.status is ConnectedSmokeStatus.PASS, result.model_dump_json()
