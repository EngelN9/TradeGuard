"""Fixed R4 inputs shared by strategy tests and evidence."""

import hashlib
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID

from tradeguard.backtest.engine import DeterministicBacktester
from tradeguard.backtest.models import RunEnvironment
from tradeguard.data.package import load_dataset_package
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
