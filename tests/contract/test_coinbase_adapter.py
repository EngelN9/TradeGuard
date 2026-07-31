"""Offline REST contract qualification for Coinbase public market data."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable
from datetime import UTC, datetime
from pathlib import Path

import pytest

from tradeguard.adapters.crypto.coinbase import CoinbaseCryptoMarketDataAdapter
from tradeguard.adapters.crypto.configuration import load_release_configuration
from tradeguard.adapters.crypto.errors import CryptoAdapterError, CryptoAdapterFailureCode
from tradeguard.adapters.crypto.protocol import (
    CryptoBarsRequest,
    CryptoMarketDataAdapter,
    MaintenanceStatus,
    RestHealthState,
    TradingStatus,
)
from tradeguard.adapters.crypto.transport import RestRequest, RestResponse, RestTransport
from tradeguard.data.quality import QualityStatus

ROOT = Path(__file__).resolve().parents[2]
FIXTURE_ROOT = ROOT / "tests" / "fixtures" / "adapters" / "coinbase"
CONFIGURATION = load_release_configuration(ROOT / "configs" / "adapters" / "coinbase_crypto.json")
NOW = datetime(2024, 1, 1, 0, 5, tzinfo=UTC)


class FakeRestTransport(RestTransport):
    def __init__(self, responses: Iterable[RestResponse]) -> None:
        self._responses = iter(responses)
        self.requests: list[RestRequest] = []

    def send(self, request: RestRequest) -> RestResponse:
        self.requests.append(request)
        return next(self._responses)


def _document(name: str) -> dict[str, object]:
    value = json.loads((FIXTURE_ROOT / name).read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _response(name: str, *, status: int = 200) -> RestResponse:
    payload = _document(name)["response"]
    return RestResponse(
        status_code=status,
        headers={"content-type": "application/json"},
        body=json.dumps(payload, separators=(",", ":"), sort_keys=True).encode(),
    )


def _adapter(transport: RestTransport, *, sleeps: list[float] | None = None):
    return CoinbaseCryptoMarketDataAdapter(
        release_configuration=CONFIGURATION,
        rest_transport=transport,
        clock=lambda: NOW,
        sleeper=(sleeps if sleeps is not None else []).append,
    )


@pytest.mark.contract
def test_fixtures_are_synthetic_sanitized_and_non_published() -> None:
    for path in FIXTURE_ROOT.glob("*.json"):
        capture = json.loads(path.read_text(encoding="utf-8"))["capture"]
        assert capture["sanitized"] is True
        assert capture["values_are_deterministic_synthetic"] is True
        assert capture["raw_payload_retained"] is False
        assert capture["raw_payload_published"] is False


@pytest.mark.contract
def test_committed_fixture_checksum_evidence_matches_bytes() -> None:
    evidence = json.loads(
        (ROOT / "artifacts" / "evidence" / "prompt5" / "fixture-checksums.json").read_text(
            encoding="utf-8"
        )
    )
    for relative_path, expected in evidence["fixtures"].items():
        assert hashlib.sha256((ROOT / relative_path).read_bytes()).hexdigest() == expected


@pytest.mark.contract
def test_capabilities_are_public_only_and_protocol_complete() -> None:
    adapter = _adapter(FakeRestTransport(()))

    assert isinstance(adapter, CryptoMarketDataAdapter)
    assert adapter.supported_pairs() == ("BTC-USD",)
    assert adapter.capabilities.public_only is True
    assert adapter.capabilities.authenticated is False
    assert adapter.capabilities.accounts is False
    assert adapter.capabilities.orders is False
    assert adapter.capabilities.transfers is False
    assert adapter.capabilities.withdrawals is False
    assert adapter.capabilities.derivatives is False
    assert adapter.capabilities.leverage is False
    assert adapter.capabilities.provider_fallback is False
    assert adapter.rate_limits.websocket_connections_per_second_per_ip == 8
    assert adapter.rate_limits.websocket_unauthenticated_messages_per_second_per_ip == 8
    assert adapter.rate_limits.reconnect_backoff_seconds == (1.0, 2.0, 4.0)


@pytest.mark.contract
def test_metadata_bars_trades_snapshot_health_and_maintenance_normalize() -> None:
    metadata_transport = FakeRestTransport((_response("product_btc_usd_sanitized.json"),))
    metadata = _adapter(metadata_transport).instrument_metadata(" btc-usd ")
    assert metadata.base_asset == "BTC"
    assert metadata.quote_asset == "USD"
    assert str(metadata.instrument.tick_size) == "0.01"
    assert str(metadata.instrument.step_size) == "1E-8"
    assert str(metadata.instrument.minimum_quantity) == "1E-8"
    assert str(metadata.instrument.minimum_notional) == "1.00"
    assert metadata.trading_status is TradingStatus.ONLINE

    bars_transport = FakeRestTransport(
        (
            _response("product_btc_usd_sanitized.json"),
            _response("candles_btc_usd_sanitized.json"),
        )
    )
    bars = _adapter(bars_transport).historical_bars(
        CryptoBarsRequest(
            start=datetime(2024, 1, 1, 0, 0, tzinfo=UTC),
            end=datetime(2024, 1, 1, 0, 3, tzinfo=UTC),
            limit=3,
        )
    )
    assert len(bars.records) == 3
    assert bars.manifest.row_count == 3
    assert bars.quality_report.status is QualityStatus.PASS
    assert bars.manifest.checksums["raw_response_bundle_sha256"]
    assert all(call.authorization_sent is False for call in bars.provider_calls)
    assert "Authorization" not in bars_transport.requests[0].headers
    assert bars_transport.requests[1].url.endswith(
        "start=1704067200&end=1704067380&granularity=ONE_MINUTE&limit=3"
    )

    trades_transport = FakeRestTransport(
        (
            _response("product_btc_usd_sanitized.json"),
            _response("ticker_btc_usd_sanitized.json"),
        )
    )
    trades = _adapter(trades_transport).public_trades("BTC-USD", limit=2)
    assert len(trades.records) == 2
    assert trades.quality_report.status is QualityStatus.PASS
    assert tuple(record.trade_id for record in trades.records) == (
        "synthetic-trade-001",
        "synthetic-trade-002",
    )

    quote = _adapter(FakeRestTransport((_response("ticker_btc_usd_sanitized.json"),))).best_bid_ask(
        "BTC-USD"
    )
    assert str(quote.bid_price) == "42003.00"
    assert str(quote.ask_price) == "42004.00"
    assert quote.quantity_status == "UNAVAILABLE_FROM_ENDPOINT"

    health = _adapter(FakeRestTransport((_response("server_time_sanitized.json"),))).rest_health()
    assert health.state is RestHealthState.HEALTHY
    assert health.provider_time_utc == NOW

    maintenance = _adapter(
        FakeRestTransport((_response("product_btc_usd_sanitized.json"),))
    ).venue_maintenance_status("BTC-USD")
    assert maintenance.status is MaintenanceStatus.CLEAR
    assert maintenance.trading_status is TradingStatus.ONLINE


@pytest.mark.contract
def test_scope_schema_status_and_rate_limit_fail_closed_without_payload_leak() -> None:
    empty_transport = FakeRestTransport(())
    with pytest.raises(CryptoAdapterError) as scope_error:
        _adapter(empty_transport).instrument_metadata("ETH-USD")
    assert scope_error.value.code is CryptoAdapterFailureCode.FAIL_SCOPE_VIOLATION
    assert empty_transport.requests == []

    drift_payload = _response("product_btc_usd_sanitized.json")
    drift_document = json.loads(drift_payload.body)
    del drift_document["base_increment"]
    drift_transport = FakeRestTransport(
        (
            RestResponse(
                status_code=200,
                headers={},
                body=json.dumps(drift_document).encode(),
            ),
        )
    )
    with pytest.raises(CryptoAdapterError) as drift_error:
        _adapter(drift_transport).instrument_metadata("BTC-USD")
    assert drift_error.value.code is CryptoAdapterFailureCode.FAIL_SCHEMA_DRIFT

    private_response = RestResponse(status_code=401, headers={}, body=b'{"secret":"hidden"}')
    with pytest.raises(CryptoAdapterError) as private_error:
        _adapter(FakeRestTransport((private_response,))).instrument_metadata("BTC-USD")
    assert private_error.value.code is CryptoAdapterFailureCode.FAIL_SCOPE_VIOLATION
    assert "hidden" not in str(private_error.value)

    limited = RestResponse(
        status_code=429,
        headers={"retry-after": "99"},
        body=b'{"error":"rate limited"}',
    )
    sleeps: list[float] = []
    retry_transport = FakeRestTransport((limited, _response("product_btc_usd_sanitized.json")))
    metadata = _adapter(retry_transport, sleeps=sleeps).instrument_metadata("BTC-USD")
    assert metadata.trading_status is TradingStatus.ONLINE
    assert sleeps == [2.0]
    assert len(retry_transport.requests) == 2

    with pytest.raises(CryptoAdapterError) as rate_error:
        _adapter(FakeRestTransport((limited, limited))).instrument_metadata("BTC-USD")
    assert rate_error.value.code is CryptoAdapterFailureCode.BLOCKED_RATE_LIMIT
