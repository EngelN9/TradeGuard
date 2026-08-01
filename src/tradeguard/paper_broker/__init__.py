"""Deterministic paper-broker bootstrap service."""

from tradeguard.paper_broker.app import app, create_app

__all__ = ["app", "create_app"]
