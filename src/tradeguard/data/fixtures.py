"""Deterministic synthetic fixtures; no external market data is used."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from tradeguard.data.lineage import TransformationGraph, TransformationStep
from tradeguard.data.manifest import (
    DataInterval,
    DatasetManifest,
    DatasetPartition,
    MissingInterval,
    ParentDataset,
)
from tradeguard.data.models import (
    CorporateAction,
    CorporateActionType,
    InstrumentMetadata,
    MaintenanceInterval,
    MarketSession,
    OHLCVBar,
    Quote,
    RecordType,
    SessionStatus,
    SupportedAssetClass,
    Trade,
)
from tradeguard.data.package import DatasetPackage
from tradeguard.data.quality import QualityPolicy, QualityStatus
from tradeguard.domain.events import AssetClass
from tradeguard.domain.serialization import canonicalize, deterministic_checksum

FIXTURE_EVALUATED_AT = datetime(2024, 1, 2, 0, 5, tzinfo=UTC)
FIXTURE_SCENARIOS = (
    "normal",
    "gap",
    "duplicate",
    "out_of_order",
    "bad_tick",
    "stock_split",
    "symbol_change",
    "delisting",
    "crypto_maintenance",
    "stale_timestamp",
    "fresh_timestamp_stale_content",
)


def _crypto_metadata() -> InstrumentMetadata:
    return InstrumentMetadata(
        source="synthetic",
        asset_class=AssetClass.CRYPTO,
        venue="SYNTH-CRYPTO",
        symbol="BTC-USD",
        canonical_symbol="BTC/USD",
        quote_asset="USD",
        tick_size=Decimal("0.01"),
        step_size=Decimal("0.0001"),
        lot_size=Decimal("0.0001"),
        minimum_quantity=Decimal("0.0001"),
        minimum_notional=Decimal("10"),
        timezone="UTC",
        active_from=datetime(2020, 1, 1, tzinfo=UTC),
        known_at=datetime(2020, 1, 1, tzinfo=UTC),
        metadata_version="synthetic-v1",
    )


def _equity_metadata(*, active_to: datetime | None = None) -> InstrumentMetadata:
    return InstrumentMetadata(
        source="synthetic",
        asset_class=AssetClass.EQUITY,
        venue="SYNTH-XNYS",
        symbol="ACME",
        canonical_symbol="ACME",
        currency="USD",
        tick_size=Decimal("0.01"),
        step_size=Decimal("1"),
        lot_size=Decimal("1"),
        minimum_quantity=Decimal("1"),
        minimum_notional=Decimal("1"),
        timezone="America/New_York",
        session_calendar="SYNTH-XNYS",
        active_from=datetime(2020, 1, 1, tzinfo=UTC),
        active_to=active_to,
        known_at=datetime(2020, 1, 1, tzinfo=UTC),
        metadata_version="synthetic-v1",
    )


def _bar(  # noqa: PLR0913 - explicit fixture fields keep scenarios reviewable
    *,
    asset_class: SupportedAssetClass = AssetClass.CRYPTO,
    venue: str = "SYNTH-CRYPTO",
    symbol: str = "BTC-USD",
    start: datetime,
    open_price: str = "100.00",
    high_price: str = "101.00",
    low_price: str = "99.00",
    close_price: str = "100.00",
    volume: str = "1.0000",
    sequence_number: int = 1,
    ingest_time: datetime | None = None,
) -> OHLCVBar:
    end = start + timedelta(minutes=1)
    return OHLCVBar(
        record_type=RecordType.BAR,
        source="synthetic",
        asset_class=asset_class,
        venue=venue,
        symbol=symbol,
        event_time_utc=end,
        ingest_time_utc=ingest_time or end,
        sequence_number=sequence_number,
        interval_start_utc=start,
        interval_end_utc=end,
        open_price=Decimal(open_price),
        high_price=Decimal(high_price),
        low_price=Decimal(low_price),
        close_price=Decimal(close_price),
        volume=Decimal(volume),
    )


def _trade(*, price: str, quantity: str, event_time: datetime) -> Trade:
    return Trade(
        source="synthetic",
        asset_class=AssetClass.CRYPTO,
        venue="SYNTH-CRYPTO",
        symbol="BTC-USD",
        event_time_utc=event_time,
        ingest_time_utc=event_time,
        sequence_number=1,
        trade_id="synthetic-trade-1",
        price=Decimal(price),
        quantity=Decimal(quantity),
        quote_asset="USD",
    )


def _record_documents(
    records: tuple[OHLCVBar | Quote | Trade, ...],
) -> tuple[dict[str, object], ...]:
    documents = []
    for record in records:
        document = canonicalize(record)
        if not isinstance(document, dict):
            raise TypeError("fixture record must canonicalize to a mapping")
        documents.append(document)
    return tuple(documents)


def _manifest(  # noqa: PLR0913 - manifest evidence is intentionally explicit
    *,
    scenario: str,
    asset_class: SupportedAssetClass,
    records: tuple[dict[str, object], ...],
    start: datetime,
    end: datetime,
    evaluated_at: datetime,
    missing_intervals: tuple[MissingInterval, ...] = (),
) -> DatasetManifest:
    dataset_id = f"synthetic-{scenario}"
    content_checksum = deterministic_checksum(records)
    source_id = f"{dataset_id}-raw"
    graph = TransformationGraph(
        steps=(
            TransformationStep(
                transformation_id=f"normalize-{scenario}",
                operation="canonicalize_synthetic_fixture",
                implementation_version="1.0.0",
                input_dataset_ids=(source_id,),
                output_dataset_id=dataset_id,
                parameters_hash=deterministic_checksum({"scenario": scenario}),
            ),
        )
    )
    partition = DatasetPartition(
        partition_id="part-0000",
        relative_path=f"{scenario}/part-0000.json",
        row_count=len(records),
        date_range=DataInterval(start_utc=start, end_utc=end),
        checksum=content_checksum,
    )
    symbol = "ACME" if asset_class is AssetClass.EQUITY else "BTC-USD"
    return DatasetManifest(
        dataset_id=dataset_id,
        dataset_version="1.0.0",
        source="synthetic-fixture-generator",
        asset_class=asset_class,
        symbols=(symbol,),
        date_range=DataInterval(start_utc=start, end_utc=end),
        row_count=len(records),
        partition_information=(partition,),
        checksums={"canonical_records_sha256": content_checksum},
        created_at=evaluated_at,
        ingested_at=evaluated_at,
        licensing_notes="Synthetic fixture; Apache-2.0; no external market data.",
        missing_intervals=missing_intervals,
        corrections=(),
        parent_dataset=ParentDataset(
            dataset_id=source_id,
            manifest_checksum=deterministic_checksum({"source": source_id}),
        ),
        transformation_graph=graph,
    )


def _package(  # noqa: PLR0913 - scenario composition is intentionally explicit
    *,
    scenario: str,
    asset_class: SupportedAssetClass,
    records: tuple[OHLCVBar | Quote | Trade, ...],
    expected_status: QualityStatus,
    metadata: tuple[InstrumentMetadata, ...],
    sessions: tuple[MarketSession, ...] = (),
    actions: tuple[CorporateAction, ...] = (),
    maintenance: tuple[MaintenanceInterval, ...] = (),
    missing_intervals: tuple[MissingInterval, ...] = (),
    evaluated_at: datetime | None = None,
) -> DatasetPackage:
    documents = _record_documents(records)
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
    effective_evaluated_at = evaluated_at or end + timedelta(minutes=1)
    manifest = _manifest(
        scenario=scenario,
        asset_class=asset_class,
        records=documents,
        start=start,
        end=end,
        evaluated_at=effective_evaluated_at,
        missing_intervals=missing_intervals,
    )
    return DatasetPackage(
        manifest=manifest,
        policy=QualityPolicy(
            evaluated_at=effective_evaluated_at,
            knowledge_time_utc=effective_evaluated_at,
        ),
        instrument_metadata=metadata,
        market_sessions=sessions,
        corporate_actions=actions,
        maintenance_intervals=maintenance,
        records=documents,  # type: ignore[arg-type]
        expected_quality_status=expected_status,
    )


def _crypto_bars() -> tuple[OHLCVBar, OHLCVBar]:
    first = _bar(start=datetime(2024, 1, 2, 0, 3, tzinfo=UTC), sequence_number=1)
    second = _bar(
        start=datetime(2024, 1, 2, 0, 4, tzinfo=UTC),
        open_price="100.00",
        high_price="102.00",
        low_price="99.00",
        close_price="101.00",
        sequence_number=2,
    )
    return first, second


def _equity_session(day: int, *, half_day: bool = False) -> MarketSession:
    return MarketSession(
        source="synthetic",
        venue="SYNTH-XNYS",
        session_calendar="SYNTH-XNYS",
        session_open_utc=datetime(2024, 1, day, 14, 30, tzinfo=UTC),
        session_close_utc=datetime(2024, 1, day, 18 if half_day else 21, 0, tzinfo=UTC),
        known_at=datetime(2023, 12, 1, tzinfo=UTC),
        status=SessionStatus.OPEN,
        half_day=half_day,
    )


def build_fixture(scenario: str) -> DatasetPackage:  # noqa: PLR0911
    """Build one named deterministic fixture."""

    if scenario not in FIXTURE_SCENARIOS:
        raise ValueError(f"unknown synthetic fixture: {scenario}")
    metadata = (_crypto_metadata(),)
    first, second = _crypto_bars()

    if scenario == "normal":
        return _package(
            scenario=scenario,
            asset_class=AssetClass.CRYPTO,
            records=(first, second),
            expected_status=QualityStatus.PASS,
            metadata=metadata,
        )
    if scenario == "gap":
        gap_start = datetime(2024, 1, 2, 0, 2, tzinfo=UTC)
        gap_end = datetime(2024, 1, 2, 0, 3, tzinfo=UTC)
        left = _bar(start=datetime(2024, 1, 2, 0, 1, tzinfo=UTC), sequence_number=1)
        right = _bar(start=gap_end, sequence_number=2)
        return _package(
            scenario=scenario,
            asset_class=AssetClass.CRYPTO,
            records=(left, right),
            expected_status=QualityStatus.FAIL,
            metadata=metadata,
            missing_intervals=(
                MissingInterval(
                    date_range=DataInterval(start_utc=gap_start, end_utc=gap_end),
                    reason="synthetic gap",
                ),
            ),
        )
    if scenario == "duplicate":
        return _package(
            scenario=scenario,
            asset_class=AssetClass.CRYPTO,
            records=(second, second),
            expected_status=QualityStatus.FAIL,
            metadata=metadata,
        )
    if scenario == "out_of_order":
        return _package(
            scenario=scenario,
            asset_class=AssetClass.CRYPTO,
            records=(second, first),
            expected_status=QualityStatus.FAIL,
            metadata=metadata,
        )
    if scenario == "bad_tick":
        trade = _trade(
            price="100.005",
            quantity="0.00015",
            event_time=datetime(2024, 1, 2, 0, 5, tzinfo=UTC),
        )
        return _package(
            scenario=scenario,
            asset_class=AssetClass.CRYPTO,
            records=(trade,),
            expected_status=QualityStatus.QUARANTINED,
            metadata=metadata,
        )
    if scenario == "crypto_maintenance":
        maintenance = MaintenanceInterval(
            venue="SYNTH-CRYPTO",
            start_utc=datetime(2024, 1, 2, 0, 3, tzinfo=UTC),
            end_utc=datetime(2024, 1, 2, 0, 4, 30, tzinfo=UTC),
            known_at=datetime(2024, 1, 1, tzinfo=UTC),
            reason="synthetic maintenance",
        )
        return _package(
            scenario=scenario,
            asset_class=AssetClass.CRYPTO,
            records=(first,),
            expected_status=QualityStatus.FAIL,
            metadata=metadata,
            maintenance=(maintenance,),
        )
    if scenario in {"stale_timestamp", "fresh_timestamp_stale_content"}:
        event_start = datetime(2024, 1, 1, 23, 0, tzinfo=UTC)
        ingest = (
            FIXTURE_EVALUATED_AT
            if scenario == "fresh_timestamp_stale_content"
            else event_start + timedelta(minutes=1)
        )
        stale = _bar(start=event_start, ingest_time=ingest)
        return _package(
            scenario=scenario,
            asset_class=AssetClass.CRYPTO,
            records=(stale,),
            expected_status=QualityStatus.FAIL,
            metadata=metadata,
            evaluated_at=FIXTURE_EVALUATED_AT,
        )

    action_time = datetime(2024, 1, 2, 14, 30, tzinfo=UTC)
    equity_metadata = (_equity_metadata(),)
    sessions = (_equity_session(1), _equity_session(2))
    before = _bar(
        asset_class=AssetClass.EQUITY,
        venue="SYNTH-XNYS",
        symbol="ACME",
        start=datetime(2024, 1, 1, 20, 58, tzinfo=UTC),
        open_price="100.00",
        high_price="101.00",
        low_price="99.00",
        close_price="100.00",
        volume="1000",
        sequence_number=1,
    )
    after = _bar(
        asset_class=AssetClass.EQUITY,
        venue="SYNTH-XNYS",
        symbol="ACME",
        start=datetime(2024, 1, 2, 14, 30, tzinfo=UTC),
        open_price="50.00",
        high_price="51.00",
        low_price="49.00",
        close_price="50.00",
        volume="2000",
        sequence_number=2,
    )
    if scenario == "stock_split":
        action = CorporateAction(
            source="synthetic",
            venue="SYNTH-XNYS",
            symbol="ACME",
            action_type=CorporateActionType.SPLIT,
            effective_at=action_time,
            known_at=datetime(2023, 12, 15, tzinfo=UTC),
            action_version="synthetic-v1",
            ratio=Decimal("2"),
        )
        return _package(
            scenario=scenario,
            asset_class=AssetClass.EQUITY,
            records=(before, after),
            expected_status=QualityStatus.WARN,
            metadata=equity_metadata,
            sessions=sessions,
            actions=(action,),
        )
    if scenario == "symbol_change":
        action = CorporateAction(
            source="synthetic",
            venue="SYNTH-XNYS",
            symbol="ACME",
            action_type=CorporateActionType.SYMBOL_CHANGE,
            effective_at=datetime(2024, 1, 3, tzinfo=UTC),
            known_at=datetime(2023, 12, 15, tzinfo=UTC),
            action_version="synthetic-v1",
            new_symbol="ACM2",
        )
        return _package(
            scenario=scenario,
            asset_class=AssetClass.EQUITY,
            records=(before,),
            expected_status=QualityStatus.PASS,
            metadata=equity_metadata,
            sessions=sessions,
            actions=(action,),
        )
    delisted_at = datetime(2024, 1, 2, 14, 0, tzinfo=UTC)
    return _package(
        scenario=scenario,
        asset_class=AssetClass.EQUITY,
        records=(after,),
        expected_status=QualityStatus.QUARANTINED,
        metadata=(_equity_metadata(active_to=delisted_at),),
        sessions=sessions,
    )


def all_fixtures() -> dict[str, DatasetPackage]:
    """Return all required scenarios in deterministic name order."""

    return {scenario: build_fixture(scenario) for scenario in FIXTURE_SCENARIOS}
