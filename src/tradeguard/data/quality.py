"""Deterministic, fail-closed quality gates for equity and crypto datasets."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping, Sequence
from datetime import timedelta
from decimal import Decimal
from enum import StrEnum
from itertools import pairwise
from typing import Annotated, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from tradeguard.data.manifest import DatasetManifest
from tradeguard.data.models import (
    MARKET_RECORD_ADAPTER,
    CorporateAction,
    CorporateActionType,
    InstrumentMetadata,
    MaintenanceInterval,
    MarketDataRecord,
    MarketSession,
    OHLCVBar,
    Quote,
    SessionStatus,
    Trade,
)
from tradeguard.domain.events import AssetClass
from tradeguard.domain.serialization import (
    AuthorityDecimal,
    CanonicalSerializationError,
    UtcDateTime,
    canonical_json,
    deterministic_checksum,
)

NonEmptyText = Annotated[str, Field(min_length=1, max_length=2048)]
Checksum = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
IssueContextValue = str | int | bool | None


class QualityStatus(StrEnum):
    PASS = "PASS"  # noqa: S105 - data-quality disposition, not a credential
    WARN = "WARN"
    FAIL = "FAIL"
    QUARANTINED = "QUARANTINED"


IssueStatus = Literal[
    QualityStatus.WARN,
    QualityStatus.FAIL,
    QualityStatus.QUARANTINED,
]


class QualityCode(StrEnum):
    MISSING = "missing"
    DUPLICATE = "duplicate"
    OUT_OF_ORDER = "out_of_order"
    FUTURE_TIMESTAMP = "future_timestamp"
    STALE_CONTENT = "stale_content"
    INVALID_OHLC = "invalid_ohlc"
    NEGATIVE_VOLUME = "negative_volume"
    ABNORMAL_PRICE_JUMP = "abnormal_price_jump"
    INCONSISTENT_SCHEMA = "inconsistent_schema"
    SYMBOL_MAPPING_CONFLICT = "symbol_mapping_conflict"
    TRADING_SESSION_VIOLATION = "trading_session_violation"
    HALF_DAY_HANDLING = "half_day_handling"
    CORPORATE_ACTION_MISMATCH = "corporate_action_mismatch"
    CORPORATE_ACTIONS_UNSUPPORTED = "corporate_actions_unsupported"
    SUSPECTED_UNMODELED_CORPORATE_ACTION = "suspected_unmodeled_corporate_action"
    SPLIT_DISCONTINUITY = "split_discontinuity"
    DELISTED_SYMBOL_HANDLING = "delisted_symbol_handling"
    POINT_IN_TIME_UNIVERSE_VIOLATION = "point_in_time_universe_violation"
    CRYPTO_24_7_GAP = "crypto_24_7_gap"
    PRECISION_MISMATCH = "precision_mismatch"
    MINIMUM_NOTIONAL_MISMATCH = "minimum_notional_mismatch"
    VENUE_MAINTENANCE_INTERVAL = "venue_maintenance_interval"
    BID_GREATER_THAN_ASK = "bid_greater_than_ask"
    SPREAD_ANOMALY = "spread_anomaly"
    QUOTE_ASSET_INCONSISTENCY = "quote_asset_inconsistency"


_STATUS_RANK = {
    QualityStatus.PASS: 0,
    QualityStatus.WARN: 1,
    QualityStatus.FAIL: 2,
    QualityStatus.QUARANTINED: 3,
}


class QualityModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", validate_default=True)


class QualityIssue(QualityModel):
    code: QualityCode
    status: IssueStatus
    message: NonEmptyText
    record_indexes: tuple[Annotated[int, Field(ge=0)], ...] = ()
    context: dict[str, IssueContextValue] = Field(default_factory=dict)


class QualityReport(QualityModel):
    """Checksummed result bound to a specific dataset manifest."""

    schema_version: Literal["1.0.0"] = "1.0.0"
    dataset_id: NonEmptyText
    manifest_checksum: Checksum
    evaluated_at: UtcDateTime
    status: QualityStatus
    issues: tuple[QualityIssue, ...]

    @model_validator(mode="after")
    def validate_derived_status(self) -> Self:
        expected = _overall_status(self.issues)
        if self.status is not expected:
            raise ValueError("quality report status does not match its issues")
        return self

    @classmethod
    def build(
        cls,
        *,
        manifest: DatasetManifest,
        evaluated_at: UtcDateTime,
        issues: Sequence[QualityIssue],
    ) -> QualityReport:
        ordered = tuple(
            sorted(
                issues,
                key=lambda issue: (
                    issue.code.value,
                    issue.record_indexes,
                    canonical_json(issue.context),
                    issue.message,
                ),
            )
        )
        return cls(
            dataset_id=manifest.dataset_id,
            manifest_checksum=manifest.checksum(),
            evaluated_at=evaluated_at,
            status=_overall_status(ordered),
            issues=ordered,
        )

    @property
    def admissible_for_validation_evidence(self) -> bool:
        return self.status in {QualityStatus.PASS, QualityStatus.WARN}

    def checksum(self) -> str:
        return deterministic_checksum(self)


class QualityPolicy(QualityModel):
    """Explicit deterministic thresholds and knowledge cut-off."""

    evaluated_at: UtcDateTime
    knowledge_time_utc: UtcDateTime
    expected_record_schema_version: str = "1.0.0"
    expected_bar_interval_seconds: Annotated[int, Field(gt=0)] = 60
    max_staleness_seconds: Annotated[int, Field(gt=0)] = 300
    max_price_jump_ratio: Annotated[AuthorityDecimal, Field(gt=0)] = Decimal("0.25")
    max_spread_ratio: Annotated[AuthorityDecimal, Field(gt=0)] = Decimal("0.05")
    split_tolerance_ratio: Annotated[AuthorityDecimal, Field(ge=0)] = Decimal("0.10")


class QualityContext(QualityModel):
    """All reviewed reference data used by a quality evaluation."""

    manifest: DatasetManifest
    policy: QualityPolicy
    instrument_metadata: tuple[InstrumentMetadata, ...]
    market_sessions: tuple[MarketSession, ...] = ()
    corporate_actions: tuple[CorporateAction, ...] = ()
    corporate_actions_supported: bool = True
    maintenance_intervals: tuple[MaintenanceInterval, ...] = ()


class ValidationEvidenceRejectedError(ValueError):
    """Raised when a dataset is not eligible to support validation evidence."""


def require_validation_evidence_eligible(
    manifest: DatasetManifest,
    report: QualityReport,
) -> None:
    """Fail closed unless the quality result is bound and PASS/WARN."""

    if report.dataset_id != manifest.dataset_id or report.manifest_checksum != manifest.checksum():
        raise ValidationEvidenceRejectedError(
            "quality report is not bound to this dataset manifest"
        )
    if not report.admissible_for_validation_evidence:
        raise ValidationEvidenceRejectedError(
            f"{report.status.value} datasets cannot enter validation evidence"
        )


def _overall_status(issues: Sequence[QualityIssue]) -> QualityStatus:
    if not issues:
        return QualityStatus.PASS
    return max((issue.status for issue in issues), key=_STATUS_RANK.__getitem__)


def _issue(
    code: QualityCode,
    status: IssueStatus,
    message: str,
    *record_indexes: int,
    context: Mapping[str, IssueContextValue] | None = None,
) -> QualityIssue:
    return QualityIssue(
        code=code,
        status=status,
        message=message,
        record_indexes=tuple(record_indexes),
        context=dict(context or {}),
    )


def _record_identity(record: MarketDataRecord) -> tuple[object, ...]:
    identity: tuple[object, ...] = (
        record.record_type,
        record.venue,
        record.symbol,
        record.event_time_utc,
    )
    if isinstance(record, Trade):
        return (*identity, record.trade_id)
    if isinstance(record, OHLCVBar):
        return (*identity, record.interval_start_utc, record.interval_end_utc)
    return identity


def _representative_price(record: MarketDataRecord) -> Decimal | None:
    if isinstance(record, Quote):
        if record.bid_price <= 0 or record.ask_price <= 0:
            return None
        return (record.bid_price + record.ask_price) / Decimal(2)
    if isinstance(record, Trade):
        return record.price if record.price > 0 else None
    if isinstance(record, OHLCVBar):
        return record.close_price if record.close_price > 0 else None
    return None


def _intervals_overlap(left: InstrumentMetadata, right: InstrumentMetadata) -> bool:
    left_end = left.active_to
    right_end = right.active_to
    return (right_end is None or left.active_from < right_end) and (
        left_end is None or right.active_from < left_end
    )


def _matching_metadata(
    record: MarketDataRecord,
    metadata: Sequence[InstrumentMetadata],
    knowledge_time: UtcDateTime,
) -> list[InstrumentMetadata]:
    return [
        item
        for item in metadata
        if item.asset_class is record.asset_class
        and item.venue == record.venue
        and item.symbol == record.symbol
        and item.is_point_in_time_valid(
            effective_at=record.event_time_utc,
            knowledge_time=knowledge_time,
        )
    ]


class QualityGate:
    """Apply shared and market-specific checks without changing source data."""

    def validate(
        self,
        raw_records: Sequence[Mapping[str, object] | MarketDataRecord],
        context: QualityContext,
    ) -> QualityReport:
        issues: list[QualityIssue] = []
        records = self._parse_records(raw_records, context, issues)
        self._check_shared(records, context, issues)
        self._check_metadata_conflicts(context.instrument_metadata, issues)
        if context.manifest.asset_class is AssetClass.EQUITY:
            self._check_equities(records, context, issues)
        else:
            self._check_crypto(records, context, issues)
        return QualityReport.build(
            manifest=context.manifest,
            evaluated_at=context.policy.evaluated_at,
            issues=issues,
        )

    @staticmethod
    def _parse_records(
        raw_records: Sequence[Mapping[str, object] | MarketDataRecord],
        context: QualityContext,
        issues: list[QualityIssue],
    ) -> list[tuple[int, MarketDataRecord]]:
        parsed: list[tuple[int, MarketDataRecord]] = []
        if len(raw_records) != context.manifest.row_count:
            status: IssueStatus = (
                QualityStatus.FAIL
                if len(raw_records) < context.manifest.row_count
                else QualityStatus.QUARANTINED
            )
            code = (
                QualityCode.MISSING
                if len(raw_records) < context.manifest.row_count
                else QualityCode.INCONSISTENT_SCHEMA
            )
            issues.append(
                _issue(
                    code,
                    status,
                    "record count does not match the bound dataset manifest",
                    context={
                        "expected_row_count": context.manifest.row_count,
                        "observed_row_count": len(raw_records),
                    },
                )
            )
        expected_records_checksum = context.manifest.checksums.get("canonical_records_sha256")
        try:
            observed_records_checksum = deterministic_checksum(raw_records)
        except CanonicalSerializationError:
            observed_records_checksum = None
        if (
            expected_records_checksum is None
            or observed_records_checksum != expected_records_checksum
        ):
            issues.append(
                _issue(
                    QualityCode.INCONSISTENT_SCHEMA,
                    QualityStatus.QUARANTINED,
                    "record content checksum does not match the dataset manifest",
                )
            )
        if not raw_records:
            issues.append(
                _issue(QualityCode.MISSING, QualityStatus.FAIL, "dataset contains no records")
            )
            return parsed
        for index, raw_record in enumerate(raw_records):
            try:
                record = (
                    raw_record
                    if isinstance(raw_record, MarketDataRecord)
                    else MARKET_RECORD_ADAPTER.validate_python(raw_record)
                )
            except ValidationError:
                issues.append(
                    _issue(
                        QualityCode.INCONSISTENT_SCHEMA,
                        QualityStatus.QUARANTINED,
                        "record does not match the canonical schema",
                        index,
                    )
                )
                continue
            if (
                record.schema_version != context.policy.expected_record_schema_version
                or record.asset_class is not context.manifest.asset_class
                or record.symbol not in context.manifest.symbols
            ):
                issues.append(
                    _issue(
                        QualityCode.INCONSISTENT_SCHEMA,
                        QualityStatus.QUARANTINED,
                        "record identity conflicts with the dataset manifest",
                        index,
                    )
                )
            parsed.append((index, record))
        return parsed

    def _check_shared(
        self,
        records: Sequence[tuple[int, MarketDataRecord]],
        context: QualityContext,
        issues: list[QualityIssue],
    ) -> None:
        self._check_duplicates_and_order(records, issues)
        self._check_timestamps(records, context.policy, issues)
        self._check_bars(records, issues)
        self._check_price_jumps(records, context.policy, issues)
        self._check_general_gaps(records, context, issues)
        self._check_point_in_time(records, context, issues)

    @staticmethod
    def _check_duplicates_and_order(
        records: Sequence[tuple[int, MarketDataRecord]],
        issues: list[QualityIssue],
    ) -> None:
        identities: dict[tuple[object, ...], int] = {}
        previous: tuple[int, MarketDataRecord] | None = None
        for index, record in records:
            identity = _record_identity(record)
            first_index = identities.get(identity)
            if first_index is not None:
                issues.append(
                    _issue(
                        QualityCode.DUPLICATE,
                        QualityStatus.FAIL,
                        "duplicate logical market-data record",
                        first_index,
                        index,
                    )
                )
            else:
                identities[identity] = index
            if previous is not None:
                previous_index, previous_record = previous
                if record.event_time_utc < previous_record.event_time_utc or (
                    record.event_time_utc == previous_record.event_time_utc
                    and record.sequence_number < previous_record.sequence_number
                ):
                    issues.append(
                        _issue(
                            QualityCode.OUT_OF_ORDER,
                            QualityStatus.FAIL,
                            "input record order moved backwards",
                            previous_index,
                            index,
                        )
                    )
            previous = (index, record)

    @staticmethod
    def _check_timestamps(
        records: Sequence[tuple[int, MarketDataRecord]],
        policy: QualityPolicy,
        issues: list[QualityIssue],
    ) -> None:
        for index, record in records:
            if (
                record.event_time_utc > policy.evaluated_at
                or record.ingest_time_utc > policy.evaluated_at
            ):
                issues.append(
                    _issue(
                        QualityCode.FUTURE_TIMESTAMP,
                        QualityStatus.QUARANTINED,
                        "record event or ingest time is in the future",
                        index,
                    )
                )
        if not records:
            return
        latest_event = max(record.event_time_utc for _, record in records)
        if latest_event < policy.evaluated_at - timedelta(seconds=policy.max_staleness_seconds):
            latest_ingest = max(record.ingest_time_utc for _, record in records)
            fresh_ingest = latest_ingest >= policy.evaluated_at - timedelta(
                seconds=policy.max_staleness_seconds
            )
            issues.append(
                _issue(
                    QualityCode.STALE_CONTENT,
                    QualityStatus.FAIL,
                    "dataset content is stale even if ingest timestamps appear fresh"
                    if fresh_ingest
                    else "dataset content is stale",
                    context={"fresh_ingest": fresh_ingest},
                )
            )

    @staticmethod
    def _check_bars(
        records: Sequence[tuple[int, MarketDataRecord]],
        issues: list[QualityIssue],
    ) -> None:
        for index, record in records:
            if not isinstance(record, OHLCVBar):
                continue
            if record.volume < 0:
                issues.append(
                    _issue(
                        QualityCode.NEGATIVE_VOLUME,
                        QualityStatus.QUARANTINED,
                        "bar volume is negative",
                        index,
                    )
                )
            if (
                min(
                    record.open_price,
                    record.high_price,
                    record.low_price,
                    record.close_price,
                )
                <= 0
                or record.high_price < max(record.open_price, record.close_price, record.low_price)
                or record.low_price > min(record.open_price, record.close_price, record.high_price)
            ):
                issues.append(
                    _issue(
                        QualityCode.INVALID_OHLC,
                        QualityStatus.QUARANTINED,
                        "bar violates positive-price or OHLC ordering rules",
                        index,
                    )
                )

    @staticmethod
    def _check_price_jumps(
        records: Sequence[tuple[int, MarketDataRecord]],
        policy: QualityPolicy,
        issues: list[QualityIssue],
    ) -> None:
        previous_by_symbol: dict[tuple[str, str], tuple[int, Decimal]] = {}
        for index, record in records:
            price = _representative_price(record)
            if price is None:
                continue
            key = (record.venue, record.symbol)
            previous = previous_by_symbol.get(key)
            if previous is not None:
                previous_index, previous_price = previous
                change = abs(price - previous_price) / previous_price
                if change > policy.max_price_jump_ratio:
                    issues.append(
                        _issue(
                            QualityCode.ABNORMAL_PRICE_JUMP,
                            QualityStatus.WARN,
                            "price change exceeds the reviewed threshold",
                            previous_index,
                            index,
                            context={"change_ratio": str(change)},
                        )
                    )
            previous_by_symbol[key] = (index, price)

    @staticmethod
    def _same_equity_session(
        left: OHLCVBar,
        right: OHLCVBar,
        sessions: Sequence[MarketSession],
        knowledge_time: UtcDateTime,
    ) -> bool:
        return any(
            session.venue == left.venue
            and session.venue == right.venue
            and session.known_at <= knowledge_time
            and session.session_open_utc <= left.interval_start_utc
            and left.interval_end_utc <= session.session_close_utc
            and session.session_open_utc <= right.interval_start_utc
            and right.interval_end_utc <= session.session_close_utc
            for session in sessions
        )

    def _check_general_gaps(
        self,
        records: Sequence[tuple[int, MarketDataRecord]],
        context: QualityContext,
        issues: list[QualityIssue],
    ) -> None:
        bars_by_symbol: dict[tuple[str, str], list[tuple[int, OHLCVBar]]] = defaultdict(list)
        for index, record in records:
            if isinstance(record, OHLCVBar):
                bars_by_symbol[(record.venue, record.symbol)].append((index, record))
        expected = timedelta(seconds=context.policy.expected_bar_interval_seconds)
        for bars in bars_by_symbol.values():
            ordered = sorted(bars, key=lambda item: item[1].interval_start_utc)
            for (left_index, left), (right_index, right) in pairwise(ordered):
                if right.interval_start_utc <= left.interval_end_utc:
                    continue
                gap = right.interval_start_utc - left.interval_end_utc
                if gap < expected:
                    continue
                if (
                    context.manifest.asset_class is AssetClass.EQUITY
                    and not self._same_equity_session(
                        left,
                        right,
                        context.market_sessions,
                        context.policy.knowledge_time_utc,
                    )
                ):
                    continue
                issues.append(
                    _issue(
                        QualityCode.MISSING,
                        QualityStatus.FAIL,
                        "expected bar interval is missing",
                        left_index,
                        right_index,
                        context={"gap_seconds": int(gap.total_seconds())},
                    )
                )

    @staticmethod
    def _check_metadata_conflicts(
        metadata: Sequence[InstrumentMetadata],
        issues: list[QualityIssue],
    ) -> None:
        for left_index, left in enumerate(metadata):
            for right_index in range(left_index + 1, len(metadata)):
                right = metadata[right_index]
                if (
                    left.asset_class is right.asset_class
                    and left.venue == right.venue
                    and left.symbol == right.symbol
                    and left.canonical_symbol != right.canonical_symbol
                    and _intervals_overlap(left, right)
                ):
                    issues.append(
                        _issue(
                            QualityCode.SYMBOL_MAPPING_CONFLICT,
                            QualityStatus.QUARANTINED,
                            "overlapping metadata maps one symbol to multiple canonical symbols",
                            context={
                                "left_metadata_index": left_index,
                                "right_metadata_index": right_index,
                            },
                        )
                    )

    @staticmethod
    def _check_point_in_time(
        records: Sequence[tuple[int, MarketDataRecord]],
        context: QualityContext,
        issues: list[QualityIssue],
    ) -> None:
        for index, record in records:
            candidates = _matching_metadata(
                record,
                context.instrument_metadata,
                context.policy.knowledge_time_utc,
            )
            if candidates:
                continue
            same_identity = [
                item
                for item in context.instrument_metadata
                if item.asset_class is record.asset_class
                and item.venue == record.venue
                and item.symbol == record.symbol
            ]
            if any(item.known_at > context.policy.knowledge_time_utc for item in same_identity):
                issues.append(
                    _issue(
                        QualityCode.POINT_IN_TIME_UNIVERSE_VIOLATION,
                        QualityStatus.QUARANTINED,
                        "instrument metadata was not known at the knowledge cut-off",
                        index,
                    )
                )
            elif any(
                item.active_to is not None and record.event_time_utc >= item.active_to
                for item in same_identity
            ):
                issues.append(
                    _issue(
                        QualityCode.DELISTED_SYMBOL_HANDLING,
                        QualityStatus.QUARANTINED,
                        "record occurs after the instrument became inactive",
                        index,
                    )
                )
            else:
                issues.append(
                    _issue(
                        QualityCode.SYMBOL_MAPPING_CONFLICT,
                        QualityStatus.QUARANTINED,
                        "no unambiguous point-in-time metadata exists for the record",
                        index,
                    )
                )

    def _check_equities(
        self,
        records: Sequence[tuple[int, MarketDataRecord]],
        context: QualityContext,
        issues: list[QualityIssue],
    ) -> None:
        self._check_equity_sessions(
            records,
            context.market_sessions,
            context.policy.knowledge_time_utc,
            issues,
        )
        self._check_corporate_actions(records, context, issues)
        if not context.corporate_actions_supported:
            issues.append(
                _issue(
                    QualityCode.CORPORATE_ACTIONS_UNSUPPORTED,
                    QualityStatus.WARN,
                    "corporate actions are unsupported; prices are unadjusted and total-return "
                    "claims are prohibited",
                )
            )
            self._check_suspected_unmodeled_corporate_actions(
                records,
                context.policy,
                issues,
            )

    @staticmethod
    def _check_suspected_unmodeled_corporate_actions(
        records: Sequence[tuple[int, MarketDataRecord]],
        policy: QualityPolicy,
        issues: list[QualityIssue],
    ) -> None:
        bars_by_symbol: dict[tuple[str, str], list[tuple[int, OHLCVBar]]] = defaultdict(list)
        for index, record in records:
            if isinstance(record, OHLCVBar):
                bars_by_symbol[(record.venue, record.symbol)].append((index, record))
        for bars in bars_by_symbol.values():
            ordered = sorted(bars, key=lambda item: item[1].event_time_utc)
            for (left_index, left), (right_index, right) in pairwise(ordered):
                if left.close_price <= 0:
                    continue
                discontinuity = abs(right.open_price - left.close_price) / left.close_price
                if discontinuity > policy.max_price_jump_ratio:
                    issues.append(
                        _issue(
                            QualityCode.SUSPECTED_UNMODELED_CORPORATE_ACTION,
                            QualityStatus.QUARANTINED,
                            "large unadjusted overnight discontinuity requires corporate-action "
                            "review; no split ratio was inferred",
                            left_index,
                            right_index,
                            context={"discontinuity_ratio": str(discontinuity)},
                        )
                    )

    @staticmethod
    def _record_in_session(record: MarketDataRecord, session: MarketSession) -> bool:
        if record.venue != session.venue or session.status is not SessionStatus.OPEN:
            return False
        if isinstance(record, OHLCVBar):
            return (
                session.session_open_utc <= record.interval_start_utc
                and record.interval_end_utc <= session.session_close_utc
            )
        return session.contains(record.event_time_utc)

    def _check_equity_sessions(
        self,
        records: Sequence[tuple[int, MarketDataRecord]],
        sessions: Sequence[MarketSession],
        knowledge_time: UtcDateTime,
        issues: list[QualityIssue],
    ) -> None:
        for index, record in records:
            if any(
                session.known_at <= knowledge_time and self._record_in_session(record, session)
                for session in sessions
            ):
                continue
            matching_day = [
                session
                for session in sessions
                if session.venue == record.venue
                and session.known_at <= knowledge_time
                and session.session_close_utc.date() == record.event_time_utc.date()
            ]
            if any(
                session.half_day and record.event_time_utc >= session.session_close_utc
                for session in matching_day
            ):
                code = QualityCode.HALF_DAY_HANDLING
                message = "record occurs after the reviewed half-day close"
            else:
                code = QualityCode.TRADING_SESSION_VIOLATION
                message = "record is outside every reviewed trading session"
            issues.append(_issue(code, QualityStatus.FAIL, message, index))

    def _check_corporate_actions(
        self,
        records: Sequence[tuple[int, MarketDataRecord]],
        context: QualityContext,
        issues: list[QualityIssue],
    ) -> None:
        bars = [(index, record) for index, record in records if isinstance(record, OHLCVBar)]
        for action in context.corporate_actions:
            metadata_matches = [
                metadata
                for metadata in context.instrument_metadata
                if metadata.asset_class is AssetClass.EQUITY
                and metadata.venue == action.venue
                and metadata.symbol == action.symbol
                and metadata.is_known_at(context.policy.knowledge_time_utc)
            ]
            structurally_valid = (
                bool(metadata_matches) and action.known_at <= context.policy.knowledge_time_utc
            )
            if action.action_type in {
                CorporateActionType.SPLIT,
                CorporateActionType.REVERSE_SPLIT,
            }:
                structurally_valid = (
                    structurally_valid and action.ratio is not None and action.ratio > 0
                )
            elif action.action_type is CorporateActionType.SYMBOL_CHANGE:
                structurally_valid = structurally_valid and bool(action.new_symbol)
            elif action.action_type is CorporateActionType.CASH_DIVIDEND:
                structurally_valid = (
                    structurally_valid
                    and action.cash_amount is not None
                    and action.cash_amount >= 0
                    and bool(action.currency)
                )
            if not structurally_valid:
                issues.append(
                    _issue(
                        QualityCode.CORPORATE_ACTION_MISMATCH,
                        QualityStatus.QUARANTINED,
                        "corporate action conflicts with point-in-time metadata or required fields",
                    )
                )
                continue
            if action.action_type not in {
                CorporateActionType.SPLIT,
                CorporateActionType.REVERSE_SPLIT,
            }:
                continue
            self._check_split_discontinuity(action, bars, context.policy, issues)

    @staticmethod
    def _check_split_discontinuity(
        action: CorporateAction,
        bars: Sequence[tuple[int, OHLCVBar]],
        policy: QualityPolicy,
        issues: list[QualityIssue],
    ) -> None:
        if action.ratio is None or action.ratio <= 0:
            return
        matching = [
            (index, bar)
            for index, bar in bars
            if bar.venue == action.venue and bar.symbol == action.symbol
        ]
        before = [
            (index, bar) for index, bar in matching if bar.event_time_utc <= action.effective_at
        ]
        after = [
            (index, bar) for index, bar in matching if bar.event_time_utc > action.effective_at
        ]
        if not before or not after:
            return
        before_index, before_bar = max(before, key=lambda item: item[1].event_time_utc)
        after_index, after_bar = min(after, key=lambda item: item[1].event_time_utc)
        expected = before_bar.close_price / action.ratio
        if expected <= 0:
            return
        deviation = abs(after_bar.open_price - expected) / expected
        if deviation > policy.split_tolerance_ratio:
            issues.append(
                _issue(
                    QualityCode.SPLIT_DISCONTINUITY,
                    QualityStatus.FAIL,
                    "observed split transition exceeds the reviewed tolerance",
                    before_index,
                    after_index,
                    context={"deviation_ratio": str(deviation)},
                )
            )

    def _check_crypto(
        self,
        records: Sequence[tuple[int, MarketDataRecord]],
        context: QualityContext,
        issues: list[QualityIssue],
    ) -> None:
        self._check_crypto_gaps(records, context.policy, issues)
        for index, record in records:
            metadata = _matching_metadata(
                record,
                context.instrument_metadata,
                context.policy.knowledge_time_utc,
            )
            if metadata:
                self._check_crypto_precision_and_notional(index, record, metadata[0], issues)
                self._check_quote_asset(index, record, metadata[0], issues)
            if any(
                interval.venue == record.venue
                and interval.known_at <= context.policy.knowledge_time_utc
                and interval.contains(record.event_time_utc)
                for interval in context.maintenance_intervals
            ):
                issues.append(
                    _issue(
                        QualityCode.VENUE_MAINTENANCE_INTERVAL,
                        QualityStatus.FAIL,
                        "record occurs during a known venue-maintenance interval",
                        index,
                    )
                )
            if isinstance(record, Quote):
                self._check_crypto_quote(index, record, context.policy, issues)

    @staticmethod
    def _check_crypto_gaps(
        records: Sequence[tuple[int, MarketDataRecord]],
        policy: QualityPolicy,
        issues: list[QualityIssue],
    ) -> None:
        bars_by_symbol: dict[tuple[str, str], list[tuple[int, OHLCVBar]]] = defaultdict(list)
        for index, record in records:
            if isinstance(record, OHLCVBar):
                bars_by_symbol[(record.venue, record.symbol)].append((index, record))
        expected = timedelta(seconds=policy.expected_bar_interval_seconds)
        for bars in bars_by_symbol.values():
            ordered = sorted(bars, key=lambda item: item[1].interval_start_utc)
            for (left_index, left), (right_index, right) in pairwise(ordered):
                gap = right.interval_start_utc - left.interval_end_utc
                if gap >= expected:
                    issues.append(
                        _issue(
                            QualityCode.CRYPTO_24_7_GAP,
                            QualityStatus.FAIL,
                            "crypto bar coverage has a 24/7 interval gap",
                            left_index,
                            right_index,
                            context={"gap_seconds": int(gap.total_seconds())},
                        )
                    )

    @staticmethod
    def _is_increment(value: Decimal, increment: Decimal) -> bool:
        return value >= 0 and value % increment == 0

    def _check_crypto_precision_and_notional(
        self,
        index: int,
        record: MarketDataRecord,
        metadata: InstrumentMetadata,
        issues: list[QualityIssue],
    ) -> None:
        prices: tuple[Decimal, ...]
        quantities: tuple[Decimal, ...]
        if isinstance(record, Quote):
            prices = (record.bid_price, record.ask_price)
            quantities = (record.bid_quantity, record.ask_quantity)
        elif isinstance(record, Trade):
            prices = (record.price,)
            quantities = (record.quantity,)
        elif isinstance(record, OHLCVBar):
            prices = (
                record.open_price,
                record.high_price,
                record.low_price,
                record.close_price,
            )
            quantities = (record.volume,)
        else:
            return
        if not all(self._is_increment(value, metadata.tick_size) for value in prices) or not all(
            self._is_increment(value, metadata.step_size) for value in quantities
        ):
            issues.append(
                _issue(
                    QualityCode.PRECISION_MISMATCH,
                    QualityStatus.QUARANTINED,
                    "price or quantity violates instrument precision",
                    index,
                )
            )
        if (
            isinstance(record, Trade)
            and record.price > 0
            and record.quantity > 0
            and record.price * record.quantity < metadata.minimum_notional
        ):
            issues.append(
                _issue(
                    QualityCode.MINIMUM_NOTIONAL_MISMATCH,
                    QualityStatus.FAIL,
                    "trade notional is below instrument minimum_notional",
                    index,
                )
            )

    @staticmethod
    def _check_quote_asset(
        index: int,
        record: MarketDataRecord,
        metadata: InstrumentMetadata,
        issues: list[QualityIssue],
    ) -> None:
        if isinstance(record, Quote | Trade) and record.quote_asset != metadata.quote_asset:
            issues.append(
                _issue(
                    QualityCode.QUOTE_ASSET_INCONSISTENCY,
                    QualityStatus.QUARANTINED,
                    "record quote asset conflicts with point-in-time metadata",
                    index,
                )
            )

    @staticmethod
    def _check_crypto_quote(
        index: int,
        quote: Quote,
        policy: QualityPolicy,
        issues: list[QualityIssue],
    ) -> None:
        if quote.bid_price > quote.ask_price:
            issues.append(
                _issue(
                    QualityCode.BID_GREATER_THAN_ASK,
                    QualityStatus.QUARANTINED,
                    "bid price exceeds ask price",
                    index,
                )
            )
            return
        midpoint = (quote.bid_price + quote.ask_price) / Decimal(2)
        if midpoint <= 0:
            issues.append(
                _issue(
                    QualityCode.INCONSISTENT_SCHEMA,
                    QualityStatus.QUARANTINED,
                    "quote midpoint must be positive",
                    index,
                )
            )
            return
        spread_ratio = (quote.ask_price - quote.bid_price) / midpoint
        if spread_ratio > policy.max_spread_ratio:
            issues.append(
                _issue(
                    QualityCode.SPREAD_ANOMALY,
                    QualityStatus.WARN,
                    "relative spread exceeds the reviewed threshold",
                    index,
                    context={"spread_ratio": str(spread_ratio)},
                )
            )
