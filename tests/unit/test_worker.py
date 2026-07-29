"""Unit tests for the worker skeleton."""

import threading

import pytest

from tradeguard.workers import run_worker


@pytest.mark.unit
def test_worker_can_stop_without_external_io(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TRADEGUARD_ENV", "research")
    stop_event = threading.Event()
    stop_event.set()

    assert run_worker(stop_event=stop_event) == 0
