"""Prompt 3 dataset through Prompt 6 artifact integration."""

import pytest
from tests.backtest_factories import crypto_order, fixed_environment, plan

from tradeguard.backtest.engine import DeterministicBacktester
from tradeguard.backtest.models import BacktestRunIdentity
from tradeguard.data.fixtures import build_fixture


@pytest.mark.integration
def test_validated_dataset_produces_bound_reproducible_artifact() -> None:
    package = build_fixture("normal")
    quality = package.validate_quality()
    artifact = DeterministicBacktester().run(
        package=package,
        plan=plan(crypto_order()),
        environment=fixed_environment(),
    )

    assert quality.admissible_for_validation_evidence is True
    assert artifact.manifest.result_checksum == artifact.result.result_checksum
    assert artifact.manifest.dataset_manifests[0].checksum == package.manifest.checksum()
    assert artifact.result.run_identity == BacktestRunIdentity.from_manifest(artifact.manifest)
    assert artifact.result.ending_currency_balances["USD"] >= 0
