"""Generate deterministic, synthetic-only Prompt 6 review evidence."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from uuid import UUID

from pydantic import ValidationError

from tradeguard.backtest.engine import BacktestRejectedError, DeterministicBacktester
from tradeguard.backtest.models import (
    BacktestArtifact,
    BacktestPlan,
    PlannedOrder,
    RunEnvironment,
)
from tradeguard.data.fixtures import build_fixture
from tradeguard.data.models import (
    MARKET_RECORD_ADAPTER,
    CorporateAction,
    CorporateActionType,
    OHLCVBar,
)
from tradeguard.data.package import DatasetPackage
from tradeguard.data.quality import ValidationEvidenceRejectedError
from tradeguard.domain.events import AssetClass, OrderType, Side
from tradeguard.domain.serialization import canonicalize, deterministic_checksum
from tradeguard.experiments.manifest import RunType

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_ROOT = REPOSITORY_ROOT / "artifacts" / "evidence" / "prompt6"
FIXED_TIME = datetime(2024, 1, 2, 1, 0, tzinfo=UTC)
_HOSTNAME_ATTRIBUTE = re.compile(r' hostname="[^"]*"')


def _environment() -> RunEnvironment:
    return RunEnvironment(
        git_sha="0" * 40,
        dirty_worktree=True,
        python_version="3.12.0-synthetic-evidence",
        platform="redacted-synthetic-runner",
        dependency_lock_hash=hashlib.sha256((REPOSITORY_ROOT / "uv.lock").read_bytes()).hexdigest(),
        started_at=FIXED_TIME,
    )


def _crypto_order(
    *,
    order_id: str,
    quantity: str,
    submitted_at: datetime,
) -> PlannedOrder:
    return PlannedOrder(
        order_id=order_id,
        asset_class=AssetClass.CRYPTO,
        venue="SYNTH-CRYPTO",
        symbol="BTC-USD",
        side=Side.BUY,
        order_type=OrderType.MARKET,
        quantity=Decimal(quantity),
        decision_event_time_utc=submitted_at,
        submitted_at_utc=submitted_at,
        sequence_number=1,
    )


def _plan(
    *,
    run_id: str,
    orders: tuple[PlannedOrder, ...],
    initial_cash: str = "100000",
) -> BacktestPlan:
    return BacktestPlan(
        run_id=UUID(run_id),
        run_type=RunType.BACKTEST,
        initial_cash=Decimal(initial_cash),
        base_currency="USD",
        orders=orders,
    )


def _equity_plan() -> BacktestPlan:
    submitted = datetime(2024, 1, 1, 20, 57, tzinfo=UTC)
    order = PlannedOrder(
        order_id="synthetic-equity-split-buy",
        asset_class=AssetClass.EQUITY,
        venue="SYNTH-XNYS",
        symbol="ACME",
        side=Side.BUY,
        order_type=OrderType.MARKET,
        quantity=Decimal("10"),
        decision_event_time_utc=submitted,
        submitted_at_utc=submitted,
        sequence_number=1,
    )
    return _plan(
        run_id="00000000-0000-4000-8000-000000000063",
        orders=(order,),
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


def _sanitize_xml(path: Path) -> None:
    content = path.read_text(encoding="utf-8")
    content = content.replace(str(REPOSITORY_ROOT), ".")
    content = content.replace(REPOSITORY_ROOT.as_posix(), ".")
    content = _HOSTNAME_ATTRIBUTE.sub(' hostname="redacted"', content)
    path.write_text(content, encoding="utf-8", newline="\n")


def _collect_manifest_binding_evidence(artifact: BacktestArtifact) -> None:
    checksum_payload = artifact.model_dump()
    checksum_payload["manifest"]["git_sha"] = "f" * 40
    checksum_tamper_accepted = True
    try:
        BacktestArtifact.model_validate(checksum_payload)
    except ValidationError:
        checksum_tamper_accepted = False

    semantic_payload = artifact.model_dump()
    semantic_payload["manifest"]["config_hash"] = "e" * 64
    semantic_payload["manifest_checksum"] = deterministic_checksum(semantic_payload["manifest"])
    recomputed_tamper_accepted = True
    try:
        BacktestArtifact.model_validate(semantic_payload)
    except ValidationError:
        recomputed_tamper_accepted = False

    recomputed_provenance_tamper_accepted: dict[str, bool] = {}
    for identity_field in ("git_sha", "universe", "dataset_id"):
        provenance_payload = artifact.model_dump()
        if identity_field == "git_sha":
            provenance_payload["manifest"]["git_sha"] = "f" * 40
        elif identity_field == "universe":
            provenance_payload["manifest"]["universe"] = ["UNRELATED"]
        else:
            provenance_payload["manifest"]["dataset_manifests"][0]["dataset_id"] = (
                "unrelated-dataset"
            )
        provenance_payload["manifest_checksum"] = deterministic_checksum(
            provenance_payload["manifest"]
        )
        accepted = True
        try:
            BacktestArtifact.model_validate(provenance_payload)
        except ValidationError:
            accepted = False
        recomputed_provenance_tamper_accepted[identity_field] = accepted

    if (
        checksum_tamper_accepted
        or recomputed_tamper_accepted
        or any(recomputed_provenance_tamper_accepted.values())
    ):
        raise RuntimeError("tampered backtest artifact passed manifest binding")
    _write(
        "manifest-tamper-rejection.json",
        {
            "schema_version": "1.0.0",
            "synthetic_only": True,
            "manifest_checksum": artifact.manifest_checksum,
            "checksum_tamper_accepted": checksum_tamper_accepted,
            "recomputed_checksum_tamper_accepted": recomputed_tamper_accepted,
            "recomputed_git_sha_tamper_accepted": (
                recomputed_provenance_tamper_accepted["git_sha"]
            ),
            "recomputed_universe_tamper_accepted": (
                recomputed_provenance_tamper_accepted["universe"]
            ),
            "recomputed_dataset_id_tamper_accepted": (
                recomputed_provenance_tamper_accepted["dataset_id"]
            ),
        },
    )


def _collect_aggregate_participation_evidence(
    engine: DeterministicBacktester,
) -> None:
    package = build_fixture("normal")
    submitted = datetime(2024, 1, 2, 0, 4, tzinfo=UTC)
    aggregate_plan = _plan(
        run_id="00000000-0000-4000-8000-000000000064",
        orders=(
            _crypto_order(order_id="aggregate-a", quantity="0.2500", submitted_at=submitted),
            _crypto_order(order_id="aggregate-b", quantity="0.2500", submitted_at=submitted),
        ),
    )
    artifact = engine.run(package=package, plan=aggregate_plan, environment=_environment())
    final_record = MARKET_RECORD_ADAPTER.validate_python(package.records[-1])
    if not isinstance(final_record, OHLCVBar):
        raise TypeError("aggregate participation evidence requires a final OHLCV bar")
    configured_cap = final_record.volume * aggregate_plan.execution.max_participation_rate
    aggregate_fill = sum(
        (fill.quantity for fill in artifact.result.fills),
        start=Decimal("0"),
    )
    within_cap = aggregate_fill <= configured_cap
    if not within_cap:
        raise RuntimeError("aggregate fills exceed the configured bar participation cap")
    _write(
        "aggregate-participation-cap.json",
        {
            "schema_version": "1.0.0",
            "synthetic_only": True,
            "aggregate_fill_quantity": aggregate_fill,
            "configured_bar_cap": configured_cap,
            "within_cap": within_cap,
            "orders": artifact.result.orders,
        },
    )


def _collect_post_bar_action_evidence(engine: DeterministicBacktester) -> None:
    package = build_fixture("stock_split")
    dividend = CorporateAction(
        source="synthetic",
        venue="SYNTH-XNYS",
        symbol="ACME",
        action_type=CorporateActionType.CASH_DIVIDEND,
        effective_at=datetime(2024, 1, 2, 14, 31, 30, tzinfo=UTC),
        known_at=datetime(2024, 1, 2, 14, 31, 30, tzinfo=UTC),
        action_version="synthetic-v1",
        cash_amount=Decimal("1"),
        currency="USD",
    )
    extended_range = package.manifest.date_range.model_copy(
        update={"end_utc": datetime(2024, 1, 2, 14, 32, tzinfo=UTC)}
    )
    package = package.model_copy(
        update={
            "manifest": package.manifest.model_copy(update={"date_range": extended_range}),
            "corporate_actions": (*package.corporate_actions, dividend),
        }
    )
    artifact = engine.run(package=package, plan=_equity_plan(), environment=_environment())
    ending_cash = artifact.result.ending_currency_balances["USD"]
    final_pnl_cash = artifact.result.pnl_series[-1].cash
    finalized = ending_cash == final_pnl_cash and artifact.result.conservation.conserved
    if not finalized:
        raise RuntimeError("post-bar corporate action did not finalize PnL and conservation")
    _write(
        "post-bar-corporate-action.json",
        {
            "schema_version": "1.0.0",
            "synthetic_only": True,
            "cash_delta": artifact.result.corporate_actions[-1].cash_delta,
            "ending_cash": ending_cash,
            "final_pnl_cash": final_pnl_cash,
            "conserved": artifact.result.conservation.conserved,
            "finalized": finalized,
        },
    )


def _collect_completion_time_evidence(
    normal: DatasetPackage,
    normal_plan: BacktestPlan,
) -> None:
    completed_at = FIXED_TIME + timedelta(seconds=1)
    environment = _environment().model_copy(update={"completed_at": None})
    artifact = DeterministicBacktester(completion_clock=lambda: completed_at).run(
        package=normal,
        plan=normal_plan,
        environment=environment,
    )
    if artifact.manifest.completed_at is None:
        raise RuntimeError("completion timestamp is missing")
    captured_after_start = artifact.manifest.completed_at > artifact.manifest.started_at
    if not captured_after_start:
        raise RuntimeError("completion timestamp was not captured after the run start")
    prefilled_completion_rejected = False
    prefilled_environment = environment.model_copy(update={"completed_at": FIXED_TIME})
    try:
        DeterministicBacktester(completion_clock=lambda: completed_at).run(
            package=normal,
            plan=normal_plan,
            environment=prefilled_environment,
        )
    except BacktestRejectedError:
        prefilled_completion_rejected = True
    if not prefilled_completion_rejected:
        raise RuntimeError("prefilled completion timestamp was accepted")
    _write(
        "truthful-completion-time.json",
        {
            "schema_version": "1.0.0",
            "synthetic_only": True,
            "started_at": artifact.manifest.started_at,
            "completed_at": artifact.manifest.completed_at,
            "captured_after_start": captured_after_start,
            "prefilled_completion_rejected": prefilled_completion_rejected,
        },
    )


def main() -> int:
    for xml_path in EVIDENCE_ROOT.glob("*.xml"):
        _sanitize_xml(xml_path)
    engine = DeterministicBacktester(completion_clock=lambda: FIXED_TIME + timedelta(seconds=1))
    normal = build_fixture("normal")
    submitted = datetime(2024, 1, 2, 0, 4, tzinfo=UTC)
    normal_plan = _plan(
        run_id="00000000-0000-4000-8000-000000000060",
        orders=(
            _crypto_order(
                order_id="synthetic-crypto-buy",
                quantity="0.1000",
                submitted_at=submitted,
            ),
        ),
    )
    first = engine.run(package=normal, plan=normal_plan, environment=_environment())
    second = engine.run(package=normal, plan=normal_plan, environment=_environment())
    _write(
        "deterministic-checksum.json",
        {
            "schema_version": "1.0.0",
            "synthetic_only": True,
            "first_result_checksum": first.result.result_checksum,
            "second_result_checksum": second.result.result_checksum,
            "identical": first.result.result_checksum == second.result.result_checksum,
            "dataset_manifest_checksum": normal.manifest.checksum(),
            "plan_checksum": normal_plan.checksum(),
        },
    )
    _write("conservation-report.json", first.result.conservation)
    _collect_manifest_binding_evidence(first)
    _collect_aggregate_participation_evidence(engine)
    _collect_post_bar_action_evidence(engine)
    _collect_completion_time_evidence(normal, normal_plan)
    lookahead_plan = _plan(
        run_id="00000000-0000-4000-8000-000000000061",
        orders=(
            _crypto_order(
                order_id="same-close-attempt",
                quantity="0.1000",
                submitted_at=datetime(2024, 1, 2, 0, 5, tzinfo=UTC),
            ),
        ),
    )
    lookahead = engine.run(package=normal, plan=lookahead_plan, environment=_environment())
    _write(
        "lookahead-rejection.json",
        {
            "fills": len(lookahead.result.fills),
            "order": lookahead.result.orders[0],
            "warnings": lookahead.result.warnings,
        },
    )
    partial_plan = _plan(
        run_id="00000000-0000-4000-8000-000000000062",
        orders=(
            _crypto_order(
                order_id="partial-fill-attempt",
                quantity="0.5000",
                submitted_at=submitted,
            ),
        ),
    )
    partial = engine.run(package=normal, plan=partial_plan, environment=_environment())
    _write(
        "partial-fill.json",
        {
            "order": partial.result.orders[0],
            "fills": partial.result.fills,
            "ending_asset_balances": partial.result.ending_asset_balances,
        },
    )
    split = engine.run(
        package=build_fixture("stock_split"),
        plan=_equity_plan(),
        environment=_environment(),
    )
    _write(
        "stock-split.json",
        {
            "corporate_actions": split.result.corporate_actions,
            "ending_asset_balances": split.result.ending_asset_balances,
            "conservation": split.result.conservation,
        },
    )
    maintenance = build_fixture("crypto_maintenance")
    rejected = False
    reason = ""
    try:
        engine.run(package=maintenance, plan=normal_plan, environment=_environment())
    except ValidationEvidenceRejectedError as exc:
        rejected = True
        reason = str(exc)
    _write(
        "crypto-maintenance-rejection.json",
        {
            "dataset_quality_status": maintenance.validate_quality().status,
            "admitted_to_backtest": not rejected,
            "rejection_reason": reason,
            "synthetic_only": True,
        },
    )
    entries = [
        {"path": path.name, "sha256": _sha256(path)}
        for path in sorted(
            candidate for candidate in EVIDENCE_ROOT.iterdir() if candidate.is_file()
        )
        if path.name not in {"coverage.xml", "index.json"}
    ]
    _write(
        "index.json",
        {
            "schema_version": "1.0.0",
            "evidence_stage": "prompt6",
            "synthetic_only": True,
            "artifacts": entries,
        },
    )
    print(EVIDENCE_ROOT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
