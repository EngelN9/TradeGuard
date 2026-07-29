"""Configuration audit-event construction."""

from __future__ import annotations

from tradeguard.config.models import EffectiveConfig
from tradeguard.domain.events import ConfigurationChanged


def build_configuration_changed_event(
    *,
    before: EffectiveConfig,
    after: EffectiveConfig,
    changed_by: str,
    reason: str,
    event_fields: dict[str, object],
) -> ConfigurationChanged:
    """Create an immutable configuration audit event without secret content."""

    return ConfigurationChanged.build(
        **event_fields,
        config_version=after.config.schema_version,
        before_hash=before.config_hash,
        after_hash=after.config_hash,
        changed_by=changed_by,
        reason=reason,
    )
