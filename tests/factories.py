"""Deterministic test factories shared across contract suites."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from uuid import UUID

from tradeguard.config.loader import load_effective_config
from tradeguard.config.models import EffectiveConfig
from tradeguard.domain.events import AssetClass, Quote
from tradeguard.experiments.manifest import (
    DatasetManifestReference,
    RunDateRange,
    RunManifest,
    RunType,
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
EVENT_TIME = datetime(2024, 1, 2, 14, 30, tzinfo=UTC)
INGEST_TIME = EVENT_TIME + timedelta(seconds=1)


def event_fields() -> dict[str, object]:
    return {
        "event_id": UUID("00000000-0000-4000-8000-000000000001"),
        "source": "deterministic-fixture",
        "asset_class": AssetClass.EQUITY,
        "venue": "XNYS",
        "symbol": "SPY",
        "event_time_utc": EVENT_TIME,
        "ingest_time_utc": INGEST_TIME,
        "sequence_number": 1,
        "correlation_id": UUID("00000000-0000-4000-8000-000000000002"),
        "causation_id": None,
        "run_id": UUID("00000000-0000-4000-8000-000000000003"),
    }


def quote_event() -> Quote:
    return Quote.build(
        **event_fields(),
        bid_price=Decimal("499.99"),
        ask_price=Decimal("500.01"),
        bid_quantity=Decimal("10"),
        ask_quantity=Decimal("12"),
    )


def research_config_paths() -> tuple[Path, ...]:
    return (
        REPOSITORY_ROOT / "configs" / "base.yaml",
        REPOSITORY_ROOT / "configs" / "research.yaml",
        REPOSITORY_ROOT / "configs" / "markets" / "equities_cash.yaml",
        REPOSITORY_ROOT / "configs" / "venues" / "mock.yaml",
        REPOSITORY_ROOT / "configs" / "data" / "fixtures.yaml",
        REPOSITORY_ROOT / "configs" / "strategies" / "disabled.yaml",
        REPOSITORY_ROOT / "configs" / "portfolio" / "research.yaml",
        REPOSITORY_ROOT / "configs" / "risk" / "research.yaml",
        REPOSITORY_ROOT / "configs" / "costs" / "research.yaml",
        REPOSITORY_ROOT / "configs" / "monitoring" / "default.yaml",
        REPOSITORY_ROOT / "configs" / "alerting" / "default.yaml",
    )


def research_effective_config() -> EffectiveConfig:
    return load_effective_config(research_config_paths())


def completed_run_manifest(*, dirty: bool = False) -> RunManifest:
    started = datetime(2024, 1, 2, 0, 0, tzinfo=UTC)
    return RunManifest(
        run_id=UUID("00000000-0000-4000-8000-000000000010"),
        run_type=RunType.RESEARCH,
        strategy_id="disabled",
        strategy_version="0.0.0",
        git_sha="1" * 40,
        dirty_worktree=dirty,
        config_hash="2" * 64,
        dataset_manifests=(
            DatasetManifestReference(
                dataset_id="synthetic-equity-bars",
                dataset_version="1.0.0",
                checksum="3" * 64,
            ),
        ),
        date_range=RunDateRange(
            start_utc=started,
            end_utc=started + timedelta(days=30),
        ),
        universe=("SPY",),
        random_seed=7,
        python_version="3.12.0",
        platform="linux-x86_64",
        dependency_lock_hash="4" * 64,
        cost_model_version="conservative-bootstrap-v1",
        execution_model_version="none",
        started_at=started,
        completed_at=started + timedelta(minutes=1),
        result_checksum="5" * 64,
        warnings=("synthetic fixture only",),
        validation_failures=(),
    )
