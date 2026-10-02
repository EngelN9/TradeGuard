"""Fixed R4 inputs shared by strategy tests and evidence."""

import hashlib
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID

from tradeguard.backtest.engine import DeterministicBacktester
from tradeguard.backtest.models import RunEnvironment
from tradeguard.data.package import DatasetPackage, load_dataset_package
from tradeguard.domain.serialization import deterministic_checksum
from tradeguard.strategies.models import StrategyRunArtifact, StrategyRunRequest
from tradeguard.strategies.runner import StrategyRunner

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
NORMAL_FIXTURE = REPOSITORY_ROOT / "tests" / "fixtures" / "market_data" / "normal.json"
FIXED_COMPLETION = datetime(2024, 1, 2, 1, 0, 1, tzinfo=UTC)


def strategy_request() -> StrategyRunRequest:
    return StrategyRunRequest(run_id=UUID("00000000-0000-4000-8000-000000000070"))


def strategy_environment() -> RunEnvironment:
    return RunEnvironment(
        git_sha="1" * 40,
        dirty_worktree=False,
        python_version="3.12.0",
        platform="test-platform",
        dependency_lock_hash="2" * 64,
        started_at=datetime(2024, 1, 2, 1, 0, tzinfo=UTC),
    )


def adverse_package() -> DatasetPackage:
    """Return the reviewed fixture with a declining final bar.

    The baseline holds to the end of the fixture, so a lower final close is the
    smallest input that produces an unfavourable result. It is an in-memory
    variant only: the runner still accepts the frozen fixture checksum alone.
    """

    package = load_dataset_package(NORMAL_FIXTURE)
    declining = dict(package.records[-1])
    declining.update(high_price="100.50", low_price="98.00", close_price="98.50")
    records = (*package.records[:-1], declining)
    manifest = package.manifest.model_copy(
        update={
            "checksums": {
                **package.manifest.checksums,
                "canonical_records_sha256": deterministic_checksum(records),
            }
        }
    )
    return package.model_copy(update={"manifest": manifest, "records": records})


def strategy_artifact() -> StrategyRunArtifact:
    package = load_dataset_package(NORMAL_FIXTURE)
    runner = StrategyRunner(
        backtester=DeterministicBacktester(completion_clock=lambda: FIXED_COMPLETION)
    )
    return runner.run(
        package=package,
        fixture_file_sha256=hashlib.sha256(NORMAL_FIXTURE.read_bytes()).hexdigest(),
        request=strategy_request(),
        environment=strategy_environment(),
    )
