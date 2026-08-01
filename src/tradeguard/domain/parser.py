"""Fail-closed event parsing with explicit legacy migration registration."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from types import MappingProxyType

from pydantic import TypeAdapter

from tradeguard.domain.events import (
    CURRENT_EVENT_SCHEMA_VERSION,
    AnyDomainEvent,
)

EventMigration = Callable[[Mapping[str, object]], Mapping[str, object]]
MigrationKey = tuple[str, str]
EVENT_ADAPTER: TypeAdapter[AnyDomainEvent] = TypeAdapter(AnyDomainEvent)


class UnsupportedEventSchemaError(ValueError):
    """Raised when no reviewed migration exists for an event schema."""


class EventParser:
    """Parse current events or explicitly registered legacy migrations."""

    def __init__(
        self,
        migrations: Mapping[MigrationKey, EventMigration] | None = None,
    ) -> None:
        self._migrations = MappingProxyType(dict(migrations or {}))

    def parse(self, value: Mapping[str, object]) -> AnyDomainEvent:
        """Parse an event, failing closed on unknown or unreviewed versions."""

        schema_version = value.get("schema_version")
        event_type = value.get("event_type")
        if not isinstance(schema_version, str) or not isinstance(event_type, str):
            raise UnsupportedEventSchemaError("event_type and schema_version are required")

        candidate: Mapping[str, object] = value
        if schema_version != CURRENT_EVENT_SCHEMA_VERSION:
            migration = self._migrations.get((event_type, schema_version))
            if migration is None:
                raise UnsupportedEventSchemaError(
                    f"unsupported event schema: {event_type}@{schema_version}"
                )
            candidate = migration(value)
            if candidate.get("schema_version") != CURRENT_EVENT_SCHEMA_VERSION:
                raise UnsupportedEventSchemaError(
                    "registered migration did not produce the current schema version"
                )

        return EVENT_ADAPTER.validate_python(candidate)
