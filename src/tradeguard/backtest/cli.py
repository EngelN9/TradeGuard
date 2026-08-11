"""Offline CLI for deterministic backtest and replay artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import shutil
import subprocess
import sys
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path

from tradeguard.backtest.engine import DeterministicBacktester
from tradeguard.backtest.models import BacktestArtifact, BacktestPlan, RunEnvironment
from tradeguard.data.package import load_dataset_package
from tradeguard.domain.serialization import canonicalize
from tradeguard.experiments.manifest import RunType


def configure_backtest_parsers(
    subcommands: argparse._SubParsersAction[argparse.ArgumentParser],
) -> None:
    """Register the required non-connected backtest/replay command tree."""

    backtest = subcommands.add_parser("backtest", help="deterministic historical simulation")
    backtest_actions = backtest.add_subparsers(dest="backtest_action", required=True)
    _add_run_parser(backtest_actions.add_parser("run"))
    inspect_parser = backtest_actions.add_parser("inspect")
    inspect_parser.add_argument("artifact", type=Path)

    replay = subcommands.add_parser("replay", help="deterministic incident replay")
    replay_actions = replay.add_subparsers(dest="replay_action", required=True)
    _add_run_parser(replay_actions.add_parser("run"))


def _add_run_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("dataset", type=Path)
    parser.add_argument("plan", type=Path)
    parser.add_argument("output", type=Path)


def run_backtest_command(arguments: argparse.Namespace) -> int:
    if arguments.command == "backtest" and arguments.backtest_action == "inspect":
        artifact = BacktestArtifact.model_validate_json(
            arguments.artifact.read_text(encoding="utf-8")
        )
        summary = {
            "conserved": artifact.result.conservation.conserved,
            "fills": len(artifact.result.fills),
            "orders": len(artifact.result.orders),
            "result_checksum": artifact.result.result_checksum,
            "run_id": str(artifact.result.run_id),
            "run_type": artifact.result.run_type.value,
            "warnings": artifact.result.warnings,
        }
        print(json.dumps(canonicalize(summary), indent=2, sort_keys=True))  # noqa: T201
        return 0

    expected_type = RunType.BACKTEST if arguments.command == "backtest" else RunType.REPLAY
    package = load_dataset_package(arguments.dataset)
    plan = BacktestPlan.model_validate_json(arguments.plan.read_text(encoding="utf-8"))
    if plan.run_type is not expected_type:
        raise ValueError("plan run_type does not match the selected CLI command")
    environment = _discover_environment()
    artifact = DeterministicBacktester().run(
        package=package,
        plan=plan,
        environment=environment,
    )
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(
        json.dumps(canonicalize(artifact), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(artifact.result.result_checksum)  # noqa: T201
    return 0


def _discover_environment() -> RunEnvironment:
    repository_root = Path(__file__).resolve().parents[3]
    git_executable = shutil.which("git")
    lockfile = repository_root / "uv.lock"
    if git_executable is None or not lockfile.is_file():
        raise RuntimeError("Git and uv.lock are required to build a truthful run manifest")
    git_sha = _git_output(git_executable, repository_root, ("rev-parse", "HEAD"))
    dirty = bool(_git_output(git_executable, repository_root, ("status", "--porcelain")))
    return RunEnvironment(
        git_sha=git_sha,
        dirty_worktree=dirty,
        python_version=platform.python_version(),
        platform=f"{sys.platform}-{platform.machine()}",
        dependency_lock_hash=hashlib.sha256(lockfile.read_bytes()).hexdigest(),
        started_at=datetime.now(UTC),
    )


def _git_output(executable: str, repository_root: Path, arguments: Sequence[str]) -> str:
    completed = subprocess.run(  # noqa: S603 - executable is resolved with shutil.which
        [executable, "-c", f"safe.directory={repository_root.as_posix()}", *arguments],
        cwd=repository_root,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()
