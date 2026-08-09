"""CLI tests for backtest run/inspect and replay run."""

import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from tests.backtest_factories import crypto_order, fixed_environment, plan

from tradeguard.backtest import cli as backtest_cli
from tradeguard.backtest.models import BacktestArtifact
from tradeguard.cli import build_parser, main
from tradeguard.domain.serialization import canonicalize
from tradeguard.experiments.manifest import RunType

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
DATASET = REPOSITORY_ROOT / "tests" / "fixtures" / "market_data" / "normal.json"


def _write_plan(path: Path, run_type: RunType) -> None:
    value = plan(crypto_order(), run_type=run_type)
    path.write_text(json.dumps(canonicalize(value)), encoding="utf-8")


@pytest.mark.unit
@pytest.mark.parametrize(
    ("command", "run_type"),
    [("backtest", RunType.BACKTEST), ("replay", RunType.REPLAY)],
)
def test_run_commands_write_valid_artifact(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    command: str,
    run_type: RunType,
) -> None:
    plan_path = tmp_path / "plan.json"
    output = tmp_path / "artifact.json"
    _write_plan(plan_path, run_type)
    monkeypatch.setattr(backtest_cli, "_discover_environment", fixed_environment)

    assert main([command, "run", str(DATASET), str(plan_path), str(output)]) == 0
    artifact = BacktestArtifact.model_validate_json(output.read_text(encoding="utf-8"))

    assert artifact.result.run_type is run_type
    assert artifact.result.conservation.conserved is True


@pytest.mark.unit
def test_inspect_prints_safe_summary(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    plan_path = tmp_path / "plan.json"
    output = tmp_path / "artifact.json"
    _write_plan(plan_path, RunType.BACKTEST)
    monkeypatch.setattr(backtest_cli, "_discover_environment", fixed_environment)
    main(["backtest", "run", str(DATASET), str(plan_path), str(output)])
    capsys.readouterr()

    assert main(["backtest", "inspect", str(output)]) == 0
    summary = json.loads(capsys.readouterr().out)
    assert summary["conserved"] is True
    assert summary["fills"] == 1
    assert "result_checksum" in summary


@pytest.mark.unit
def test_cli_rejects_run_type_mismatch(tmp_path: Path) -> None:
    plan_path = tmp_path / "plan.json"
    _write_plan(plan_path, RunType.REPLAY)
    with pytest.raises(ValueError, match="does not match"):
        main(["backtest", "run", str(DATASET), str(plan_path), str(tmp_path / "out.json")])


@pytest.mark.unit
def test_parser_exposes_required_prompt6_commands() -> None:
    parser = build_parser()
    assert parser.parse_args(["backtest", "inspect", "result.json"]).backtest_action == "inspect"
    assert parser.parse_args(["replay", "run", "d.json", "p.json", "o.json"]).replay_action == "run"


@pytest.mark.unit
def test_environment_discovery_fails_closed_without_git(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(backtest_cli.shutil, "which", lambda _name: None)
    with pytest.raises(RuntimeError, match=r"Git and uv\.lock"):
        backtest_cli._discover_environment()


@pytest.mark.unit
def test_environment_discovery_records_git_and_lock(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    outputs = iter(["a" * 40, " M file.py"])
    monkeypatch.setattr(backtest_cli.shutil, "which", lambda _name: "git.exe")
    monkeypatch.setattr(
        backtest_cli.subprocess,
        "run",
        lambda *_args, **_kwargs: SimpleNamespace(stdout=next(outputs)),
    )

    environment = backtest_cli._discover_environment()

    assert environment.git_sha == "a" * 40
    assert environment.dirty_worktree is True
    assert len(environment.dependency_lock_hash) == 64
    assert environment.completed_at is None
