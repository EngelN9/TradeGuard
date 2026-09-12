"""Export deterministic JSON Schema snapshots and a sample run manifest."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import UUID

from pydantic import TypeAdapter

from tradeguard.adapters.crypto.coinbase import reviewed_rest_schemas
from tradeguard.adapters.crypto.configuration import CoinbaseReleaseConfiguration
from tradeguard.adapters.crypto.connected import CryptoConnectedSmokeResult
from tradeguard.adapters.crypto.protocol import CryptoAdapterCapabilities, CryptoBarsRequest
from tradeguard.adapters.crypto.stream import StreamRunResult
from tradeguard.adapters.equity.calendar import ReviewedCalendarDocument
from tradeguard.adapters.equity.configuration import TwelveDataReleaseConfiguration
from tradeguard.adapters.equity.connected import ConnectedSmokeResult
from tradeguard.adapters.equity.protocol import EquityAdapterCapabilities, HistoricalBarsRequest
from tradeguard.adapters.equity.twelve_data import reviewed_time_series_schema
from tradeguard.backtest.models import (
    BacktestArtifact,
    BacktestPlan,
    FillLedgerEntry,
    OrderLedgerEntry,
    PnLLedgerEntry,
    PositionLedgerEntry,
)
from tradeguard.config.models import TradeGuardConfig
from tradeguard.data.manifest import DatasetManifest
from tradeguard.data.models import AnyMarketRecord, InstrumentMetadata
from tradeguard.data.package import DatasetPackage
from tradeguard.data.quality import QualityReport
from tradeguard.domain.events import AnyDomainEvent
from tradeguard.domain.serialization import canonicalize
from tradeguard.experiments.manifest import (
    DatasetManifestReference,
    RunDateRange,
    RunManifest,
    RunType,
)
from tradeguard.strategies.models import (
    BuyAndHoldParameters,
    StrategyRunArtifact,
    StrategyRunRequest,
    StrategySpecification,
    StrategySyntheticReport,
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_ROOT = REPOSITORY_ROOT / "schemas"


def sample_run_manifest() -> RunManifest:
    """Return a fixed, synthetic, clean run manifest."""

    started = datetime(2024, 1, 2, 0, 0, tzinfo=UTC)
    return RunManifest(
        run_id=UUID("00000000-0000-4000-8000-000000000010"),
        run_type=RunType.RESEARCH,
        strategy_id="disabled",
        strategy_version="0.0.0",
        git_sha="1" * 40,
        dirty_worktree=False,
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


def schema_documents() -> dict[str, object]:
    """Build every committed machine-readable contract artifact."""

    documents = {
        "domain-events.schema.json": TypeAdapter(AnyDomainEvent).json_schema(),
        "tradeguard-config.schema.json": TradeGuardConfig.model_json_schema(),
        "run-manifest.schema.json": RunManifest.model_json_schema(),
        "market-records.schema.json": TypeAdapter(AnyMarketRecord).json_schema(),
        "instrument-metadata.schema.json": InstrumentMetadata.model_json_schema(),
        "dataset-manifest.schema.json": DatasetManifest.model_json_schema(),
        "quality-report.schema.json": QualityReport.model_json_schema(),
        "dataset-package.schema.json": DatasetPackage.model_json_schema(),
        "backtest/plan.schema.json": BacktestPlan.model_json_schema(),
        "backtest/artifact.schema.json": BacktestArtifact.model_json_schema(),
        "backtest/order-ledger-entry.schema.json": OrderLedgerEntry.model_json_schema(),
        "backtest/fill-ledger-entry.schema.json": FillLedgerEntry.model_json_schema(),
        "backtest/position-ledger-entry.schema.json": PositionLedgerEntry.model_json_schema(),
        "backtest/pnl-ledger-entry.schema.json": PnLLedgerEntry.model_json_schema(),
        "strategies/specification.schema.json": StrategySpecification.model_json_schema(),
        "strategies/buy-and-hold-parameters.schema.json": (
            BuyAndHoldParameters.model_json_schema()
        ),
        "strategies/run-request.schema.json": StrategyRunRequest.model_json_schema(),
        "strategies/synthetic-report.schema.json": StrategySyntheticReport.model_json_schema(),
        "strategies/run-artifact.schema.json": StrategyRunArtifact.model_json_schema(),
        "adapters/equity-capabilities.schema.json": (EquityAdapterCapabilities.model_json_schema()),
        "adapters/equity-historical-bars-request.schema.json": (
            HistoricalBarsRequest.model_json_schema()
        ),
        "adapters/equity-connected-sessions.schema.json": (
            ReviewedCalendarDocument.model_json_schema()
        ),
        "adapters/twelve-data-release-configuration.schema.json": (
            TwelveDataReleaseConfiguration.model_json_schema()
        ),
        "adapters/twelve-data-time-series.schema.json": reviewed_time_series_schema(),
        "adapters/equity-connected-smoke-result.schema.json": (
            ConnectedSmokeResult.model_json_schema()
        ),
        "adapters/crypto-capabilities.schema.json": (CryptoAdapterCapabilities.model_json_schema()),
        "adapters/crypto-historical-bars-request.schema.json": (
            CryptoBarsRequest.model_json_schema()
        ),
        "adapters/coinbase-release-configuration.schema.json": (
            CoinbaseReleaseConfiguration.model_json_schema()
        ),
        "adapters/crypto-connected-smoke-result.schema.json": (
            CryptoConnectedSmokeResult.model_json_schema()
        ),
        "adapters/crypto-websocket-run-result.schema.json": StreamRunResult.model_json_schema(),
        "examples/sample-run-manifest.json": canonicalize(sample_run_manifest()),
    }
    documents.update(
        {
            f"adapters/coinbase-rest-{name}.schema.json": schema
            for name, schema in reviewed_rest_schemas().items()
        }
    )
    return documents


def write_document(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def main() -> int:
    for relative_path, document in schema_documents().items():
        write_document(SCHEMA_ROOT / relative_path, document)
    print(SCHEMA_ROOT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
