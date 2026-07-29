"""Export deterministic JSON Schema snapshots and a sample run manifest."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import UUID

from pydantic import TypeAdapter

from tradeguard.config.models import TradeGuardConfig
from tradeguard.domain.events import AnyDomainEvent
from tradeguard.domain.serialization import canonicalize
from tradeguard.experiments.manifest import (
    DatasetManifestReference,
    RunDateRange,
    RunManifest,
    RunType,
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

    return {
        "domain-events.schema.json": TypeAdapter(AnyDomainEvent).json_schema(),
        "tradeguard-config.schema.json": TradeGuardConfig.model_json_schema(),
        "run-manifest.schema.json": RunManifest.model_json_schema(),
        "examples/sample-run-manifest.json": canonicalize(sample_run_manifest()),
    }


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
