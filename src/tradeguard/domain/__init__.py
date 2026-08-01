"""Immutable domain contracts for TradeGuard."""

from tradeguard.domain.events import AnyDomainEvent, DomainEvent
from tradeguard.domain.parser import EventParser, UnsupportedEventSchemaError

__all__ = [
    "AnyDomainEvent",
    "DomainEvent",
    "EventParser",
    "UnsupportedEventSchemaError",
]
