"""Contract checks for committed synthetic R4 strategy evidence."""

import hashlib
import json
from pathlib import Path

import pytest

from tradeguard.strategies.models import StrategyRunArtifact

EVIDENCE_ROOT = Path(__file__).resolve().parents[2] / "artifacts" / "evidence" / "r4"


@pytest.mark.contract
def test_r4_evidence_is_synthetic_deterministic_and_non_promotional() -> None:
    artifact = StrategyRunArtifact.model_validate_json(
        (EVIDENCE_ROOT / "synthetic-run.json").read_text(encoding="utf-8")
    )
    deterministic = json.loads((EVIDENCE_ROOT / "determinism.json").read_text(encoding="utf-8"))
    unsupported = json.loads(
        (EVIDENCE_ROOT / "unsupported-market-rejection.json").read_text(encoding="utf-8")
    )
    undeclared = json.loads(
        (EVIDENCE_ROOT / "undeclared-data-rejection.json").read_text(encoding="utf-8")
    )
    tamper = json.loads((EVIDENCE_ROOT / "tamper-rejection.json").read_text(encoding="utf-8"))

    assert artifact.synthetic_only is True
    assert artifact.report.promotion_status == "NOT_EVALUATED"
    assert artifact.report.investment_advice is False
    assert artifact.report.profitability_claim is False
    assert artifact.outputs[-1].event_time_utc < artifact.backtest.result.fills[0].event_time_utc
    assert deterministic["identical"] is True
    assert deterministic["first_artifact_checksum"] == deterministic["second_artifact_checksum"]
    assert unsupported == {
        "accepted": False,
        "candidate_market": "SYNTH-XNYS:ACME",
        "rejection_code": "unsupported_market",
        "schema_version": "1.0.0",
        "synthetic_only": True,
    }
    assert undeclared["accepted"] is False
    assert undeclared["rejection_code"] == "undeclared_data"
    assert tamper["direct_checksum_tamper_accepted"] is False
    assert tamper["recomputed_checksum_semantic_tamper_accepted"] is False


@pytest.mark.contract
def test_r4_evidence_index_matches_files_and_contains_no_local_paths() -> None:
    index = json.loads((EVIDENCE_ROOT / "index.json").read_text(encoding="utf-8"))
    entries = {entry["path"]: entry["sha256"] for entry in index["artifacts"]}
    expected = {
        "strategy-contract.json",
        "synthetic-run.json",
        "determinism.json",
        "unsupported-market-rejection.json",
        "undeclared-data-rejection.json",
        "tamper-rejection.json",
    }

    assert index["synthetic_only"] is True
    assert index["promotion_status"] == "NOT_EVALUATED"
    assert set(entries) == expected
    for path in EVIDENCE_ROOT.glob("*.json"):
        content = path.read_text(encoding="utf-8")
        assert "C:\\Users\\" not in content
        assert "/home/" not in content
        if path.name != "index.json":
            assert entries[path.name] == hashlib.sha256(path.read_bytes()).hexdigest()
