"""Fail-closed Coinbase public WebSocket state machine and bounded supervisor."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from decimal import Decimal, InvalidOperation
from enum import StrEnum
from typing import Annotated, Any, Literal, Protocol
from uuid import NAMESPACE_URL, UUID, uuid4, uuid5

from pydantic import BaseModel, ConfigDict, Field, StrictInt, StrictStr, ValidationError
from websockets.sync.client import ClientConnection, connect

from tradeguard.adapters.crypto.errors import (
    CryptoAdapterError,
    CryptoAdapterFailureCode,
)
from tradeguard.adapters.crypto.protocol import TradingPairMetadata, TradingStatus
from tradeguard.data.lineage import TransformationGraph, TransformationStep
from tradeguard.data.manifest import DataInterval, DatasetManifest, DatasetPartition
from tradeguard.data.models import Quote, Trade
from tradeguard.data.quality import QualityContext, QualityGate, QualityPolicy, QualityReport
from tradeguard.domain.events import AssetClass, DataQualityAlert, Severity
from tradeguard.domain.serialization import canonicalize, deterministic_checksum

_PUBLIC_WEBSOCKET_URL = "wss://advanced-trade-ws.coinbase.com"
_PRODUCT = "BTC-USD"
_VENUE = "coinbase-advanced-trade"
_CHANNELS = ("heartbeats", "market_trades", "status", "ticker")
_BACKOFF_SECONDS = (1.0, 2.0, 4.0)
_MAX_MESSAGE_BYTES = 1_048_576
_MAX_STREAM_MESSAGES = 20
_MINIMUM_QUALIFYING_MESSAGES = 4


class StreamState(StrEnum):
    CONNECTING = "CONNECTING"
    SUBSCRIBING = "SUBSCRIBING"
    TRADABLE = "TRADABLE"
    NOT_TRADABLE = "NOT_TRADABLE"
    STOPPED = "STOPPED"


class StreamModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", validate_default=True)


class StreamMessageResult(StreamModel):
    channel: str | None
    provider_sequence: int | None
    accepted: bool
    records: tuple[Quote | Trade, ...] = ()
    alerts: tuple[DataQualityAlert, ...] = ()


class StreamRunResult(StreamModel):
    schema_version: Literal["1.0.0"] = "1.0.0"
    provider: Literal["coinbase_advanced_trade"] = "coinbase_advanced_trade"
    product_id: Literal["BTC-USD"] = "BTC-USD"
    final_state: StreamState
    messages_received: Annotated[int, Field(ge=0, le=20)]
    records: tuple[Quote | Trade, ...]
    alerts: tuple[DataQualityAlert, ...]
    reconnect_count: Annotated[int, Field(ge=0, le=3)]
    resubscription_count: Annotated[int, Field(ge=0)]
    subscriptions_sent: tuple[str, ...]
    backoff_seconds: tuple[float, ...]
    clean_shutdown: bool
    raw_message_sha256: tuple[Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")], ...]
    manifest: DatasetManifest | None = None
    quality_report: QualityReport | None = None
    raw_payload_retained: Literal[False] = False
    raw_payload_published: Literal[False] = False


class WebSocketTransportError(RuntimeError):
    """Redacted transport boundary error."""


class WebSocketConnection(Protocol):
    def send(self, message: str) -> None:
        """Send one public subscription message."""

    def recv(self, timeout: float) -> str | bytes:
        """Receive one bounded message."""

    def close(self) -> None:
        """Perform a controlled normal close."""


class WebSocketConnector(Protocol):
    def open(self, url: str) -> WebSocketConnection:
        """Open only the reviewed public market-data endpoint."""


class _WebsocketsConnection:
    def __init__(self, connection: ClientConnection) -> None:
        self._connection = connection

    def send(self, message: str) -> None:
        try:
            self._connection.send(message)
        except Exception as exc:
            raise WebSocketTransportError("public WebSocket send failed") from exc

    def recv(self, timeout: float) -> str | bytes:
        try:
            value: str | bytes = self._connection.recv(timeout=timeout)
            return value
        except TimeoutError:
            raise
        except Exception as exc:
            raise WebSocketTransportError("public WebSocket receive failed") from exc

    def close(self) -> None:
        try:
            self._connection.close(code=1000, reason="TradeGuard controlled shutdown")
        except Exception as exc:
            raise WebSocketTransportError("public WebSocket close failed") from exc


class WebsocketsPublicConnector:
    """Production connector pinned to the unauthenticated public market endpoint."""

    def open(self, url: str) -> WebSocketConnection:
        if url != _PUBLIC_WEBSOCKET_URL:
            raise CryptoAdapterError(
                CryptoAdapterFailureCode.FAIL_SCOPE_VIOLATION,
                "WebSocket URL is outside the public market-data allowlist",
            )
        try:
            connection = connect(
                url,
                open_timeout=10,
                close_timeout=5,
                ping_interval=20,
                ping_timeout=20,
                max_size=_MAX_MESSAGE_BYTES,
                max_queue=16,
                user_agent_header="TradeGuard/0.1.0",
            )
        except (OSError, TimeoutError) as exc:
            raise WebSocketTransportError("public WebSocket connection failed") from exc
        return _WebsocketsConnection(connection)


class _WsProviderModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", validate_default=True)


class _Envelope(_WsProviderModel):
    channel: StrictStr
    timestamp: StrictStr
    sequence_num: StrictInt
    events: Annotated[tuple[dict[str, Any], ...], Field(min_length=1)]
    client_id: StrictStr | None = None


class _HeartbeatEvent(_WsProviderModel):
    current_time: StrictStr
    heartbeat_counter: StrictInt | StrictStr


class _TradeItem(_WsProviderModel):
    trade_id: StrictStr
    product_id: StrictStr
    price: StrictStr
    size: StrictStr
    side: StrictStr
    time: StrictStr


class _TradeEvent(_WsProviderModel):
    type: Literal["snapshot", "update"]
    trades: Annotated[tuple[_TradeItem, ...], Field(min_length=1)]


class _TickerItem(_WsProviderModel):
    type: Literal["ticker"]
    product_id: StrictStr
    price: StrictStr
    volume_24_h: StrictStr
    low_24_h: StrictStr
    high_24_h: StrictStr
    low_52_w: StrictStr
    high_52_w: StrictStr
    price_percent_chg_24_h: StrictStr
    best_bid: StrictStr
    best_bid_quantity: StrictStr
    best_ask: StrictStr
    best_ask_quantity: StrictStr


class _TickerEvent(_WsProviderModel):
    type: Literal["snapshot", "update"]
    tickers: Annotated[tuple[_TickerItem, ...], Field(min_length=1)]


class _StatusProduct(_WsProviderModel):
    product_type: StrictStr
    id: StrictStr
    base_currency: StrictStr
    quote_currency: StrictStr
    base_increment: StrictStr
    quote_increment: StrictStr
    display_name: StrictStr
    status: StrictStr
    status_message: StrictStr
    min_market_funds: StrictStr


class _StatusEvent(_WsProviderModel):
    type: Literal["snapshot", "update"]
    products: Annotated[tuple[_StatusProduct, ...], Field(min_length=1)]


class CoinbaseStreamStateMachine:
    """Validate provider envelopes before making a stream research-admissible."""

    def __init__(
        self,
        *,
        product_metadata: TradingPairMetadata,
        clock: Callable[[], datetime],
        stale_after_seconds: int,
        run_id: UUID | None = None,
        correlation_id: UUID | None = None,
    ) -> None:
        self.product_metadata = product_metadata
        self._clock = clock
        self._stale_after = timedelta(seconds=stale_after_seconds)
        self._run_id = run_id or uuid4()
        self._correlation_id = correlation_id or uuid4()
        self._last_sequences: dict[str, int] = {}
        self._last_heartbeat_counter: int | None = None
        self._last_message_at: datetime | None = None
        self._heartbeat_seen = False
        self._status_seen = False
        self._data_seen = False
        self._alert_counter = 0
        self._record_counter = 0
        self.state = StreamState.CONNECTING

    def on_connect(self) -> None:
        self._last_sequences.clear()
        self._last_heartbeat_counter = None
        self._last_message_at = None
        self._heartbeat_seen = False
        self._status_seen = False
        self._data_seen = False
        self.state = (
            StreamState.SUBSCRIBING
            if self.product_metadata.trading_status is TradingStatus.ONLINE
            else StreamState.NOT_TRADABLE
        )

    def process(  # noqa: PLR0911 - every failure returns explicit evidence
        self,
        raw_message: str | bytes,
    ) -> StreamMessageResult:
        now = _normalize_clock(self._clock())
        try:
            payload = json.loads(raw_message)
            envelope = _Envelope.model_validate(payload)
            timestamp = _parse_utc(envelope.timestamp)
        except (UnicodeDecodeError, json.JSONDecodeError, ValidationError, ValueError):
            alert = self._alert(
                "COINBASE_WS_SCHEMA_DRIFT",
                "WebSocket message violates the reviewed envelope schema",
                now,
                0,
            )
            return StreamMessageResult(
                channel=None,
                provider_sequence=None,
                accepted=False,
                alerts=(alert,),
            )
        if envelope.channel not in _CHANNELS:
            alert = self._alert(
                "COINBASE_WS_UNAPPROVED_CHANNEL",
                "WebSocket message arrived from an unapproved channel",
                min(timestamp, now),
                envelope.sequence_num,
            )
            return self._rejected(envelope, alert)
        if timestamp > now:
            alert = self._alert(
                "COINBASE_WS_FUTURE_TIMESTAMP",
                "WebSocket message timestamp is in the future",
                now,
                envelope.sequence_num,
            )
            return self._rejected(envelope, alert)
        if now - timestamp > self._stale_after:
            alert = self._alert(
                "COINBASE_WS_STALE_STREAM",
                "WebSocket message is older than the reviewed stale threshold",
                timestamp,
                envelope.sequence_num,
            )
            return self._rejected(envelope, alert)
        sequence_alert = self._sequence_alert(envelope, timestamp)
        if sequence_alert is not None:
            return self._rejected(envelope, sequence_alert)
        self._last_message_at = now
        try:
            records = self._parse_channel(envelope, timestamp, now)
        except _MetadataConflictError as exc:
            return self._rejected(envelope, exc.alert)
        except _HeartbeatGapError:
            alert = self._alert(
                "COINBASE_WS_HEARTBEAT_GAP",
                "heartbeat counter gap detected; missing heartbeats were not inferred",
                timestamp,
                envelope.sequence_num,
            )
            return self._rejected(envelope, alert)
        except (ValidationError, ValueError, CryptoAdapterError):
            alert = self._alert(
                "COINBASE_WS_SCHEMA_DRIFT",
                "WebSocket channel payload violates the reviewed schema",
                timestamp,
                envelope.sequence_num,
            )
            return self._rejected(envelope, alert)
        if (
            self.product_metadata.trading_status is TradingStatus.ONLINE
            and self._heartbeat_seen
            and self._status_seen
            and self._data_seen
        ):
            self.state = StreamState.TRADABLE
        return StreamMessageResult(
            channel=envelope.channel,
            provider_sequence=envelope.sequence_num,
            accepted=True,
            records=records,
        )

    def mark_stale(self) -> DataQualityAlert:
        now = _normalize_clock(self._clock())
        event_time = self._last_message_at or now
        return self._alert(
            "COINBASE_WS_STALE_STREAM",
            "no WebSocket message arrived within the reviewed stale threshold",
            event_time,
            max(self._last_sequences.values(), default=0),
        )

    def mark_reconnect_exhausted(self) -> DataQualityAlert:
        now = _normalize_clock(self._clock())
        return self._alert(
            "COINBASE_WS_RECONNECT_EXHAUSTED",
            "bounded reconnect schedule was exhausted before stream qualification",
            now,
            max(self._last_sequences.values(), default=0),
        )

    def stop(self) -> None:
        if self.state is not StreamState.NOT_TRADABLE:
            self.state = StreamState.STOPPED

    def _sequence_alert(
        self,
        envelope: _Envelope,
        timestamp: datetime,
    ) -> DataQualityAlert | None:
        if envelope.channel == "heartbeats":
            return None
        previous = self._last_sequences.get(envelope.channel)
        if previous is None:
            self._last_sequences[envelope.channel] = envelope.sequence_num
            return None
        if envelope.sequence_num == previous:
            return self._alert(
                "COINBASE_WS_DUPLICATE_SEQUENCE",
                "duplicate provider sequence is quarantined",
                timestamp,
                envelope.sequence_num,
            )
        if envelope.sequence_num < previous:
            return self._alert(
                "COINBASE_WS_OUT_OF_ORDER_SEQUENCE",
                "out-of-order provider sequence is quarantined",
                timestamp,
                envelope.sequence_num,
            )
        if envelope.sequence_num != previous + 1:
            return self._alert(
                "COINBASE_WS_SEQUENCE_GAP",
                "provider sequence gap detected; missing events were not inferred",
                timestamp,
                envelope.sequence_num,
            )
        self._last_sequences[envelope.channel] = envelope.sequence_num
        return None

    def _parse_channel(  # noqa: PLR0912 - channel contracts are intentionally centralized
        self,
        envelope: _Envelope,
        timestamp: datetime,
        now: datetime,
    ) -> tuple[Quote | Trade, ...]:
        if envelope.channel == "heartbeats":
            for raw_event in envelope.events:
                event = _HeartbeatEvent.model_validate(raw_event)
                counter = int(event.heartbeat_counter)
                if (
                    self._last_heartbeat_counter is not None
                    and counter != self._last_heartbeat_counter + 1
                ):
                    raise _HeartbeatGapError
                self._last_heartbeat_counter = counter
            self._heartbeat_seen = True
            return ()
        if envelope.channel == "status":
            products = tuple(
                product
                for raw_event in envelope.events
                for product in _StatusEvent.model_validate(raw_event).products
                if product.id == _PRODUCT
            )
            if len(products) != 1 or not self._status_matches(products[0]):
                alert = self._alert(
                    "COINBASE_WS_METADATA_CONFLICT",
                    "WebSocket status metadata conflicts with REST metadata",
                    timestamp,
                    envelope.sequence_num,
                )
                raise _MetadataConflictError(alert)
            self._status_seen = True
            return ()
        if envelope.channel == "ticker":
            records: list[Quote | Trade] = []
            for raw_event in envelope.events:
                for ticker in _TickerEvent.model_validate(raw_event).tickers:
                    if ticker.product_id != _PRODUCT:
                        raise ValueError("ticker product mismatch")
                    self._record_counter += 1
                    records.append(
                        Quote(
                            source="coinbase-advanced-trade-public-websocket",
                            asset_class=AssetClass.CRYPTO,
                            venue=_VENUE,
                            symbol=_PRODUCT,
                            event_time_utc=timestamp,
                            ingest_time_utc=now,
                            sequence_number=self._record_counter,
                            bid_price=_decimal(ticker.best_bid),
                            ask_price=_decimal(ticker.best_ask),
                            bid_quantity=_decimal(ticker.best_bid_quantity),
                            ask_quantity=_decimal(ticker.best_ask_quantity),
                            quote_asset="USD",
                        )
                    )
            self._data_seen = bool(records) or self._data_seen
            return tuple(records)
        if envelope.channel == "market_trades":
            records = []
            for raw_event in envelope.events:
                for item in _TradeEvent.model_validate(raw_event).trades:
                    if item.product_id != _PRODUCT or item.side not in {"BUY", "SELL"}:
                        raise ValueError("trade identity mismatch")
                    event_time = _parse_utc(item.time)
                    if event_time > now:
                        raise ValueError("future trade timestamp")
                    self._record_counter += 1
                    records.append(
                        Trade(
                            source="coinbase-advanced-trade-public-websocket",
                            asset_class=AssetClass.CRYPTO,
                            venue=_VENUE,
                            symbol=_PRODUCT,
                            event_time_utc=event_time,
                            ingest_time_utc=now,
                            sequence_number=self._record_counter,
                            trade_id=item.trade_id,
                            price=_decimal(item.price),
                            quantity=_decimal(item.size),
                            quote_asset="USD",
                        )
                    )
            self._data_seen = bool(records) or self._data_seen
            return tuple(records)
        raise ValueError("unreachable unapproved channel")

    def _status_matches(self, status: _StatusProduct) -> bool:
        metadata = self.product_metadata
        return (
            status.product_type == "SPOT"
            and status.base_currency == metadata.base_asset
            and status.quote_currency == metadata.quote_asset
            and _decimal(status.base_increment) == metadata.instrument.step_size
            and _decimal(status.quote_increment) == metadata.instrument.tick_size
            and _decimal(status.min_market_funds) == metadata.instrument.minimum_notional
            and status.status.strip().lower() == metadata.provider_status.strip().lower()
        )

    def _rejected(
        self,
        envelope: _Envelope,
        alert: DataQualityAlert,
    ) -> StreamMessageResult:
        return StreamMessageResult(
            channel=envelope.channel,
            provider_sequence=envelope.sequence_num,
            accepted=False,
            alerts=(alert,),
        )

    def _alert(
        self,
        code: str,
        message: str,
        event_time: datetime,
        sequence: int,
    ) -> DataQualityAlert:
        self.state = StreamState.NOT_TRADABLE
        self._alert_counter += 1
        return DataQualityAlert.build(
            event_id=uuid5(
                NAMESPACE_URL,
                f"{self._run_id}:{self._alert_counter}:{code}:{sequence}",
            ),
            source="tradeguard-coinbase-stream-gate",
            asset_class=AssetClass.CRYPTO,
            venue=_VENUE,
            symbol=_PRODUCT,
            event_time_utc=event_time,
            ingest_time_utc=_normalize_clock(self._clock()),
            sequence_number=max(sequence, 0),
            correlation_id=self._correlation_id,
            causation_id=None,
            run_id=self._run_id,
            code=code,
            severity=Severity.ERROR,
            message=message,
            quarantined=True,
        )


class _MetadataConflictError(ValueError):
    def __init__(self, alert: DataQualityAlert) -> None:
        self.alert = alert
        super().__init__("metadata conflict")


class _HeartbeatGapError(ValueError):
    """Internal marker converted into a fail-closed quality alert."""


class CoinbaseStreamSupervisor:
    """Reconnect, resubscribe, bound backoff, and always close the connection."""

    def __init__(  # noqa: PLR0913 - explicit safety controls remain independently testable
        self,
        *,
        connector: WebSocketConnector,
        product_metadata: TradingPairMetadata,
        clock: Callable[[], datetime],
        sleeper: Callable[[float], None],
        stale_after_seconds: int,
        maximum_reconnects: int,
    ) -> None:
        if maximum_reconnects < 0 or maximum_reconnects > len(_BACKOFF_SECONDS):
            raise ValueError("maximum reconnects exceeds the reviewed bounded schedule")
        self._connector = connector
        self._metadata = product_metadata
        self._clock = clock
        self._sleeper = sleeper
        self._stale_after_seconds = stale_after_seconds
        self._maximum_reconnects = maximum_reconnects

    def run(  # noqa: PLR0912, PLR0915 - lifecycle cleanup stays visible in one boundary
        self,
        *,
        stop_after_messages: int,
        deadline_utc: datetime,
    ) -> StreamRunResult:
        deadline = _normalize_clock(deadline_utc)
        if stop_after_messages < 1 or stop_after_messages > _MAX_STREAM_MESSAGES:
            raise ValueError("stop_after_messages must be between 1 and 20")
        machine = CoinbaseStreamStateMachine(
            product_metadata=self._metadata,
            clock=self._clock,
            stale_after_seconds=self._stale_after_seconds,
        )
        records: list[Quote | Trade] = []
        alerts: list[DataQualityAlert] = []
        checksums: list[str] = []
        subscriptions: list[str] = []
        backoffs: list[float] = []
        messages_received = 0
        reconnect_count = 0
        clean_shutdown = True
        finished = False
        for connection_index in range(self._maximum_reconnects + 1):
            if _normalize_clock(self._clock()) >= deadline:
                alerts.append(machine.mark_stale())
                break
            if connection_index:
                delay = _BACKOFF_SECONDS[connection_index - 1]
                backoffs.append(delay)
                self._sleeper(delay)
                reconnect_count += 1
            machine.on_connect()
            connection: WebSocketConnection | None = None
            try:
                connection = self._connector.open(_PUBLIC_WEBSOCKET_URL)
                for channel in _CHANNELS:
                    subscription = json.dumps(
                        {
                            "type": "subscribe",
                            "product_ids": [_PRODUCT],
                            "channel": channel,
                        },
                        separators=(",", ":"),
                        sort_keys=True,
                    )
                    if "jwt" in subscription.lower():
                        raise CryptoAdapterError(
                            CryptoAdapterFailureCode.FAIL_SCOPE_VIOLATION,
                            "authentication is prohibited in public subscriptions",
                        )
                    connection.send(subscription)
                    subscriptions.append(channel)
                while messages_received < stop_after_messages:
                    remaining = (deadline - _normalize_clock(self._clock())).total_seconds()
                    if remaining <= 0:
                        alerts.append(machine.mark_stale())
                        break
                    try:
                        raw = connection.recv(timeout=min(self._stale_after_seconds, remaining))
                    except TimeoutError:
                        alerts.append(machine.mark_stale())
                        break
                    raw_bytes = raw.encode() if isinstance(raw, str) else raw
                    if len(raw_bytes) > _MAX_MESSAGE_BYTES:
                        result = machine.process(b"{}")
                    else:
                        result = machine.process(raw)
                    checksums.append(hashlib.sha256(raw_bytes).hexdigest())
                    messages_received += 1
                    records.extend(result.records)
                    alerts.extend(result.alerts)
                    if not result.accepted:
                        break
                    if (
                        machine.state is StreamState.TRADABLE
                        and messages_received >= _MINIMUM_QUALIFYING_MESSAGES
                    ):
                        finished = True
                        break
            except WebSocketTransportError:
                pass
            finally:
                if connection is not None:
                    try:
                        connection.close()
                    except WebSocketTransportError:
                        clean_shutdown = False
            if finished:
                break
            if messages_received >= stop_after_messages:
                break
        canonical_records = _canonicalize_records(records)
        manifest: DatasetManifest | None = None
        quality_report: QualityReport | None = None
        if canonical_records:
            manifest = _build_stream_manifest(canonical_records, tuple(checksums), self._clock())
            quality_report = QualityGate().validate(
                canonical_records,
                QualityContext(
                    manifest=manifest,
                    policy=QualityPolicy(
                        evaluated_at=_normalize_clock(self._clock()),
                        knowledge_time_utc=_normalize_clock(self._clock()),
                        max_staleness_seconds=300,
                    ),
                    instrument_metadata=(self._metadata.instrument,),
                ),
            )
        if not finished and not alerts:
            alerts.append(machine.mark_reconnect_exhausted())
        if alerts or not finished or machine.state is not StreamState.TRADABLE:
            final_state = StreamState.NOT_TRADABLE
        else:
            machine.stop()
            final_state = StreamState.STOPPED
        return StreamRunResult(
            final_state=final_state,
            messages_received=messages_received,
            records=canonical_records,
            alerts=tuple(alerts),
            reconnect_count=reconnect_count,
            resubscription_count=reconnect_count,
            subscriptions_sent=tuple(subscriptions),
            backoff_seconds=tuple(backoffs),
            clean_shutdown=clean_shutdown,
            raw_message_sha256=tuple(checksums),
            manifest=manifest,
            quality_report=quality_report,
        )


def _canonicalize_records(records: list[Quote | Trade]) -> tuple[Quote | Trade, ...]:
    ordered = sorted(
        records,
        key=lambda record: (
            record.event_time_utc,
            record.record_type.value,
            record.trade_id if isinstance(record, Trade) else "",
        ),
    )
    return tuple(
        record.model_copy(update={"sequence_number": index})
        for index, record in enumerate(ordered, start=1)
    )


def _build_stream_manifest(
    records: tuple[Quote | Trade, ...],
    raw_checksums: tuple[str, ...],
    clock_value: datetime,
) -> DatasetManifest:
    now = _normalize_clock(clock_value)
    canonical_checksum = deterministic_checksum(tuple(canonicalize(record) for record in records))
    raw_bundle_checksum = deterministic_checksum(raw_checksums)
    dataset_id = f"coinbase-ws-btc-usd-{canonical_checksum[:16]}"
    start = min(record.event_time_utc for record in records)
    end = max(record.event_time_utc for record in records)
    if end <= start:
        end = start + timedelta(microseconds=1)
    date_range = DataInterval(start_utc=start, end_utc=end)
    return DatasetManifest(
        dataset_id=dataset_id,
        dataset_version="1.0.0",
        source="coinbase-advanced-trade-public-websocket",
        asset_class=AssetClass.CRYPTO,
        symbols=(_PRODUCT,),
        date_range=date_range,
        row_count=len(records),
        partition_information=(
            DatasetPartition(
                partition_id="part-0000",
                relative_path=f"runtime/{dataset_id}/canonical-stream-records.json",
                row_count=len(records),
                date_range=date_range,
                checksum=canonical_checksum,
            ),
        ),
        checksums={
            "canonical_records_sha256": canonical_checksum,
            "raw_message_bundle_sha256": raw_bundle_checksum,
        },
        created_at=now,
        ingested_at=now,
        licensing_notes=(
            "Coinbase public WebSocket data used for internal non-display research; raw "
            "messages are transient and prohibited from Git and public release evidence."
        ),
        transformation_graph=TransformationGraph(
            steps=(
                TransformationStep(
                    transformation_id="normalize-coinbase-public-websocket-v1",
                    operation="validate_sequence_metadata_and_map_public_stream",
                    implementation_version="1.0.0",
                    input_dataset_ids=(f"coinbase-ws-raw-{raw_bundle_checksum[:16]}",),
                    output_dataset_id=dataset_id,
                    parameters_hash=deterministic_checksum(
                        {"product_id": _PRODUCT, "channels": _CHANNELS}
                    ),
                ),
            )
        ),
    )


def _parse_utc(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("timestamp has no timezone")
    return parsed.astimezone(UTC)


def _normalize_clock(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("stream clock and deadline must be timezone-aware")
    return value.astimezone(UTC)


def _decimal(value: str) -> Decimal:
    try:
        parsed = Decimal(value)
    except InvalidOperation:
        raise ValueError("invalid decimal") from None
    if not parsed.is_finite() or parsed < 0:
        raise ValueError("negative or non-finite decimal")
    return parsed
