"""Coinbase Advanced Trade public REST and WebSocket market-data adapter."""

from __future__ import annotations

import hashlib
import json
import logging
import math
import time
from collections.abc import Callable, Mapping, Sequence
from datetime import UTC, datetime, timedelta
from decimal import Decimal, InvalidOperation
from typing import TYPE_CHECKING, Annotated, Any, TypeVar
from urllib.parse import urlencode, urlsplit

from pydantic import BaseModel, ConfigDict, Field, StrictBool, StrictStr, ValidationError

from tradeguard.adapters.crypto.configuration import CoinbaseReleaseConfiguration
from tradeguard.adapters.crypto.errors import (
    CryptoAdapterError,
    CryptoAdapterFailureCode,
    CryptoScopeViolationError,
)
from tradeguard.adapters.crypto.protocol import (
    BestBidAsk,
    CryptoAdapterCapabilities,
    CryptoBarsRequest,
    CryptoDataset,
    MaintenanceStatus,
    ProviderCallRecord,
    RateLimitMetadata,
    RestHealth,
    RestHealthState,
    TradingPairMetadata,
    TradingStatus,
    VenueMaintenance,
)
from tradeguard.adapters.crypto.transport import (
    CoinbasePublicHttpsTransport,
    RestRequest,
    RestResponse,
    RestTransport,
)
from tradeguard.data.lineage import TransformationGraph, TransformationStep
from tradeguard.data.manifest import DataInterval, DatasetManifest, DatasetPartition
from tradeguard.data.models import InstrumentMetadata, MarketDataRecord, OHLCVBar, Quote, Trade
from tradeguard.data.quality import QualityContext, QualityGate, QualityPolicy, QualityStatus
from tradeguard.domain.events import AssetClass
from tradeguard.domain.serialization import canonicalize, deterministic_checksum

if TYPE_CHECKING:
    from tradeguard.adapters.crypto.stream import WebSocketConnector

_LOGGER = logging.getLogger(__name__)
_APPROVED_PRODUCT = "BTC-USD"
_VENUE = "coinbase-advanced-trade"
_REST_ROOT = "https://api.coinbase.com/api/v3/brokerage"
_MAX_RESPONSE_BYTES = 1_048_576
_TIMEOUT_SECONDS = 10.0
_MAX_ATTEMPTS = 2
_MAX_RETRY_AFTER_SECONDS = 2.0
_HTTP_TOO_MANY_REQUESTS = 429
_HTTP_SUCCESS_MIN = 200
_HTTP_SUCCESS_MAX_EXCLUSIVE = 300
_HTTP_SERVER_ERROR_MIN = 500
_HTTP_SERVER_ERROR_MAX = 599
_MAX_PUBLIC_ROWS = 10
_MAX_SERVER_TIME_SKEW_SECONDS = 30
_MAX_STREAM_MESSAGES = 20
_ProviderModelT = TypeVar("_ProviderModelT", bound="_ProviderModel")


class _ProviderModel(BaseModel):
    """Validate required semantics while tolerating additive documented fields."""

    model_config = ConfigDict(frozen=True, extra="ignore", validate_default=True)


class _ProductResponse(_ProviderModel):
    product_id: StrictStr
    base_increment: StrictStr
    quote_increment: StrictStr
    quote_min_size: StrictStr
    base_min_size: StrictStr
    status: StrictStr
    is_disabled: StrictBool
    cancel_only: StrictBool
    trading_disabled: StrictBool
    product_type: StrictStr
    quote_currency_id: StrictStr
    base_currency_id: StrictStr
    view_only: StrictBool
    price_increment: StrictStr
    product_venue: StrictStr
    new_at: StrictStr


class _Candle(_ProviderModel):
    start: StrictStr
    low: StrictStr
    high: StrictStr
    open: StrictStr
    close: StrictStr
    volume: StrictStr


class _CandlesResponse(_ProviderModel):
    candles: Annotated[tuple[_Candle, ...], Field(min_length=1, max_length=10)]


class _PublicTrade(_ProviderModel):
    trade_id: StrictStr
    product_id: StrictStr
    price: StrictStr
    size: StrictStr
    time: StrictStr
    side: StrictStr
    exchange: StrictStr | None = None


