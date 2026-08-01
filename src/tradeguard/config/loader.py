"""Safe deterministic YAML configuration loading."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path

import yaml

from tradeguard.config.models import EffectiveConfig, TradeGuardConfig, make_effective_config


class ConfigurationLoadError(ValueError):
    """Raised when a configuration source cannot be validated."""


def _merge_mappings(
    current: dict[str, object],
    incoming: Mapping[str, object],
) -> dict[str, object]:
    merged = dict(current)
    for key, value in incoming.items():
        existing = merged.get(key)
        if isinstance(existing, dict) and isinstance(value, Mapping):
            merged[key] = _merge_mappings(existing, value)
        else:
            merged[key] = value
    return merged


def load_effective_config(paths: Sequence[Path]) -> EffectiveConfig:
    """Load reviewed YAML layers in order and fail closed on invalid content."""

    if not paths:
        raise ConfigurationLoadError("at least one configuration source is required")

    merged: dict[str, object] = {}
    sources = []
    for path in paths:
        try:
            loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
        except (OSError, yaml.YAMLError) as exc:
            raise ConfigurationLoadError(f"unable to load configuration source: {path}") from exc
        if not isinstance(loaded, Mapping):
            raise ConfigurationLoadError(f"configuration source must contain a mapping: {path}")
        merged = _merge_mappings(merged, loaded)
        sources.append(path.as_posix())

    try:
        config = TradeGuardConfig.model_validate(merged)
    except ValueError as exc:
        raise ConfigurationLoadError("effective configuration validation failed") from exc
    return make_effective_config(config, sources=tuple(sources))
