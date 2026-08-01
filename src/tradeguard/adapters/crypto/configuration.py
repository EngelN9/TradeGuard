"""Human-reviewed Coinbase Advanced Trade public-data release configuration."""

from __future__ import annotations

from pathlib import Path
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, model_validator

from tradeguard.adapters.crypto.protocol import CryptoAdapterCapabilities


class ReleaseConfigurationModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", validate_default=True)


class ProviderDecision(ReleaseConfigurationModel):
    name: Literal["coinbase_advanced_trade"]
    status: Literal["approved_with_conditions"]
    authentication: Literal["prohibited_for_public_market_data"]
    fallback: Literal["prohibited"]


class RetentionDecision(ReleaseConfigurationModel):
    raw_connected_response: Literal["transient_only"]
    raw_response_publication: Literal["prohibited"]
    sanitized_contract_fixture_allowed: Literal[True]
    synthetic_fixture_allowed: Literal[True]
    checksum_and_manifest_allowed: Literal[True]


class ConnectedSmokeBoundary(ReleaseConfigurationModel):
    product_id: Literal["BTC-USD"]
    rest_trade_limit: Literal[5]
    websocket_minimum_messages: Literal[4]
    websocket_maximum_messages: Literal[20]
    websocket_deadline_seconds: Literal[30]
    maximum_reconnects: Literal[3]
    stale_after_seconds: Literal[5]


class CoinbaseReleaseConfiguration(ReleaseConfigurationModel):
    schema_version: Literal["1.0.0"] = "1.0.0"
    provider: ProviderDecision
    retention: RetentionDecision
    connected_smoke: ConnectedSmokeBoundary
    capabilities: CryptoAdapterCapabilities

    @model_validator(mode="after")
    def validate_consistency(self) -> Self:
        if self.provider.name != self.capabilities.provider:
            raise ValueError("capability provider must match provider decision")
        if self.connected_smoke.product_id not in self.capabilities.approved_pairs:
            raise ValueError("connected product must be capability-approved")
        if (
            self.connected_smoke.websocket_minimum_messages
            > self.connected_smoke.websocket_maximum_messages
        ):
            raise ValueError("minimum WebSocket messages cannot exceed maximum")
        return self


def load_release_configuration(path: Path) -> CoinbaseReleaseConfiguration:
    return CoinbaseReleaseConfiguration.model_validate_json(path.read_text(encoding="utf-8"))
