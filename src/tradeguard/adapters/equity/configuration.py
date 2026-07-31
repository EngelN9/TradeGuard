"""Human-reviewed release configuration for the Twelve Data adapter."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from tradeguard.adapters.equity.protocol import EquityAdapterCapabilities

PositiveInt = Annotated[int, Field(gt=0)]


class ReleaseConfigurationModel(BaseModel):
    """Strict immutable configuration boundary."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        serialize_by_alias=True,
        validate_default=True,
    )


class ProviderDecision(ReleaseConfigurationModel):
    name: Literal["twelve_data"]
    status: Literal["approved_with_conditions"]
    fallback: Literal["prohibited"]


class AccountDecision(ReleaseConfigurationModel):
    plan_name: Literal["Basic"]
    account_type: Literal["individual"]


class UsageDecision(ReleaseConfigurationModel):
    intended_use: Literal["internal_non_display"]
    approved: Literal[True]


class LicensingDecision(ReleaseConfigurationModel):
    classification: Literal["internal_use_only"]
    redistribution_allowed: Literal[False]
    public_raw_fixture_allowed: Literal[False]


class RetentionDecision(ReleaseConfigurationModel):
    raw_connected_response: Literal["transient_only"]
    raw_response_publication: Literal["prohibited"]
    raw_response_release_evidence: Literal["prohibited"]
    sanitized_contract_fixture_allowed: Literal[True]
    synthetic_fixture_allowed: Literal[True]
    checksum_and_manifest_allowed: Literal[True]


class PublicDisplayDecision(ReleaseConfigurationModel):
    allowed: Literal[False]


class ApiEntitlement(ReleaseConfigurationModel):
    """Reviewed account metadata; provider responses remain authoritative at runtime."""

    api_credits_per_minute: PositiveInt
    daily_credit_limit: PositiveInt
    time_series_endpoint: Literal["allowed"]
    symbol_aapl: Literal["allowed"] = Field(alias="symbol_AAPL")
    interval_1day: Literal["allowed"]
    historical_daily_bars: Literal["allowed"]


class ConnectedSmokeBoundary(ReleaseConfigurationModel):
    provider: Literal["twelve_data"]
    symbol: Literal["AAPL"]
    mic: Literal["XNAS"]
    interval: Literal["1day"]
    outputsize: Annotated[int, Field(ge=1, le=10)]
    adjustment: Literal["none"]
    minimum_completed_sessions: Annotated[int, Field(ge=1, le=10)]


class CorporateActionDecision(ReleaseConfigurationModel):
    corporate_action_retrieval: Literal["unsupported"]
    dividends_endpoint: Literal["disabled"]
    splits_endpoint: Literal["disabled"]
    bar_adjustment: Literal["none"]


class TwelveDataReleaseConfiguration(ReleaseConfigurationModel):
    """Complete reviewed decision record used by adapter and connected tooling."""

    schema_version: Literal["1.0.0"] = "1.0.0"
    provider: ProviderDecision
    account: AccountDecision
    usage: UsageDecision
    licensing: LicensingDecision
    retention: RetentionDecision
    public_display: PublicDisplayDecision
    api_entitlement: ApiEntitlement
    connected_smoke: ConnectedSmokeBoundary
    corporate_actions: CorporateActionDecision
    capabilities: EquityAdapterCapabilities

    @model_validator(mode="after")
    def validate_consistency(self) -> Self:
        if self.connected_smoke.outputsize < self.connected_smoke.minimum_completed_sessions:
            raise ValueError("connected outputsize cannot be below the completed-session minimum")
        if self.connected_smoke.provider != self.provider.name:
            raise ValueError("connected provider must match the approved provider")
        if self.capabilities.provider != self.provider.name:
            raise ValueError("capability provider must match the approved provider")
        if self.connected_smoke.symbol not in self.capabilities.approved_symbols:
            raise ValueError("connected symbol must be capability-approved")
        if self.connected_smoke.mic not in self.capabilities.approved_mics:
            raise ValueError("connected MIC must be capability-approved")
        return self


def load_release_configuration(path: Path) -> TwelveDataReleaseConfiguration:
    """Load the reviewed release configuration from an explicit path."""

    return TwelveDataReleaseConfiguration.model_validate_json(path.read_text(encoding="utf-8"))
