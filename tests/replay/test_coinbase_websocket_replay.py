"""Deterministic Coinbase WebSocket replay and fail-closed stream tests."""

from __future__ import annotations

import json
from collections.abc import Iterable
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import pytest

from tradeguard.adapters.crypto.protocol import TradingPairMetadata, TradingStatus
from tradeguard.adapters.crypto.stream import (
    CoinbaseStreamStateMachine,
    CoinbaseStreamSupervisor,
    StreamState,
    WebSocketConnection,
    WebSocketConnector,
    WebSocketTransportError,
)
from tradeguard.data.models import InstrumentMetadata
from tradeguard.data.quality import QualityStatus
from tradeguard.domain.events import AssetClass

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "tests" / "fixtures" / "adapters" / "coinbase" / "websocket_btc_usd_sanitized.json"
NOW = datetime(2024, 1, 1, 0, 5, tzinfo=UTC)


def _messages() -> list[dict[str, object]]:
    document = json.loads(FIXTURE.read_text(encoding="utf-8"))
    messages = document["messages"]
    assert isinstance(messages, list)
    return messages


def _metadata(*, quote_increment: str = "0.01") -> TradingPairMetadata:
    return TradingPairMetadata(
        instrument=InstrumentMetadata(
            source="fixture",
            asset_class=AssetClass.CRYPTO,
            venue="coinbase-advanced-trade",
            symbol="BTC-USD",
            canonical_symbol="BTC-USD",
            quote_asset="USD",
            tick_size=Decimal(quote_increment),
            step_size=Decimal("0.00000001"),
            lot_size=Decimal("0.00000001"),
            minimum_quantity=Decimal("0.00000001"),
            minimum_notional=Decimal("1.00"),
            timezone="UTC",
            active_from=datetime(2015, 1, 1, tzinfo=UTC),
            known_at=NOW,
            metadata_version="fixture-v1",
        ),
        base_asset="BTC",
        quote_asset="USD",
        trading_status=TradingStatus.ONLINE,
        provider_status="online",
        metadata_timestamp=NOW,
    )


def _machine(metadata: TradingPairMetadata | None = None) -> CoinbaseStreamStateMachine:
    machine = CoinbaseStreamStateMachine(
        product_metadata=metadata or _metadata(),
        clock=lambda: NOW,
        stale_after_seconds=5,
    )
    machine.on_connect()
    return machine


def _encoded(message: dict[str, object]) -> str:
    return json.dumps(message, separators=(",", ":"), sort_keys=True)


@pytest.mark.replay
def test_recorded_messages_reach_tradable_without_alerts() -> None:
    machine = _machine()
    results = [machine.process(_encoded(message)) for message in _messages()]

    assert all(result.accepted for result in results)
    assert not tuple(alert for result in results for alert in result.alerts)
    assert machine.state is StreamState.TRADABLE
    assert sum(len(result.records) for result in results) == 2


@pytest.mark.replay
@pytest.mark.parametrize(
    ("second_sequence", "expected_code"),
    [
        (30, "COINBASE_WS_DUPLICATE_SEQUENCE"),
        (29, "COINBASE_WS_OUT_OF_ORDER_SEQUENCE"),
        (32, "COINBASE_WS_SEQUENCE_GAP"),
    ],
)
def test_duplicate_gap_and_out_of_order_sequences_are_not_tradable(
    second_sequence: int,
    expected_code: str,
) -> None:
    ticker = _messages()[2]
    second = json.loads(json.dumps(ticker))
    second["sequence_num"] = second_sequence
    machine = _machine()

    assert machine.process(_encoded(ticker)).accepted is True
    rejected = machine.process(_encoded(second))

    assert rejected.accepted is False
    assert rejected.alerts[0].code == expected_code
    assert rejected.alerts[0].quarantined is True
    assert machine.state is StreamState.NOT_TRADABLE


@pytest.mark.replay
def test_unknown_sequence_stale_schema_and_metadata_conflict_emit_alerts() -> None:
    missing_sequence = json.loads(json.dumps(_messages()[2]))
    del missing_sequence["sequence_num"]
    schema_result = _machine().process(_encoded(missing_sequence))
    assert schema_result.alerts[0].code == "COINBASE_WS_SCHEMA_DRIFT"

    stale = json.loads(json.dumps(_messages()[2]))
    stale["timestamp"] = "2024-01-01T00:04:50Z"
    stale_result = _machine().process(_encoded(stale))
    assert stale_result.alerts[0].code == "COINBASE_WS_STALE_STREAM"

    conflict = _machine(metadata=_metadata(quote_increment="0.10")).process(
        _encoded(_messages()[0])
    )
    assert conflict.alerts[0].code == "COINBASE_WS_METADATA_CONFLICT"

    unknown_channel = json.loads(json.dumps(_messages()[2]))
    unknown_channel["channel"] = "user"
    channel_result = _machine().process(_encoded(unknown_channel))
    assert channel_result.alerts[0].code == "COINBASE_WS_UNAPPROVED_CHANNEL"

    future = json.loads(json.dumps(_messages()[2]))
    future["timestamp"] = "2024-01-01T00:05:01Z"
    future_result = _machine().process(_encoded(future))
    assert future_result.alerts[0].code == "COINBASE_WS_FUTURE_TIMESTAMP"


