"""Minimal command-line entrypoint for bootstrap services."""

from __future__ import annotations

import argparse
from collections.abc import Sequence

import uvicorn

from tradeguard import __version__
from tradeguard.workers.service import run_worker

_SERVICES = {
    "api": ("tradeguard.api.app:app", 8000),
    "mock-market-data": ("tradeguard.mock_market_data.app:app", 8001),
    "paper-broker": ("tradeguard.paper_broker.app:app", 8002),
}


def build_parser() -> argparse.ArgumentParser:
    """Build the explicitly non-live bootstrap CLI."""

    parser = argparse.ArgumentParser(
        prog="tradeguard",
        description="TradeGuard research and paper/shadow monitoring tools",
    )
    parser.add_argument("--version", action="version", version=__version__)
    subcommands = parser.add_subparsers(dest="command", required=True)
    for command in _SERVICES:
        subcommands.add_parser(command)
    subcommands.add_parser("worker")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run a selected bootstrap service."""

    arguments = build_parser().parse_args(argv)
    if arguments.command == "worker":
        return run_worker()

    application, port = _SERVICES[arguments.command]
    uvicorn.run(application, host="0.0.0.0", port=port)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
