"""Trusted-local strategy protocol without provider or execution access."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from tradeguard.strategies.models import (
    StrategyBar,
    StrategyContext,
    StrategyOutput,
    StrategySpecification,
)


@runtime_checkable
class StrategyProtocol(Protocol):
    """A narrow in-process contract; this is not a Python security sandbox."""

    @property
    def specification(self) -> StrategySpecification:
        """Return the immutable declared strategy contract."""

    def initialize(self, context: StrategyContext) -> None:
        """Initialize from bounded, immutable research context."""

    def on_event(self, event: StrategyBar) -> tuple[StrategyOutput, ...]:
        """Consume one declared completed bar and return bounded outputs."""

    def finalize(self) -> tuple[StrategyOutput, ...]:
        """Return deterministic final outputs, if any."""
