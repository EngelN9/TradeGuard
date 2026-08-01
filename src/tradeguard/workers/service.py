"""Signal-aware worker placeholder without implicit external I/O."""

from __future__ import annotations

import signal
import threading

from tradeguard.runtime import load_environment


def run_worker(*, stop_event: threading.Event | None = None) -> int:
    """Wait for controlled shutdown after validating the environment."""

    load_environment()
    event = stop_event or threading.Event()

    if stop_event is None:
        signal.signal(signal.SIGTERM, lambda *_args: event.set())
        signal.signal(signal.SIGINT, lambda *_args: event.set())

    event.wait()
    return 0
