"""R4 strategy-to-R3-result integration tests."""

import json
from pathlib import Path

import pytest
from tests.strategy_factories import (
    NORMAL_FIXTURE,
    strategy_artifact,
    strategy_environment,
    strategy_request,
)

from tradeguard.cli import main
from tradeguard.strategies import cli as strategy_cli
from tradeguard.strategies.models import StrategyRunArtifact


@pytest.mark.integration
def test_strategy_pipeline_binds_outputs_plan_and_r3_result() -> None:
    artifact = strategy_artifact()

    assert artifact.plan.strategy_version == artifact.strategy_version_hash
    assert artifact.backtest.result.run_identity.strategy_version == artifact.strategy_version_hash
    assert artifact.backtest.result.plan_checksum == artifact.plan.checksum()
    assert artifact.report.backtest_result_checksum == artifact.backtest.result.result_checksum
    assert artifact.backtest.result.conservation.conserved is True
    assert len(artifact.backtest.result.fills) == 1


@pytest.mark.integration
def test_strategy_cli_run_and_inspect(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    request_path = tmp_path / "request.json"
    output = tmp_path / "artifact.json"
    request_path.write_text(strategy_request().model_dump_json(), encoding="utf-8")
    monkeypatch.setattr(strategy_cli, "_discover_environment", strategy_environment)

    assert main(["strategy", "run", str(NORMAL_FIXTURE), str(request_path), str(output)]) == 0
    artifact = StrategyRunArtifact.model_validate_json(output.read_text(encoding="utf-8"))
    assert artifact.synthetic_only is True
    capsys.readouterr()

    assert main(["strategy", "inspect", str(output)]) == 0
    summary = json.loads(capsys.readouterr().out)
    assert summary["synthetic_only"] is True
    assert summary["promotion_status"] == "NOT_EVALUATED"
    assert "not investment advice" in summary["warning"]


@pytest.mark.integration
def test_strategy_cli_rejection_leaves_no_output(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    request_path = tmp_path / "request.json"
    request_path.write_text(strategy_request().model_dump_json(), encoding="utf-8")
    output = tmp_path / "artifact.json"
    equity = Path(__file__).parents[1] / "fixtures" / "market_data" / "stock_split.json"

    assert main(["strategy", "run", str(equity), str(request_path), str(output)]) == 2
    assert not output.exists()
    assert "failed closed" in capsys.readouterr().err


@pytest.mark.integration
def test_strategy_cli_rejects_unknown_strategy_without_output(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    request_path = tmp_path / "request.json"
    request_path.write_text(
        '{"run_id":"00000000-0000-4000-8000-000000000070","strategy_id":"unknown"}',
        encoding="utf-8",
    )
    output = tmp_path / "artifact.json"

    assert main(["strategy", "run", str(NORMAL_FIXTURE), str(request_path), str(output)]) == 2
    assert not output.exists()
    assert "failed closed" in capsys.readouterr().err
