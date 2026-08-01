"""Generate deterministic, synthetic-only Prompt 6 review evidence."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from uuid import UUID

from tradeguard.backtest.engine import DeterministicBacktester
from tradeguard.backtest.models import BacktestPlan, PlannedOrder, RunEnvironment
from tradeguard.data.fixtures import build_fixture
from tradeguard.data.quality import ValidationEvidenceRejectedError
from tradeguard.domain.events import AssetClass, OrderType, Side
from tradeguard.domain.serialization import canonicalize
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
        completed_at=FIXED_TIME,
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


def main() -> int:
    for xml_path in EVIDENCE_ROOT.glob("*.xml"):
        _sanitize_xml(xml_path)
    engine = DeterministicBacktester()
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
