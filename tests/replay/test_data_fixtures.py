"""Replay every committed Prompt 3 synthetic fixture deterministically."""

from pathlib import Path

import pytest

from tradeguard.data.fixtures import FIXTURE_SCENARIOS, build_fixture
from tradeguard.data.package import load_dataset_package

FIXTURE_ROOT = Path(__file__).resolve().parents[1] / "fixtures" / "market_data"


@pytest.mark.replay
@pytest.mark.parametrize("scenario", FIXTURE_SCENARIOS)
def test_committed_fixture_replays_to_expected_report(scenario: str) -> None:
    committed = load_dataset_package(FIXTURE_ROOT / f"{scenario}.json")
    generated = build_fixture(scenario)

    assert committed == generated
    assert committed.validate_quality() == generated.validate_quality()
    assert committed.validate_quality().checksum() == generated.validate_quality().checksum()
