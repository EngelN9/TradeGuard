"""Unit tests for the bounded command-line surface."""

import pytest

from tradeguard import cli
from tradeguard.cli import build_parser


@pytest.mark.unit
def test_cli_exposes_only_non_live_bootstrap_commands() -> None:
    parser = build_parser()
    help_text = parser.format_help()

    assert "api" in help_text
    assert "worker" in help_text
    assert "mock-market-data" in help_text
    assert "paper-broker" in help_text
    assert "live" not in help_text


@pytest.mark.unit
def test_cli_rejects_live_command() -> None:
    parser = build_parser()

    with pytest.raises(SystemExit):
        parser.parse_args(["live"])


@pytest.mark.unit
def test_cli_routes_api_to_expected_application(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = []
    monkeypatch.setattr(cli.uvicorn, "run", lambda *args, **kwargs: calls.append((args, kwargs)))

    assert cli.main(["api"]) == 0
    assert calls == [
        (
            ("tradeguard.api.app:app",),
            {"host": "0.0.0.0", "port": 8000},  # noqa: S104 - expected container bind
        )
    ]


@pytest.mark.unit
def test_cli_routes_worker_without_starting_external_io(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cli, "run_worker", lambda: 0)

    assert cli.main(["worker"]) == 0
