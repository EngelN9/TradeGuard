"""Generate deterministic, synthetic-only R4 strategy review evidence."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID

from pydantic import ValidationError

from tradeguard.backtest.engine import DeterministicBacktester
from tradeguard.backtest.models import RunEnvironment
from tradeguard.data.fixtures import build_fixture
from tradeguard.data.package import load_dataset_package
from tradeguard.domain.serialization import canonicalize, deterministic_checksum
from tradeguard.strategies.buy_and_hold import (
    EXPECTED_FIXTURE_SHA256,
    BuyAndHoldBtcUsd,
    buy_and_hold_specification,
)
from tradeguard.strategies.models import (
    BuyAndHoldParameters,
    StrategyBar,
    StrategyRunArtifact,
    StrategyRunRequest,
    StrategySpecification,
)
from tradeguard.strategies.runner import StrategyRejectedError, StrategyRunner

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_ROOT = REPOSITORY_ROOT / "artifacts" / "evidence" / "r4"
FIXTURE_PATH = REPOSITORY_ROOT / "tests" / "fixtures" / "market_data" / "normal.json"
FIXED_TIME = datetime(2024, 1, 2, 1, 0, tzinfo=UTC)


def _environment() -> RunEnvironment:
    return RunEnvironment(
        git_sha="0" * 40,
        dirty_worktree=True,
        python_version="3.12.0-synthetic-evidence",
        platform="redacted-synthetic-runner",
        dependency_lock_hash=hashlib.sha256((REPOSITORY_ROOT / "uv.lock").read_bytes()).hexdigest(),
        started_at=FIXED_TIME,
    )


def _request() -> StrategyRunRequest:
    return StrategyRunRequest(run_id=UUID("00000000-0000-4000-8000-000000000070"))


def _runner() -> StrategyRunner:
    return StrategyRunner(
        backtester=DeterministicBacktester(
            completion_clock=lambda: datetime(2024, 1, 2, 1, 0, 1, tzinfo=UTC)
        )
    )


def _write(name: str, value: object) -> None:
    EVIDENCE_ROOT.mkdir(parents=True, exist_ok=True)
    (EVIDENCE_ROOT / name).write_text(
        json.dumps(canonicalize(value), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _collect_rejections() -> None:
    unsupported_code = "not_rejected"
    try:
        _runner().run(
            package=build_fixture("stock_split"),
            fixture_file_sha256=EXPECTED_FIXTURE_SHA256,
            request=_request(),
            environment=_environment(),
        )
    except StrategyRejectedError as exc:
        unsupported_code = exc.code.value
    if unsupported_code != "unsupported_market":
        raise RuntimeError("unsupported market did not fail closed")
    _write(
        "unsupported-market-rejection.json",
        {
            "schema_version": "1.0.0",
            "synthetic_only": True,
            "candidate_market": "SYNTH-XNYS:ACME",
            "accepted": False,
            "rejection_code": unsupported_code,
        },
    )

    class UndeclaredDataStrategy(BuyAndHoldBtcUsd):
        @property
        def specification(self) -> StrategySpecification:
            base = buy_and_hold_specification()
            return base.model_copy(update={"required_data": (*base.required_data, "volume")})

    undeclared_code = "not_rejected"
    try:
        _runner().run(
            package=load_dataset_package(FIXTURE_PATH),
            fixture_file_sha256=_sha256(FIXTURE_PATH),
            request=_request(),
            environment=_environment(),
            strategy=UndeclaredDataStrategy(BuyAndHoldParameters()),
        )
    except StrategyRejectedError as exc:
        undeclared_code = exc.code.value
    if undeclared_code != "undeclared_data":
        raise RuntimeError("undeclared data requirement did not fail closed")
    _write(
        "undeclared-data-rejection.json",
        {
            "schema_version": "1.0.0",
            "synthetic_only": True,
            "requested_field": "volume",
            "allowed_strategy_bar_fields": sorted(StrategyBar.model_fields),
            "accepted": False,
            "rejection_code": undeclared_code,
        },
    )


def _collect_tamper_rejection(artifact: StrategyRunArtifact) -> None:
    direct = artifact.model_dump(mode="python")
    direct["artifact_checksum"] = "f" * 64
    direct_accepted = True
    try:
        StrategyRunArtifact.model_validate(direct)
    except ValidationError:
        direct_accepted = False

    semantic = artifact.model_dump(mode="python")
    semantic["specification"]["strategy_version"] = "1.0.1"
    semantic["artifact_checksum"] = deterministic_checksum(
        {key: value for key, value in semantic.items() if key != "artifact_checksum"}
    )
    recomputed_accepted = True
    try:
        StrategyRunArtifact.model_validate(semantic)
    except ValidationError:
        recomputed_accepted = False
    if direct_accepted or recomputed_accepted:
        raise RuntimeError("tampered strategy artifact passed validation")
    _write(
        "tamper-rejection.json",
        {
            "schema_version": "1.0.0",
            "synthetic_only": True,
            "direct_checksum_tamper_accepted": direct_accepted,
            "recomputed_checksum_semantic_tamper_accepted": recomputed_accepted,
        },
    )


def main() -> int:
    package = load_dataset_package(FIXTURE_PATH)
    first = _runner().run(
        package=package,
        fixture_file_sha256=_sha256(FIXTURE_PATH),
        request=_request(),
        environment=_environment(),
    )
    second = _runner().run(
        package=package,
        fixture_file_sha256=_sha256(FIXTURE_PATH),
        request=_request(),
        environment=_environment(),
    )
    _write(
        "strategy-contract.json",
        {
            "schema_version": "1.0.0",
            "synthetic_only": True,
            "specification": first.specification,
            "parameters": first.parameters,
            "strategy_version_hash": first.strategy_version_hash,
            "strategy_bar_fields": sorted(StrategyBar.model_fields),
            "dynamic_loading_supported": False,
            "provider_access_supported": False,
            "credential_access_supported": False,
            "risk_approval_implied": False,
            "external_order_supported": False,
        },
    )
    _write("synthetic-run.json", first)
    _write(
        "determinism.json",
        {
            "schema_version": "1.0.0",
            "synthetic_only": True,
            "strategy_version_hash": first.strategy_version_hash,
            "first_artifact_checksum": first.artifact_checksum,
            "second_artifact_checksum": second.artifact_checksum,
            "first_result_checksum": first.backtest.result.result_checksum,
            "second_result_checksum": second.backtest.result.result_checksum,
            "first_report_checksum": first.report.report_checksum,
            "second_report_checksum": second.report.report_checksum,
            "identical": first.artifact_checksum == second.artifact_checksum,
        },
    )
    _collect_rejections()
    _collect_tamper_rejection(first)
    entries = [
        {"path": path.name, "sha256": _sha256(path)}
        for path in sorted(EVIDENCE_ROOT.iterdir())
        if path.is_file() and path.name != "index.json"
    ]
    _write(
        "index.json",
        {
            "schema_version": "1.0.0",
            "evidence_stage": "r4-strategy-candidate",
            "synthetic_only": True,
            "promotion_status": "NOT_EVALUATED",
            "artifacts": entries,
        },
    )
    print(EVIDENCE_ROOT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
