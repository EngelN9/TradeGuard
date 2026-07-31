"""Twelve Data daily-equity adapter constrained to the reviewed v0.1.0 scope."""

from __future__ import annotations

import hashlib
import json
import logging
import re
import time
from collections.abc import Callable, Mapping
from datetime import UTC, date, datetime
from decimal import Decimal, InvalidOperation
from typing import Annotated, Any, Literal
from urllib.parse import urlencode

from pydantic import BaseModel, ConfigDict, Field, SecretStr, StrictStr, ValidationError

from tradeguard.adapters.equity.calendar import (
    DeterministicMicCalendarRegistry,
    MarketCalendarUnavailableError,
)
from tradeguard.adapters.equity.configuration import TwelveDataReleaseConfiguration
from tradeguard.adapters.equity.errors import (
    AdapterFailureCode,
    EquityAdapterError,
    ScopeViolationError,
    UnsupportedCapabilityError,
)
from tradeguard.adapters.equity.protocol import (
    EquityAdapterCapabilities,
    EquityDataset,
    HistoricalBarsRequest,
    ProviderCallRecord,
)
from tradeguard.adapters.equity.transport import (
    HttpRequest,
    HttpResponse,
    HttpTransport,
    UrllibHttpsTransport,
)
from tradeguard.data.lineage import TransformationGraph, TransformationStep
from tradeguard.data.manifest import DataInterval, DatasetManifest, DatasetPartition
from tradeguard.data.models import CorporateAction, InstrumentMetadata, MarketSession, OHLCVBar
from tradeguard.data.quality import (
    QualityContext,
    QualityGate,
    QualityPolicy,
    QualityStatus,
)
from tradeguard.domain.events import AssetClass
from tradeguard.domain.serialization import canonicalize, deterministic_checksum

_LOGGER = logging.getLogger(__name__)
_APPROVED_SYMBOL = "AAPL"
_APPROVED_MICS = frozenset({"XNAS", "XNGS"})
_APPROVED_TIMEZONE = "America/New_York"
_MAX_RESPONSE_BYTES = 1_048_576
_TIMEOUT_SECONDS = 10.0
_MAX_RETRY_AFTER_SECONDS = 2.0
_MAX_ATTEMPTS = 2
_HTTP_TOO_MANY_REQUESTS = 429
_HTTP_SERVER_ERROR_MIN = 500
_HTTP_SERVER_ERROR_MAX = 599
_HTTP_SUCCESS_MIN = 200
_HTTP_SUCCESS_MAX_EXCLUSIVE = 300
_ISO_DATE_LENGTH = 10
_SAFE_REQUEST_ID = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")


class _ProviderModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", validate_default=True)


class _TimeSeriesMeta(_ProviderModel):
    symbol: StrictStr
    interval: StrictStr
    currency: StrictStr
    exchange_timezone: StrictStr
    exchange: StrictStr
    mic_code: StrictStr
    instrument_type: StrictStr = Field(alias="type")


class _TimeSeriesValue(_ProviderModel):
    datetime: StrictStr
    open: StrictStr
    high: StrictStr
    low: StrictStr
    close: StrictStr
    volume: StrictStr


class _TimeSeriesResponse(_ProviderModel):
    meta: _TimeSeriesMeta
    values: Annotated[tuple[_TimeSeriesValue, ...], Field(min_length=1, max_length=10)]
    status: Literal["ok"]


def reviewed_time_series_schema() -> dict[str, Any]:
    """Return the strict provider-side schema used only at the adapter boundary."""

    return _TimeSeriesResponse.model_json_schema()


