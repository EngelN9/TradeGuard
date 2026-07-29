"""Strict versioned configuration models and redacted inspection."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, SecretStr, model_validator

from tradeguard.domain.events import AssetClass
from tradeguard.domain.serialization import AuthorityDecimal, canonicalize, deterministic_checksum
from tradeguard.runtime import RuntimeEnvironment

CONFIG_SCHEMA_VERSION = "1.0.0"
NonEmptyText = Annotated[str, Field(min_length=1, max_length=512)]
NonNegativeDecimal = Annotated[AuthorityDecimal, Field(ge=0)]
PositiveDecimal = Annotated[AuthorityDecimal, Field(gt=0)]
UnitIntervalDecimal = Annotated[AuthorityDecimal, Field(ge=0, le=1)]
HashValue = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]


class ConfigModel(BaseModel):
    """Immutable strict configuration base."""

    model_config = ConfigDict(frozen=True, extra="forbid", validate_default=True)


class BaseSettings(ConfigModel):
    application_name: Literal["TradeGuard"] = "TradeGuard"
    default_environment: Literal[RuntimeEnvironment.RESEARCH] = RuntimeEnvironment.RESEARCH
    timezone: Literal["UTC"] = "UTC"


class EnvironmentSettings(ConfigModel):
    name: RuntimeEnvironment


class MarketSettings(ConfigModel):
    asset_class: Literal[AssetClass.EQUITY, AssetClass.CRYPTO]
    timezone: NonEmptyText
    session_calendar: str | None = None
    quote_asset: str | None = None


class VenueSettings(ConfigModel):
    name: NonEmptyText
    read_only: Literal[True] = True
    supports_order_submission: Literal[False] = False


class DataSettings(ConfigModel):
    source: NonEmptyText
    schema_version: NonEmptyText
    max_staleness_seconds: Annotated[int, Field(ge=0)]
    fail_on_quality_error: Literal[True] = True


class StrategySettings(ConfigModel):
    strategy_id: NonEmptyText
    strategy_version: NonEmptyText
    enabled: bool = False
    parameters: dict[str, str | int | bool | None] = Field(default_factory=dict)


class PortfolioSettings(ConfigModel):
    base_currency: NonEmptyText
    initial_cash: PositiveDecimal
    max_leverage: UnitIntervalDecimal


class RiskSettings(ConfigModel):
    fail_closed: Literal[True] = True
    max_gross_exposure: UnitIntervalDecimal
    max_single_asset_exposure: UnitIntervalDecimal
    stale_data_seconds: Annotated[int, Field(gt=0)]

    @model_validator(mode="after")
    def validate_exposure_hierarchy(self) -> RiskSettings:
        if self.max_single_asset_exposure > self.max_gross_exposure:
            raise ValueError("single-asset exposure must not exceed gross exposure")
        return self


class CostSettings(ConfigModel):
    model_version: NonEmptyText
    commission_rate: NonNegativeDecimal
    slippage_rate: NonNegativeDecimal
    unmodeled_cost_warning: Literal[True] = True


class MonitoringSettings(ConfigModel):
    health_interval_seconds: Annotated[int, Field(gt=0)]
    data_freshness_seconds: Annotated[int, Field(gt=0)]


class AlertingSettings(ConfigModel):
    enabled: bool
    minimum_severity: Literal["info", "warning", "error", "critical"]


class SecretSettings(ConfigModel):
    """Optional credentials excluded from hashes by deterministic redaction."""

    provider_api_key: SecretStr | None = None
    account_read_token: SecretStr | None = None


class TradeGuardConfig(ConfigModel):
    """Complete merged configuration inspected before any process starts."""

    schema_version: Literal["1.0.0"] = "1.0.0"
    base: BaseSettings
    environment: EnvironmentSettings
    market: MarketSettings
    venue: VenueSettings
    data: DataSettings
    strategy: StrategySettings
    portfolio: PortfolioSettings
    risk: RiskSettings
    cost: CostSettings
    monitoring: MonitoringSettings
    alerting: AlertingSettings
    secrets: SecretSettings = Field(default_factory=SecretSettings)

    @model_validator(mode="after")
    def validate_non_live_boundary(self) -> TradeGuardConfig:
        if self.venue.supports_order_submission:
            raise ValueError("order submission is prohibited by the v0.1.0 configuration contract")
        return self


def _redact(value: object) -> object:
    if isinstance(value, SecretStr):
        return "<redacted>"
    if isinstance(value, BaseModel):
        return {name: _redact(item) for name, item in value.__dict__.items()}
    if isinstance(value, Mapping):
        return {str(key): _redact(item) for key, item in value.items()}
    if isinstance(value, tuple | list):
        return [_redact(item) for item in value]
    return canonicalize(value)


def redacted_config(config: TradeGuardConfig) -> dict[str, object]:
    """Return a complete effective configuration with all secret values redacted."""

    redacted = _redact(config)
    if not isinstance(redacted, dict):
        raise TypeError("redacted configuration must be a mapping")
    return redacted


def deterministic_config_hash(config: TradeGuardConfig) -> str:
    """Hash the redacted effective configuration without credential influence."""

    return deterministic_checksum(redacted_config(config))


class EffectiveConfig(ConfigModel):
    """Validated effective configuration plus provenance and deterministic hash."""

    config: TradeGuardConfig
    config_hash: HashValue
    sources: tuple[NonEmptyText, ...]

    @model_validator(mode="after")
    def validate_hash(self) -> EffectiveConfig:
        if self.config_hash != deterministic_config_hash(self.config):
            raise ValueError("config_hash does not match the effective configuration")
        return self


def make_effective_config(config: TradeGuardConfig, *, sources: tuple[str, ...]) -> EffectiveConfig:
    """Create an effective configuration record from reviewed sources."""

    return EffectiveConfig(
        config=config,
        config_hash=deterministic_config_hash(config),
        sources=sources,
    )


def inspect_effective_config(effective: EffectiveConfig) -> dict[str, object]:
    """Return a redacted, reviewable effective-configuration document."""

    return {
        "schema_version": effective.config.schema_version,
        "config_hash": effective.config_hash,
        "sources": list(effective.sources),
        "effective_config": redacted_config(effective.config),
    }