@pytest.mark.replay
def test_heartbeat_gap_and_receive_timeout_fail_closed() -> None:
    first = _messages()[1]
    second = json.loads(json.dumps(first))
    second["sequence_num"] = 21
    second["events"][0]["heartbeat_counter"] = 102
    machine = _machine()

    assert machine.process(_encoded(first)).accepted is True
    result = machine.process(_encoded(second))
    assert result.alerts[0].code == "COINBASE_WS_HEARTBEAT_GAP"

    timeout_alert = _machine().mark_stale()
    assert timeout_alert.code == "COINBASE_WS_STALE_STREAM"
    assert timeout_alert.quarantined is True

    sequential = json.loads(json.dumps(first))
    sequential["events"][0]["heartbeat_counter"] = 101
    sequential_machine = _machine()
    assert sequential_machine.process(_encoded(first)).accepted is True
    assert sequential_machine.process(_encoded(sequential)).accepted is True


class FakeConnection(WebSocketConnection):
    def __init__(self, messages: Iterable[dict[str, object]]) -> None:
        self._messages = iter(messages)
        self.sent: list[str] = []
        self.closed = False

    def send(self, message: str) -> None:
        self.sent.append(message)

    def recv(self, timeout: float) -> str:
        assert timeout > 0
        try:
            return _encoded(next(self._messages))
        except StopIteration:
            raise WebSocketTransportError("fixture disconnect") from None

    def close(self) -> None:
        self.closed = True


class FakeConnector(WebSocketConnector):
    def __init__(self, connections: Iterable[FakeConnection]) -> None:
        self._connections = iter(connections)
        self.urls: list[str] = []

    def open(self, url: str) -> WebSocketConnection:
        self.urls.append(url)
        return next(self._connections)


@pytest.mark.replay
def test_supervisor_builds_manifest_quality_and_clean_shutdown() -> None:
    connection = FakeConnection(_messages())
    connector = FakeConnector((connection,))
    result = CoinbaseStreamSupervisor(
        connector=connector,
        product_metadata=_metadata(),
        clock=lambda: NOW,
        sleeper=lambda _: None,
        stale_after_seconds=5,
        maximum_reconnects=3,
    ).run(stop_after_messages=4, deadline_utc=NOW.replace(minute=6))

    assert result.final_state is StreamState.STOPPED
    assert result.messages_received == 4
    assert len(result.records) == 2
    assert result.alerts == ()
    assert result.manifest is not None
    assert result.quality_report is not None
    assert result.quality_report.status is QualityStatus.PASS
    assert result.clean_shutdown is True
    assert connection.closed is True
    assert result.subscriptions_sent == (
        "heartbeats",
        "market_trades",
        "status",
        "ticker",
    )
    assert all("jwt" not in message.lower() for message in connection.sent)


@pytest.mark.replay
def test_disconnect_uses_bounded_backoff_and_resubscribes() -> None:
    first = FakeConnection((_messages()[0],))
    second = FakeConnection(_messages())
    sleeps: list[float] = []
    connector = FakeConnector((first, second))

    result = CoinbaseStreamSupervisor(
        connector=connector,
        product_metadata=_metadata(),
        clock=lambda: NOW,
        sleeper=sleeps.append,
        stale_after_seconds=5,
        maximum_reconnects=3,
    ).run(stop_after_messages=5, deadline_utc=NOW.replace(minute=6))

    assert result.final_state is StreamState.STOPPED
    assert result.reconnect_count == 1
    assert result.resubscription_count == 1
    assert result.backoff_seconds == (1.0,)
    assert sleeps == [1.0]
    assert len(result.subscriptions_sent) == 8
    assert first.closed is True
    assert second.closed is True


@pytest.mark.replay
def test_exhausted_reconnects_are_not_tradable() -> None:
    connections = tuple(FakeConnection(()) for _ in range(4))
    result = CoinbaseStreamSupervisor(
        connector=FakeConnector(connections),
        product_metadata=_metadata(),
        clock=lambda: NOW,
        sleeper=lambda _: None,
        stale_after_seconds=5,
        maximum_reconnects=3,
    ).run(stop_after_messages=4, deadline_utc=NOW.replace(minute=6))

    assert result.final_state is StreamState.NOT_TRADABLE
    assert result.reconnect_count == 3
    assert result.alerts[-1].code == "COINBASE_WS_RECONNECT_EXHAUSTED"
    assert result.records == ()
    assert all(connection.closed for connection in connections)