class TwelveDataEquityAdapter:
    """Authenticated market-data-only adapter with no broker or order capability."""

    def __init__(  # noqa: PLR0913 - dependencies are explicit and independently testable
        self,
        *,
        api_key: SecretStr,
        calendar_registry: DeterministicMicCalendarRegistry,
        release_configuration: TwelveDataReleaseConfiguration,
        transport: HttpTransport | None = None,
        clock: Callable[[], datetime] | None = None,
        sleeper: Callable[[float], None] | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        if not api_key.get_secret_value().strip():
            raise EquityAdapterError(
                AdapterFailureCode.BLOCKED_INVALID_CREDENTIAL,
                "market-data credential is empty",
            )
        self._api_key = api_key
        self._calendar_registry = calendar_registry
        self._release_configuration = release_configuration
        self._transport = transport or UrllibHttpsTransport()
        self._clock = clock or (lambda: datetime.now(UTC))
        self._sleeper = sleeper or time.sleep
        self._logger = logger or _LOGGER

    @property
    def capabilities(self) -> EquityAdapterCapabilities:
        return self._release_configuration.capabilities

    def normalize_symbol(self, symbol: str) -> str:
        normalized = symbol.strip().upper()
        if normalized != _APPROVED_SYMBOL:
            raise ScopeViolationError("symbol is outside the approved v0.1.0 allowlist")
        return normalized

    def instrument_metadata(self, symbol: str, mic: str) -> InstrumentMetadata:
        normalized_symbol = self.normalize_symbol(symbol)
        normalized_mic = self._normalize_mic(mic)
        return InstrumentMetadata(
            source="tradeguard-reviewed-instrument-registry",
            asset_class=AssetClass.EQUITY,
            venue=normalized_mic,
            symbol=normalized_symbol,
            canonical_symbol=normalized_symbol,
            currency="USD",
            tick_size=Decimal("0.01"),
            step_size=Decimal("1"),
            lot_size=Decimal("1"),
            minimum_quantity=Decimal("1"),
            minimum_notional=Decimal("0"),
            timezone=_APPROVED_TIMEZONE,
            session_calendar=normalized_mic,
            active_from=datetime(2024, 1, 1, tzinfo=UTC),
            known_at=datetime(2023, 12, 1, tzinfo=UTC),
            metadata_version="tradeguard-reviewed-2026-07-31",
        )

    def historical_bars(self, request: HistoricalBarsRequest) -> EquityDataset:
        symbol = self.normalize_symbol(request.symbol)
        self._normalize_mic(request.mic)
        now = self._normalized_now()
        response, call_record = self._request_time_series(request, symbol)
        parsed = self._parse_response(response)
        self._validate_meta(parsed.meta, symbol)
        self._validate_response_range(parsed, request)
        records, sessions = self._normalize_bars(parsed, now)
        manifest = self._build_manifest(
            request=request,
            records=records,
            ingested_at=now,
            raw_response_sha256=call_record.raw_response_sha256,
        )
        context = QualityContext(
            manifest=manifest,
            policy=QualityPolicy(
                evaluated_at=now,
                knowledge_time_utc=now,
                expected_bar_interval_seconds=86_400,
                max_staleness_seconds=259_200,
            ),
            instrument_metadata=(self.instrument_metadata(symbol, parsed.meta.mic_code),),
            market_sessions=sessions,
            corporate_actions=(),
            corporate_actions_supported=False,
        )
        report = QualityGate().validate(records, context)
        if report.status in {QualityStatus.FAIL, QualityStatus.QUARANTINED}:
            raise EquityAdapterError(
                AdapterFailureCode.FAIL_DATA_QUALITY,
                f"canonical data failed the quality gate with status {report.status.value}",
            )
        return EquityDataset(
            records=records,
            manifest=manifest,
            quality_report=report,
            provider_call=call_record,
            warnings=(
                "corporate actions unsupported; adjust=none; total-return claims prohibited",
                "feed is not consolidated, NBBO, full-market-volume, or execution-grade",
            ),
        )

    def latest_bar(self, symbol: str, mic: str) -> OHLCVBar:
        dataset = self.historical_bars(HistoricalBarsRequest(symbol=symbol, mic=mic, output_size=1))
        return dataset.records[-1]

    def market_calendar(
        self,
        mic: str,
        start_date: date,
        end_date: date,
    ) -> tuple[MarketSession, ...]:
        return self._calendar_registry.sessions_between(
            self._normalize_mic(mic),
            start_date,
            end_date,
        )

    def timezone(self, symbol: str, mic: str) -> str:
        self.normalize_symbol(symbol)
        self._normalize_mic(mic)
        return _APPROVED_TIMEZONE

    def corporate_actions(
        self,
        symbol: str,
        mic: str,
        start_date: date,
        end_date: date,
    ) -> tuple[CorporateAction, ...]:
        self.normalize_symbol(symbol)
        self._normalize_mic(mic)
        if end_date < start_date:
            raise ValueError("end_date must not precede start_date")
        raise UnsupportedCapabilityError("corporate-action retrieval")

    def _request_time_series(
        self,
        request: HistoricalBarsRequest,
        symbol: str,
    ) -> tuple[HttpResponse, ProviderCallRecord]:
        params = [
            ("symbol", symbol),
            ("interval", request.interval),
            ("outputsize", str(request.output_size)),
            ("exchange", "NASDAQ"),
            ("format", "JSON"),
            ("adjust", request.adjustment),
            ("order", "ASC"),
        ]
        if request.start_date is not None:
            params.append(("start_date", request.start_date.isoformat()))
        if request.end_date is not None:
            params.append(("end_date", request.end_date.isoformat()))
        url = f"https://api.twelvedata.com/time_series?{urlencode(params)}"
        http_request = HttpRequest(
            method="GET",
            url=url,
            headers={
                "Accept": "application/json",
                "Authorization": f"apikey {self._api_key.get_secret_value()}",
                "User-Agent": "TradeGuard/0.1.0",
            },
            timeout_seconds=_TIMEOUT_SECONDS,
            max_response_bytes=_MAX_RESPONSE_BYTES,
        )
        attempts = 0
        while True:
            attempts += 1
            response = self._transport.send(http_request)
            request_id = _safe_request_id(_header(response.headers, "x-request-id", "request-id"))
            self._logger.info(
                "twelve_data_response",
                extra={
                    "provider": "twelve_data",
                    "provider_request_id": request_id,
                    "provider_status": response.status_code,
                    "provider_attempt": attempts,
                },
            )
            if response.status_code != _HTTP_TOO_MANY_REQUESTS or attempts >= _MAX_ATTEMPTS:
                break
            self._sleeper(_retry_delay(response.headers))
        self._raise_for_status(response.status_code)
        return response, ProviderCallRecord(
            request_id=request_id,
            attempts=attempts,
            response_status=response.status_code,
            raw_response_sha256=hashlib.sha256(response.body).hexdigest(),
        )

    @staticmethod
    def _parse_response(response: HttpResponse) -> _TimeSeriesResponse:
        try:
            payload: Any = json.loads(response.body)
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise EquityAdapterError(
                AdapterFailureCode.FAIL_SCHEMA_DRIFT,
                "provider response is not valid UTF-8 JSON",
            ) from None
        if isinstance(payload, Mapping) and payload.get("status") == "error":
            code = payload.get("code")
            if isinstance(code, int):
                TwelveDataEquityAdapter._raise_for_status(code)
            raise EquityAdapterError(
                AdapterFailureCode.FAIL_REQUEST_REJECTED,
                "provider returned a structured request error",
            )
        try:
            return _TimeSeriesResponse.model_validate(payload)
        except ValidationError:
            raise EquityAdapterError(
                AdapterFailureCode.FAIL_SCHEMA_DRIFT,
                "provider response does not match the reviewed time-series schema",
            ) from None

    @staticmethod
    def _validate_meta(meta: _TimeSeriesMeta, symbol: str) -> None:
        if (
            meta.symbol.strip().upper() != symbol
            or meta.interval != "1day"
            or meta.currency != "USD"
            or meta.exchange.strip().upper() != "NASDAQ"
            or meta.mic_code not in _APPROVED_MICS
            or meta.exchange_timezone != _APPROVED_TIMEZONE
            or meta.instrument_type.strip().lower() != "common stock"
        ):
            raise EquityAdapterError(
                AdapterFailureCode.FAIL_SCHEMA_DRIFT,
                "provider metadata conflicts with the approved instrument scope",
            )

    @staticmethod
    def _validate_response_range(
        response: _TimeSeriesResponse,
        request: HistoricalBarsRequest,
    ) -> None:
        if len(response.values) > request.output_size:
            raise EquityAdapterError(
                AdapterFailureCode.FAIL_SCHEMA_DRIFT,
                "provider returned more rows than the reviewed request allowed",
            )
        for value in response.values:
            session_date = _parse_session_date(value.datetime)
            if (request.start_date is not None and session_date < request.start_date) or (
                request.end_date is not None and session_date > request.end_date
            ):
                raise EquityAdapterError(
                    AdapterFailureCode.FAIL_SCHEMA_DRIFT,
                    "provider returned a session outside the requested date range",
                )

    def _normalize_bars(
        self,
        response: _TimeSeriesResponse,
        ingested_at: datetime,
    ) -> tuple[tuple[OHLCVBar, ...], tuple[MarketSession, ...]]:
        parsed_values = []
        for value in response.values:
            session_date = _parse_session_date(value.datetime)
            try:
                session = self._calendar_registry.require_session(
                    response.meta.mic_code,
                    session_date,
                )
            except MarketCalendarUnavailableError as exc:
                raise EquityAdapterError(
                    AdapterFailureCode.BLOCKED_MARKET_CALENDAR,
                    "provider date is absent from the reviewed MIC session registry",
                ) from exc
            if session.session_close_utc > ingested_at:
                continue
            parsed_values.append((session, value))
        parsed_values.sort(key=lambda item: item[0].session_open_utc)
        if not parsed_values:
            raise EquityAdapterError(
                AdapterFailureCode.FAIL_DATA_QUALITY,
                "provider returned no completed reviewed sessions",
            )
        bars = tuple(
            OHLCVBar(
                source="twelve-data",
                asset_class=AssetClass.EQUITY,
                venue=response.meta.mic_code,
                symbol=response.meta.symbol.strip().upper(),
                event_time_utc=session.session_close_utc,
                ingest_time_utc=ingested_at,
                sequence_number=index,
                interval_start_utc=session.session_open_utc,
                interval_end_utc=session.session_close_utc,
                open_price=_parse_decimal(value.open, "open"),
                high_price=_parse_decimal(value.high, "high"),
                low_price=_parse_decimal(value.low, "low"),
                close_price=_parse_decimal(value.close, "close"),
                volume=_parse_decimal(value.volume, "volume"),
            )
            for index, (session, value) in enumerate(parsed_values, start=1)
        )
        sessions = tuple(session for session, _ in parsed_values)
        return bars, sessions

    @staticmethod
    def _build_manifest(
        *,
        request: HistoricalBarsRequest,
        records: tuple[OHLCVBar, ...],
        ingested_at: datetime,
        raw_response_sha256: str,
    ) -> DatasetManifest:
        record_documents = tuple(canonicalize(record) for record in records)
        canonical_checksum = deterministic_checksum(record_documents)
        dataset_id = f"twelve-data-aapl-1day-{canonical_checksum[:16]}"
        source_dataset_id = f"twelve-data-response-{raw_response_sha256[:16]}"
        date_range = DataInterval(
            start_utc=records[0].interval_start_utc,
            end_utc=records[-1].interval_end_utc,
        )
        request_parameters = {
            "symbol": request.symbol,
            "mic": request.mic,
            "interval": request.interval,
            "output_size": request.output_size,
            "start_date": request.start_date,
            "end_date": request.end_date,
            "adjustment": request.adjustment,
        }
        graph = TransformationGraph(
            steps=(
                TransformationStep(
                    transformation_id="normalize-twelve-data-time-series-v1",
                    operation="validate_map_exchange_session_to_canonical_ohlcv",
                    implementation_version="1.0.0",
                    input_dataset_ids=(source_dataset_id,),
                    output_dataset_id=dataset_id,
                    parameters_hash=deterministic_checksum(request_parameters),
                ),
            )
        )
        return DatasetManifest(
            dataset_id=dataset_id,
            dataset_version="1.0.0",
            source="twelve-data",
            asset_class=AssetClass.EQUITY,
            symbols=(_APPROVED_SYMBOL,),
            date_range=date_range,
            row_count=len(records),
            partition_information=(
                DatasetPartition(
                    partition_id="part-0000",
                    relative_path=f"runtime/{dataset_id}/canonical-bars.json",
                    row_count=len(records),
                    date_range=date_range,
                    checksum=canonical_checksum,
                ),
            ),
            checksums={
                "canonical_records_sha256": canonical_checksum,
                "raw_response_sha256": raw_response_sha256,
            },
            created_at=ingested_at,
            ingested_at=ingested_at,
            licensing_notes=(
                "Twelve Data internal non-display use only; redistribution and public display "
                "prohibited; public evidence contains no raw market values."
            ),
            transformation_graph=graph,
        )

    @staticmethod
    def _normalize_mic(mic: str) -> str:
        normalized = mic.strip().upper()
        if normalized not in _APPROVED_MICS:
            raise ScopeViolationError("MIC is outside the approved XNAS/XNGS allowlist")
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
                AdapterFailureCode.FAIL_REQUEST_REJECTED,
                "provider rejected the reviewed request",
            ),
            401: (
                AdapterFailureCode.BLOCKED_INVALID_CREDENTIAL,
                "market-data credential was rejected",
            ),
            403: (
                AdapterFailureCode.BLOCKED_ENTITLEMENT,
                "account lacks the required market-data entitlement",
            ),
            404: (
                AdapterFailureCode.FAIL_REQUEST_REJECTED,
                "approved market data was not found",
            ),
            429: (
                AdapterFailureCode.BLOCKED_RATE_LIMIT,
                "provider rate limit remained exhausted after the bounded retry",
            ),
        }
        if status_code in mapping:
            code, message = mapping[status_code]
            raise EquityAdapterError(code, message)
        if _HTTP_SERVER_ERROR_MIN <= status_code <= _HTTP_SERVER_ERROR_MAX:
            raise EquityAdapterError(
                AdapterFailureCode.BLOCKED_PROVIDER_UNAVAILABLE,
                "approved market-data provider returned a server error",
            )
        if status_code < _HTTP_SUCCESS_MIN or status_code >= _HTTP_SUCCESS_MAX_EXCLUSIVE:
            raise EquityAdapterError(
                AdapterFailureCode.FAIL_REQUEST_REJECTED,
                "provider returned an unreviewed HTTP status",
            )


