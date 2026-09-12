"""Offline CLI for the bounded R4 strategy research slice."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

from pydantic import ValidationError

from tradeguard.backtest.cli import _discover_environment
from tradeguard.data.package import load_dataset_package
from tradeguard.domain.serialization import canonicalize
from tradeguard.strategies.models import StrategyRunArtifact, StrategyRunRequest
from tradeguard.strategies.runner import StrategyRejectedError, StrategyRunner


def configure_strategy_parsers(
    subcommands: argparse._SubParsersAction[argparse.ArgumentParser],
) -> None:
    strategy = subcommands.add_parser(
        "strategy",
        help="trusted-local synthetic strategy research",
    )
    actions = strategy.add_subparsers(dest="strategy_action", required=True)
    run = actions.add_parser("run")
    run.add_argument("dataset", type=Path)
    run.add_argument("request", type=Path)
    run.add_argument("output", type=Path)
    inspect = actions.add_parser("inspect")
    inspect.add_argument("artifact", type=Path)


def run_strategy_command(arguments: argparse.Namespace) -> int:
    try:
        if arguments.strategy_action == "inspect":
            artifact = StrategyRunArtifact.model_validate_json(
                arguments.artifact.read_text(encoding="utf-8")
            )
            summary = {
                "artifact_checksum": artifact.artifact_checksum,
                "backtest_result_checksum": artifact.backtest.result.result_checksum,
                "conserved": artifact.report.conserved,
                "fills": artifact.report.fills,
                "promotion_status": artifact.report.promotion_status,
                "strategy_id": artifact.specification.strategy_id,
                "strategy_version_hash": artifact.strategy_version_hash,
                "synthetic_only": artifact.synthetic_only,
                "warning": artifact.report.warning,
            }
            print(json.dumps(canonicalize(summary), indent=2, sort_keys=True))  # noqa: T201
            return 0

        dataset_bytes = arguments.dataset.read_bytes()
        package = load_dataset_package(arguments.dataset)
        request = StrategyRunRequest.model_validate_json(
            arguments.request.read_text(encoding="utf-8")
        )
        artifact = StrategyRunner().run(
            package=package,
            fixture_file_sha256=hashlib.sha256(dataset_bytes).hexdigest(),
            request=request,
            environment=_discover_environment(),
        )
        arguments.output.parent.mkdir(parents=True, exist_ok=True)
        arguments.output.write_text(
            json.dumps(canonicalize(artifact), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        print(artifact.artifact_checksum)  # noqa: T201
        return 0
    except (OSError, ValidationError, StrategyRejectedError, ValueError) as exc:
        print(f"strategy command failed closed: {exc}", file=sys.stderr)  # noqa: T201
        return 2
