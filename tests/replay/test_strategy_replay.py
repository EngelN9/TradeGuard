"""Deterministic replay and artifact-binding tests for R4."""

import pytest
from pydantic import ValidationError
from tests.strategy_factories import strategy_artifact

from tradeguard.domain.serialization import deterministic_checksum
from tradeguard.strategies.models import StrategyRunArtifact


@pytest.mark.replay
def test_strategy_outputs_plan_result_and_report_replay_identically() -> None:
    first = strategy_artifact()
    second = strategy_artifact()

    assert first.strategy_version_hash == second.strategy_version_hash
    assert [output.payload_checksum for output in first.outputs] == [
        output.payload_checksum for output in second.outputs
    ]
    assert first.plan.checksum() == second.plan.checksum()
    assert first.backtest.result.result_checksum == second.backtest.result.result_checksum
    assert first.report.report_checksum == second.report.report_checksum
    assert first.artifact_checksum == second.artifact_checksum


@pytest.mark.replay
def test_direct_and_recomputed_strategy_artifact_tampering_are_rejected() -> None:
    artifact = strategy_artifact()
    direct = artifact.model_dump(mode="python")
    direct["artifact_checksum"] = "f" * 64
    with pytest.raises(ValidationError, match="artifact_checksum"):
        StrategyRunArtifact.model_validate(direct)

    semantic = artifact.model_dump(mode="python")
    semantic["specification"]["strategy_version"] = "1.0.1"
    semantic["artifact_checksum"] = deterministic_checksum(
        {key: value for key, value in semantic.items() if key != "artifact_checksum"}
    )
    with pytest.raises(ValidationError, match="strategy version hash"):
        StrategyRunArtifact.model_validate(semantic)
