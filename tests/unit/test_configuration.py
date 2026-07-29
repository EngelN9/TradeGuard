"""Unit tests for versioned and redacted configuration."""

from pathlib import Path

import pytest
from pydantic import SecretStr, ValidationError
from tests.factories import event_fields, research_config_paths, research_effective_config

from tradeguard.config.audit import build_configuration_changed_event
from tradeguard.config.loader import ConfigurationLoadError, load_effective_config
from tradeguard.config.models import (
    EffectiveConfig,
    RiskSettings,
    SecretSettings,
    deterministic_config_hash,
    inspect_effective_config,
    make_effective_config,
)
from tradeguard.runtime import RuntimeEnvironment


@pytest.mark.unit
@pytest.mark.parametrize("environment", list(RuntimeEnvironment))
def test_every_supported_environment_layer_validates(environment: RuntimeEnvironment) -> None:
    paths = list(research_config_paths())
    paths[1] = paths[1].with_name(f"{environment.value}.yaml")

    effective = load_effective_config(paths)

    assert effective.config.environment.name is environment


@pytest.mark.unit
def test_reviewed_configuration_layers_load_deterministically() -> None:
    first = research_effective_config()
    second = load_effective_config(research_config_paths())

    assert first == second
    assert first.config.environment.name is RuntimeEnvironment.RESEARCH
    assert first.config.venue.supports_order_submission is False
    assert first.config.risk.fail_closed is True
    assert len(first.config_hash) == 64


@pytest.mark.unit
def test_secret_redaction_is_complete_and_hash_is_credential_independent() -> None:
    original = research_effective_config()
    first_config = original.config.model_copy(
        update={"secrets": SecretSettings(provider_api_key=SecretStr("first-secret-value"))}
    )
    second_config = original.config.model_copy(
        update={"secrets": SecretSettings(provider_api_key=SecretStr("second-secret-value"))}
    )
    first = make_effective_config(first_config, sources=original.sources)
    second = make_effective_config(second_config, sources=original.sources)
    inspection = inspect_effective_config(first)
    rendered = str(inspection)

    assert "first-secret-value" not in rendered
    assert "<redacted>" in rendered
    assert first.config_hash == second.config_hash
    assert deterministic_config_hash(first_config) == deterministic_config_hash(second_config)


@pytest.mark.unit
def test_invalid_yaml_or_environment_fails_closed(tmp_path: Path) -> None:
    invalid_yaml = tmp_path / "unsafe.yaml"
    invalid_yaml.write_text("environment:\n  name: live\n", encoding="utf-8")

    with pytest.raises(ConfigurationLoadError, match="validation failed"):
        load_effective_config((*research_config_paths(), invalid_yaml))

    unsafe_tag = tmp_path / "tag.yaml"
    unsafe_tag.write_text("!!python/object/apply:os.system ['echo unsafe']\n", encoding="utf-8")
    with pytest.raises(ConfigurationLoadError, match="unable to load"):
        load_effective_config((unsafe_tag,))

    scalar = tmp_path / "scalar.yaml"
    scalar.write_text("not-a-mapping\n", encoding="utf-8")
    with pytest.raises(ConfigurationLoadError, match="must contain a mapping"):
        load_effective_config((scalar,))

    with pytest.raises(ConfigurationLoadError, match="at least one"):
        load_effective_config(())


@pytest.mark.unit
def test_configuration_rejects_binary_float_at_authority_boundary() -> None:
    config = research_effective_config().config.model_dump(mode="python")
    config["portfolio"]["initial_cash"] = 100000.0  # type: ignore[index]

    with pytest.raises(ValidationError, match="binary floats"):
        type(research_effective_config().config).model_validate(config)


@pytest.mark.unit
def test_configuration_change_event_contains_hashes_not_secrets() -> None:
    before = research_effective_config()
    changed_config = before.config.model_copy(
        update={"alerting": before.config.alerting.model_copy(update={"minimum_severity": "error"})}
    )
    after = make_effective_config(changed_config, sources=before.sources)

    event = build_configuration_changed_event(
        before=before,
        after=after,
        changed_by="maintainer",
        reason="raise minimum alert severity",
        event_fields=event_fields(),
    )

    assert event.before_hash == before.config_hash
    assert event.after_hash == after.config_hash
    assert event.before_hash != event.after_hash


@pytest.mark.unit
def test_risk_hierarchy_and_effective_hash_fail_closed() -> None:
    with pytest.raises(ValidationError, match="single-asset exposure"):
        RiskSettings(
            max_gross_exposure="0.5",
            max_single_asset_exposure="0.6",
            stale_data_seconds=300,
        )

    effective = research_effective_config()
    with pytest.raises(ValidationError, match="config_hash"):
        EffectiveConfig(
            config=effective.config,
            config_hash="0" * 64,
            sources=effective.sources,
        )
