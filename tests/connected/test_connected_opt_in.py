"""Connected-test placeholder kept separate from deterministic CI."""

import os

import pytest


@pytest.mark.connected
def test_connected_adapters_are_not_implemented_in_prompt_1() -> None:
    if os.getenv("TRADEGUARD_RUN_CONNECTED") != "1":
        pytest.skip("connected tests require TRADEGUARD_RUN_CONNECTED=1")
    pytest.skip("connected adapters are introduced only after their staged review gates")