class _TickerResponse(_ProviderModel):
    trades: Annotated[tuple[_PublicTrade, ...], Field(min_length=1, max_length=10)]
    best_bid: StrictStr
    best_ask: StrictStr


class _ServerTimeResponse(_ProviderModel):
    iso: StrictStr
    epoch_seconds: StrictStr = Field(alias="epochSeconds")
    epoch_millis: StrictStr = Field(alias="epochMillis")


def reviewed_rest_schemas() -> dict[str, dict[str, Any]]:
    """Return strict required-field schemas used at the provider boundary."""

    return {
        "product": _ProductResponse.model_json_schema(),
        "candles": _CandlesResponse.model_json_schema(),
        "ticker": _TickerResponse.model_json_schema(),
        "server_time": _ServerTimeResponse.model_json_schema(),
    }


class CoinbaseCryptoMarketDataAdapter:
    """Unauthenticated public-data adapter with no account or order endpoints."""

    def __init__(  # noqa: PLR0913 - explicit injectable boundaries are intentional
        self,
        *,
        release_configuration: CoinbaseReleaseConfiguration,
        rest_transport: RestTransport | None = None,
        websocket_connector: WebSocketConnector | None = None,
        clock: Callable[[], datetime] | None = None,
        sleeper: Callable[[float], None] | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        self._release_configuration = release_configuration
        self._rest_transport = rest_transport or CoinbasePublicHttpsTransport()
        self._websocket_connector = websocket_connector
        self._clock = clock or (lambda: datetime.now(UTC))
        self._sleeper = sleeper or time.sleep
        self._logger = logger or _LOGGER

    @property
    def capabilities(self) -> CryptoAdapterCapabilities:
        return self._release_configuration.capabilities

    @property
    def rate_limits(self) -> RateLimitMetadata:
        return RateLimitMetadata(
            rest_limit="provider_enforced_not_published_for_unauthenticated_public_endpoints",
            http_429_handling="one_bounded_retry",
            websocket_connections_per_second_per_ip=8,
            websocket_unauthenticated_messages_per_second_per_ip=8,
            reconnect_backoff_seconds=(1.0, 2.0, 4.0),
            observed_documentation_at=datetime(2026, 7, 31, tzinfo=UTC),
        )

    def supported_pairs(self) -> tuple[str, ...]:
        return tuple(self.capabilities.approved_pairs)

    def instrument_metadata(self, product_id: str) -> TradingPairMetadata:
        normalized = self._normalize_product(product_id)
        now = self._normalized_now()
        product, _ = self._get_product(normalized)
        return self._normalize_metadata(product, now)

    def historical_bars(self, request: CryptoBarsRequest) -> CryptoDataset:
        product = self._normalize_product(request.product_id)
        now = self._normalized_now()
        provider_product, product_call = self._get_product(product)
        metadata = self._normalize_metadata(provider_product, now)
        query = urlencode(
            {
                "start": str(math.floor(request.start.timestamp())),
                "end": str(math.floor(request.end.timestamp())),
                "granularity": request.granularity,
                "limit": str(request.limit),
            }
        )
        response, candles_call = self._request(
            f"/api/v3/brokerage/market/products/{product}/candles",
            query=query,
        )
        parsed = self._parse(response, _CandlesResponse, "public candles")
        records = self._normalize_bars(parsed, request, now)
        return self._dataset(
            records=records,
            metadata=metadata.instrument,
            calls=(product_call, candles_call),
            now=now,
            operation="normalize-coinbase-public-candles-v1",
            expected_bar_interval_seconds=60,
        )

    def public_trades(self, product_id: str, *, limit: int = 5) -> CryptoDataset:
        product = self._normalize_product(product_id)
        if limit < 1 or limit > _MAX_PUBLIC_ROWS:
            raise CryptoScopeViolationError("public trade limit must be between 1 and 10")
        now = self._normalized_now()
        provider_product, product_call = self._get_product(product)
        metadata = self._normalize_metadata(provider_product, now)
        response, ticker_call = self._request(
            f"/api/v3/brokerage/market/products/{product}/ticker",
            query=urlencode({"limit": str(limit)}),
        )
        parsed = self._parse(response, _TickerResponse, "public market trades")
        if len(parsed.trades) > limit:
            raise CryptoAdapterError(
                CryptoAdapterFailureCode.FAIL_SCHEMA_DRIFT,
                "provider returned more trades than requested",
            )
        records = self._normalize_trades(parsed, now)
        return self._dataset(
            records=records,
            metadata=metadata.instrument,
            calls=(product_call, ticker_call),
            now=now,
            operation="normalize-coinbase-public-trades-v1",
        )

    def best_bid_ask(self, product_id: str) -> BestBidAsk:
        product = self._normalize_product(product_id)
        now = self._normalized_now()
        response, call = self._request(
            f"/api/v3/brokerage/market/products/{product}/ticker",
            query=urlencode({"limit": "1"}),
        )
        parsed = self._parse(response, _TickerResponse, "public best bid and ask")
        try:
            return BestBidAsk(
                observed_at=now,
                bid_price=_decimal(parsed.best_bid, "best_bid"),
                ask_price=_decimal(parsed.best_ask, "best_ask"),
                provider_call=call,
            )
        except ValidationError:
            raise CryptoAdapterError(
                CryptoAdapterFailureCode.FAIL_DATA_QUALITY,
                "provider best bid and ask failed canonical validation",
            ) from None

    def rest_health(self) -> RestHealth:
        now = self._normalized_now()
        response, call = self._request("/api/v3/brokerage/time")
        parsed = self._parse(response, _ServerTimeResponse, "server time")
        provider_time = _utc_datetime(parsed.iso, "iso")
        try:
            epoch_seconds = int(parsed.epoch_seconds)
            epoch_millis = int(parsed.epoch_millis)
        except ValueError:
            raise CryptoAdapterError(
                CryptoAdapterFailureCode.FAIL_SCHEMA_DRIFT,
                "provider server-time epochs are invalid",
            ) from None
        if epoch_seconds != int(provider_time.timestamp()) or epoch_millis // 1000 != epoch_seconds:
            raise CryptoAdapterError(
                CryptoAdapterFailureCode.FAIL_SCHEMA_DRIFT,
                "provider server-time fields conflict",
            )
        state = (
            RestHealthState.HEALTHY
            if abs((now - provider_time).total_seconds()) <= _MAX_SERVER_TIME_SKEW_SECONDS
            else RestHealthState.DEGRADED
        )
        return RestHealth(
            state=state,
            observed_at=now,
            provider_time_utc=provider_time,
            response_status=call.response_status,
            raw_response_sha256=call.raw_response_sha256,
            attempts=call.attempts,
        )

    def venue_maintenance_status(self, product_id: str) -> VenueMaintenance:
        metadata = self.instrument_metadata(product_id)
        normalized_status = metadata.provider_status.strip().lower()
        if normalized_status == "online" and metadata.trading_status is TradingStatus.ONLINE:
            status = MaintenanceStatus.CLEAR
            reason = "provider product is online with no disabled or cancel-only flag"
        elif "maintenance" in normalized_status:
            status = MaintenanceStatus.MAINTENANCE
            reason = "provider explicitly reports maintenance"
        else:
            status = MaintenanceStatus.UNKNOWN
            reason = "provider state does not prove whether venue maintenance is active"
        return VenueMaintenance(
            status=status,
            trading_status=metadata.trading_status,
            observed_at=metadata.metadata_timestamp,
            reason=reason,
        )

    def websocket_stream(
        self,
        product_id: str,
        *,
        stop_after_messages: int,
        deadline_utc: datetime,
    ) -> object:
        """Use the reviewed stream supervisor; import lazily to avoid transport cycles."""

        from tradeguard.adapters.crypto.stream import (  # noqa: PLC0415
            CoinbaseStreamSupervisor,
            WebsocketsPublicConnector,
        )

        product = self._normalize_product(product_id)
        if stop_after_messages < 1 or stop_after_messages > _MAX_STREAM_MESSAGES:
            raise CryptoScopeViolationError("stream message bound must be between 1 and 20")
        metadata = self.instrument_metadata(product)
        connector = self._websocket_connector or WebsocketsPublicConnector()
        return CoinbaseStreamSupervisor(
            connector=connector,
            product_metadata=metadata,
            clock=self._clock,
            sleeper=self._sleeper,
            stale_after_seconds=self._release_configuration.connected_smoke.stale_after_seconds,
            maximum_reconnects=self._release_configuration.connected_smoke.maximum_reconnects,
        ).run(
            stop_after_messages=stop_after_messages,
            deadline_utc=deadline_utc,
        )

    def _get_product(self, product: str) -> tuple[_ProductResponse, ProviderCallRecord]:
        response, call = self._request(f"/api/v3/brokerage/market/products/{product}")
        parsed = self._parse(response, _ProductResponse, "public product metadata")
        self._validate_product_identity(parsed)
        return parsed, call

    def _request(
        self,
        path: str,
        *,
        query: str = "",
    ) -> tuple[RestResponse, ProviderCallRecord]:
        url = f"{_REST_ROOT}{path}"
        if query:
            url = f"{url}?{query}"
        request = RestRequest(
            method="GET",
            url=url,
            headers={
                "Accept": "application/json",
                "Cache-Control": "no-cache",
                "User-Agent": "TradeGuard/0.1.0",
            },
            timeout_seconds=_TIMEOUT_SECONDS,
            max_response_bytes=_MAX_RESPONSE_BYTES,
        )
        attempts = 0
        while True:
            attempts += 1
            response = self._rest_transport.send(request)
            self._logger.info(
                "coinbase_public_response",
                extra={
                    "provider": "coinbase_advanced_trade",
                    "provider_path": path,
                    "provider_status": response.status_code,
                    "provider_attempt": attempts,
                },
            )
            if response.status_code != _HTTP_TOO_MANY_REQUESTS or attempts >= _MAX_ATTEMPTS:
                break
            self._sleeper(_retry_delay(response.headers))
        self._raise_for_status(response.status_code)
        return response, ProviderCallRecord(
            path=urlsplit(url).path,
            attempts=attempts,
            response_status=response.status_code,
            raw_response_sha256=hashlib.sha256(response.body).hexdigest(),
        )

    @staticmethod
    def _parse(
        response: RestResponse,
        model: type[_ProviderModelT],
        contract_name: str,
    ) -> _ProviderModelT:
        try:
            payload: Any = json.loads(response.body)
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise CryptoAdapterError(
                CryptoAdapterFailureCode.FAIL_SCHEMA_DRIFT,
                f"provider {contract_name} response is not valid UTF-8 JSON",
            ) from None
        try:
            return model.model_validate(payload)
        except ValidationError:
            raise CryptoAdapterError(
                CryptoAdapterFailureCode.FAIL_SCHEMA_DRIFT,
                f"provider {contract_name} response violates the reviewed required fields",
            ) from None

    @staticmethod
    def _validate_product_identity(product: _ProductResponse) -> None:
        if (
            product.product_id != _APPROVED_PRODUCT
            or product.product_type != "SPOT"
            or product.base_currency_id != "BTC"
            or product.quote_currency_id != "USD"
        ):
            raise CryptoAdapterError(
                CryptoAdapterFailureCode.FAIL_METADATA_CONFLICT,
                "provider product identity conflicts with the approved BTC-USD spot scope",
            )

    @staticmethod
    def _normalize_metadata(
        product: _ProductResponse,
        observed_at: datetime,
    ) -> TradingPairMetadata:
        CoinbaseCryptoMarketDataAdapter._validate_product_identity(product)
        status = (
            TradingStatus.ONLINE
            if product.status.strip().lower() == "online"
            and not product.is_disabled
            and not product.trading_disabled
            and not product.cancel_only
            and not product.view_only
            else TradingStatus.NOT_TRADABLE
        )
        listed_at = _utc_datetime(product.new_at, "new_at")
        raw_identity = {
            "product_id": product.product_id,
            "base_increment": product.base_increment,
            "quote_increment": product.quote_increment,
            "quote_min_size": product.quote_min_size,
            "base_min_size": product.base_min_size,
            "status": product.status,
            "is_disabled": product.is_disabled,
            "cancel_only": product.cancel_only,
            "trading_disabled": product.trading_disabled,
            "view_only": product.view_only,
            "price_increment": product.price_increment,
            "product_venue": product.product_venue,
        }
        instrument = InstrumentMetadata(
            source="coinbase-advanced-trade-public-rest",
            asset_class=AssetClass.CRYPTO,
            venue=_VENUE,
            symbol=_APPROVED_PRODUCT,
            canonical_symbol=_APPROVED_PRODUCT,
            quote_asset="USD",
            tick_size=_decimal(product.price_increment, "price_increment"),
            step_size=_decimal(product.base_increment, "base_increment"),
            lot_size=_decimal(product.base_increment, "base_increment"),
            minimum_quantity=_decimal(product.base_min_size, "base_min_size"),
            minimum_notional=_decimal(product.quote_min_size, "quote_min_size"),
            timezone="UTC",
            active_from=listed_at,
            known_at=observed_at,
            metadata_version=f"coinbase-public-{deterministic_checksum(raw_identity)[:16]}",
        )
        return TradingPairMetadata(
            instrument=instrument,
            base_asset="BTC",
            quote_asset="USD",
            trading_status=status,
            provider_status=product.status,
            metadata_timestamp=observed_at,
        )

    @staticmethod
    def _normalize_bars(
        response: _CandlesResponse,
        request: CryptoBarsRequest,
        observed_at: datetime,
    ) -> tuple[OHLCVBar, ...]:
        duration = timedelta(minutes=1)
        parsed: list[tuple[datetime, _Candle]] = []
        for candle in response.candles:
            try:
                start = datetime.fromtimestamp(int(candle.start), tz=UTC)
            except (ValueError, OSError, OverflowError):
                raise CryptoAdapterError(
                    CryptoAdapterFailureCode.FAIL_SCHEMA_DRIFT,
                    "provider candle start timestamp is invalid",
                ) from None
            end = start + duration
            if start < request.start or end > request.end or end > observed_at:
                raise CryptoAdapterError(
                    CryptoAdapterFailureCode.FAIL_DATA_QUALITY,
                    "provider returned an incomplete or out-of-range candle",
                )
            parsed.append((start, candle))
        parsed.sort(key=lambda item: item[0])
        if len(parsed) > request.limit:
            raise CryptoAdapterError(
                CryptoAdapterFailureCode.FAIL_SCHEMA_DRIFT,
                "provider returned more candles than requested",
            )
        return tuple(
            OHLCVBar(
                source="coinbase-advanced-trade-public-rest",
                asset_class=AssetClass.CRYPTO,
                venue=_VENUE,
                symbol=_APPROVED_PRODUCT,
                event_time_utc=start + duration,
                ingest_time_utc=observed_at,
                sequence_number=index,
                interval_start_utc=start,
                interval_end_utc=start + duration,
                open_price=_decimal(candle.open, "open"),
                high_price=_decimal(candle.high, "high"),
                low_price=_decimal(candle.low, "low"),
                close_price=_decimal(candle.close, "close"),
                volume=_decimal(candle.volume, "volume"),
            )
            for index, (start, candle) in enumerate(parsed, start=1)
        )

    @staticmethod
    def _normalize_trades(
        response: _TickerResponse,
        observed_at: datetime,
    ) -> tuple[Trade, ...]:
        parsed = []
        for provider_trade in response.trades:
            if provider_trade.product_id != _APPROVED_PRODUCT:
                raise CryptoAdapterError(
                    CryptoAdapterFailureCode.FAIL_METADATA_CONFLICT,
                    "provider trade product conflicts with the approved pair",
                )
            if provider_trade.side.upper() not in {"BUY", "SELL"}:
                raise CryptoAdapterError(
                    CryptoAdapterFailureCode.FAIL_SCHEMA_DRIFT,
                    "provider trade side is outside the reviewed schema",
                )
            event_time = _utc_datetime(provider_trade.time, "trade time")
            if event_time > observed_at:
                raise CryptoAdapterError(
                    CryptoAdapterFailureCode.FAIL_DATA_QUALITY,
                    "provider trade timestamp is in the future",
                )
            parsed.append((event_time, provider_trade))
        parsed.sort(key=lambda item: (item[0], item[1].trade_id))
        return tuple(
            Trade(
                source="coinbase-advanced-trade-public-rest",
                asset_class=AssetClass.CRYPTO,
                venue=_VENUE,
                symbol=_APPROVED_PRODUCT,
                event_time_utc=event_time,
                ingest_time_utc=observed_at,
                sequence_number=index,
                trade_id=provider_trade.trade_id,
                price=_decimal(provider_trade.price, "price"),
                quantity=_decimal(provider_trade.size, "size"),
                quote_asset="USD",
            )
            for index, (event_time, provider_trade) in enumerate(parsed, start=1)
        )

    @staticmethod
    def _dataset(  # noqa: PLR0913 - evidence inputs stay explicit
        *,
        records: tuple[OHLCVBar | Quote | Trade, ...],
        metadata: InstrumentMetadata,
        calls: tuple[ProviderCallRecord, ...],
        now: datetime,
        operation: str,
        expected_bar_interval_seconds: int = 60,
    ) -> CryptoDataset:
        if not records:
            raise CryptoAdapterError(
                CryptoAdapterFailureCode.FAIL_DATA_QUALITY,
                "provider returned no canonical market records",
            )
        manifest = _build_manifest(
            records=records,
            calls=calls,
            ingested_at=now,
            operation=operation,
        )
        report = QualityGate().validate(
            records,
            QualityContext(
                manifest=manifest,
                policy=QualityPolicy(
                    evaluated_at=now,
                    knowledge_time_utc=now,
                    expected_bar_interval_seconds=expected_bar_interval_seconds,
                    max_staleness_seconds=300,
                ),
                instrument_metadata=(metadata,),
            ),
        )
        if report.status in {QualityStatus.FAIL, QualityStatus.QUARANTINED}:
            raise CryptoAdapterError(
                CryptoAdapterFailureCode.FAIL_DATA_QUALITY,
                f"canonical data failed the quality gate with status {report.status.value}",
            )
        return CryptoDataset(
            records=records,
            manifest=manifest,
            quality_report=report,
            provider_calls=calls,
            warnings=(
                "public research feed only; not consolidated or execution-grade",
                "raw connected provider values are transient and prohibited from public evidence",
            ),
        )

    @staticmethod
    def _normalize_product(product_id: str) -> str:
        normalized = product_id.strip().upper()
        if normalized != _APPROVED_PRODUCT:
            raise CryptoScopeViolationError("product is outside the BTC-USD spot allowlist")
        return normalized

    def _normalized_now(self) -> datetime:
        value = self._clock()
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("adapter clock must return a timezone-aware datetime")
        return value.astimezone(UTC)

    @staticmethod
    def _raise_for_status(status_code: int) -> None:
        mapping = {
            400: (
                CryptoAdapterFailureCode.FAIL_REQUEST_REJECTED,
                "provider rejected the reviewed public request",
            ),
            401: (
                CryptoAdapterFailureCode.FAIL_SCOPE_VIOLATION,
                "public endpoint unexpectedly requested authentication",
            ),
            403: (
                CryptoAdapterFailureCode.FAIL_SCOPE_VIOLATION,
                "public endpoint access is not available under the approved boundary",
            ),
            404: (
                CryptoAdapterFailureCode.FAIL_REQUEST_REJECTED,
                "approved public market data was not found",
            ),
            429: (
                CryptoAdapterFailureCode.BLOCKED_RATE_LIMIT,
                "provider rate limit remained exhausted after the bounded retry",
            ),
        }
        if status_code in mapping:
            code, message = mapping[status_code]
            raise CryptoAdapterError(code, message)
        if _HTTP_SERVER_ERROR_MIN <= status_code <= _HTTP_SERVER_ERROR_MAX:
            raise CryptoAdapterError(
                CryptoAdapterFailureCode.BLOCKED_PROVIDER_UNAVAILABLE,
                "provider returned a server error",
            )
        if status_code < _HTTP_SUCCESS_MIN or status_code >= _HTTP_SUCCESS_MAX_EXCLUSIVE:
            raise CryptoAdapterError(
                CryptoAdapterFailureCode.FAIL_REQUEST_REJECTED,
                "provider returned an unreviewed HTTP status",
            )


def _build_manifest(
    *,
    records: Sequence[MarketDataRecord],
    calls: tuple[ProviderCallRecord, ...],
    ingested_at: datetime,
    operation: str,
) -> DatasetManifest:
    canonical_checksum = deterministic_checksum(tuple(canonicalize(record) for record in records))
    raw_checksums = tuple(call.raw_response_sha256 for call in calls)
    raw_bundle_checksum = deterministic_checksum(raw_checksums)
    dataset_id = f"coinbase-btc-usd-{canonical_checksum[:16]}"
    source_dataset_id = f"coinbase-public-response-{raw_bundle_checksum[:16]}"
    starts = [
        record.interval_start_utc if isinstance(record, OHLCVBar) else record.event_time_utc
        for record in records
    ]
    ends = [
        record.interval_end_utc if isinstance(record, OHLCVBar) else record.event_time_utc
        for record in records
    ]
    start = min(starts)
    end = max(ends)
    if end <= start:
        end = start + timedelta(microseconds=1)
    date_range = DataInterval(start_utc=start, end_utc=end)
    graph = TransformationGraph(
        steps=(
            TransformationStep(
                transformation_id=operation,
                operation="validate_map_public_provider_payload_to_canonical_crypto_records",
                implementation_version="1.0.0",
                input_dataset_ids=(source_dataset_id,),
                output_dataset_id=dataset_id,
                parameters_hash=deterministic_checksum(
                    {
                        "product_id": _APPROVED_PRODUCT,
                        "call_paths": tuple(call.path for call in calls),
                    }
                ),
            ),
        )
    )
    return DatasetManifest(
        dataset_id=dataset_id,
        dataset_version="1.0.0",
        source="coinbase-advanced-trade-public",
        asset_class=AssetClass.CRYPTO,
        symbols=(_APPROVED_PRODUCT,),
        date_range=date_range,
        row_count=len(records),
        partition_information=(
            DatasetPartition(
                partition_id="part-0000",
                relative_path=f"runtime/{dataset_id}/canonical-records.json",
                row_count=len(records),
                date_range=date_range,
                checksum=canonical_checksum,
            ),
        ),
        checksums={
            "canonical_records_sha256": canonical_checksum,
            "raw_response_bundle_sha256": raw_bundle_checksum,
        },
        created_at=ingested_at,
        ingested_at=ingested_at,
        licensing_notes=(
            "Coinbase public market data used for internal non-display research; raw connected "
            "values are transient and prohibited from Git and public release evidence."
        ),
        transformation_graph=graph,
    )


def _decimal(value: str, field: str) -> Decimal:
    try:
        parsed = Decimal(value)
    except (InvalidOperation, ValueError):
        raise CryptoAdapterError(
            CryptoAdapterFailureCode.FAIL_SCHEMA_DRIFT,
            f"provider {field} is not a valid decimal string",
        ) from None
    if not parsed.is_finite() or parsed < 0:
        raise CryptoAdapterError(
            CryptoAdapterFailureCode.FAIL_DATA_QUALITY,
            f"provider {field} is negative or non-finite",
        )
    return parsed


def _utc_datetime(value: str, field: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        raise CryptoAdapterError(
            CryptoAdapterFailureCode.FAIL_SCHEMA_DRIFT,
            f"provider {field} is not a valid timestamp",
        ) from None
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise CryptoAdapterError(
            CryptoAdapterFailureCode.FAIL_SCHEMA_DRIFT,
            f"provider {field} has no timezone",
        )
    return parsed.astimezone(UTC)


def _retry_delay(headers: Mapping[str, str]) -> float:
    raw = next(
        (value for name, value in headers.items() if name.lower() == "retry-after"),
        "1",
    )
    try:
        parsed = float(raw)
    except ValueError:
        parsed = 1.0
    return min(max(parsed, 0.0), _MAX_RETRY_AFTER_SECONDS)
