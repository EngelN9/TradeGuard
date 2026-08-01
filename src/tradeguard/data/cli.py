"""Offline-only CLI handlers for dataset validation and inspection."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from pydantic import ValidationError

from tradeguard.data.package import load_dataset_package
from tradeguard.domain.serialization import canonicalize


def configure_data_parser(subcommands: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    """Register the bounded ``tradeguard data`` command surface."""

    data_parser = subcommands.add_parser("data", help="offline dataset tools")
    data_subcommands = data_parser.add_subparsers(dest="data_command", required=True)
    for command in ("validate", "manifest", "inspect"):
        command_parser = data_subcommands.add_parser(command)
        command_parser.add_argument("dataset", type=Path)


def _print_json(value: object) -> None:
    print(  # noqa: T201 - CLI result is intentionally written to stdout
        json.dumps(canonicalize(value), indent=2, sort_keys=True, ensure_ascii=False)
    )


def run_data_command(arguments: argparse.Namespace) -> int:
    """Run one offline data command, returning non-zero on unsafe input."""

    try:
        package = load_dataset_package(arguments.dataset)
        if arguments.data_command == "manifest":
            _print_json(
                {
                    "manifest": package.manifest,
                    "manifest_checksum": package.manifest.checksum(),
                }
            )
            return 0

        report = package.validate_quality()
        if arguments.data_command == "validate":
            _print_json(report)
        else:
            _print_json(
                {
                    "dataset_id": package.manifest.dataset_id,
                    "asset_class": package.manifest.asset_class,
                    "symbols": package.manifest.symbols,
                    "row_count": package.manifest.row_count,
                    "manifest_checksum": package.manifest.checksum(),
                    "lineage_checksum": package.manifest.transformation_graph.checksum(),
                    "quality_status": report.status,
                    "validation_evidence_eligible": report.admissible_for_validation_evidence,
                }
            )
        return 0 if report.admissible_for_validation_evidence else 2
    except (OSError, ValidationError, ValueError) as exc:
        print(  # noqa: T201 - bounded CLI error is intentionally written to stderr
            f"dataset command failed closed: {type(exc).__name__}",
            file=sys.stderr,
        )
        return 2