def _parse_session_date(value: str) -> date:
    if len(value) != _ISO_DATE_LENGTH:
        raise EquityAdapterError(
            AdapterFailureCode.FAIL_DATA_QUALITY,
            "daily bar timestamp is not an exchange-local session date",
        )
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise EquityAdapterError(
            AdapterFailureCode.FAIL_DATA_QUALITY,
            "daily bar timestamp is invalid",
        ) from None


def _parse_decimal(value: str, field_name: str) -> Decimal:
    try:
        parsed = Decimal(value)
    except InvalidOperation:
        raise EquityAdapterError(
            AdapterFailureCode.FAIL_DATA_QUALITY,
            f"provider {field_name} value is not a valid decimal",
        ) from None
    if not parsed.is_finite():
        raise EquityAdapterError(
            AdapterFailureCode.FAIL_DATA_QUALITY,
            f"provider {field_name} value is not finite",
        )
    return parsed


def _header(headers: Mapping[str, str], *names: str) -> str | None:
    normalized = {key.lower(): value for key, value in headers.items()}
    return next((normalized[name] for name in names if name in normalized), None)


def _safe_request_id(value: str | None) -> str | None:
    if value is None or _SAFE_REQUEST_ID.fullmatch(value) is None:
        return None
    return value


def _retry_delay(headers: Mapping[str, str]) -> float:
    raw = _header(headers, "retry-after")
    if raw is None:
        return 1.0
    try:
        return min(max(float(raw), 0.0), _MAX_RETRY_AFTER_SECONDS)
    except ValueError:
        return 1.0
