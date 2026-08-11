"""Contract checks for committed synthetic Prompt 6 evidence."""

import hashlib
import json
from pathlib import Path

import pytest

EVIDENCE_ROOT = Path(__file__).resolve().parents[2] / "artifacts" / "evidence" / "prompt6"


@pytest.mark.contract
def test_prompt6_evidence_is_synthetic_deterministic_and_fail_closed() -> None:
    deterministic = json.loads(
        (EVIDENCE_ROOT / "deterministic-checksum.json").read_text(encoding="utf-8")
    )
    maintenance = json.loads(
        (EVIDENCE_ROOT / "crypto-maintenance-rejection.json").read_text(encoding="utf-8")
    )
    lookahead = json.loads((EVIDENCE_ROOT / "lookahead-rejection.json").read_text(encoding="utf-8"))
    manifest = json.loads(
        (EVIDENCE_ROOT / "manifest-tamper-rejection.json").read_text(encoding="utf-8")
    )
    participation = json.loads(
        (EVIDENCE_ROOT / "aggregate-participation-cap.json").read_text(encoding="utf-8")
    )
    action = json.loads(
        (EVIDENCE_ROOT / "post-bar-corporate-action.json").read_text(encoding="utf-8")
    )
    completion = json.loads(
        (EVIDENCE_ROOT / "truthful-completion-time.json").read_text(encoding="utf-8")
    )

    assert deterministic["synthetic_only"] is True
    assert deterministic["identical"] is True
    assert deterministic["first_result_checksum"] == deterministic["second_result_checksum"]
    assert maintenance["admitted_to_backtest"] is False
    assert maintenance["dataset_quality_status"] == "FAIL"
    assert lookahead["fills"] == 0
    assert lookahead["order"]["status"] == "unfilled"
    assert manifest["checksum_tamper_accepted"] is False
    assert manifest["recomputed_checksum_tamper_accepted"] is False
    assert manifest["recomputed_git_sha_tamper_accepted"] is False
    assert manifest["recomputed_universe_tamper_accepted"] is False
    assert manifest["recomputed_dataset_id_tamper_accepted"] is False
    assert participation["within_cap"] is True
    assert participation["aggregate_fill_quantity"] == participation["configured_bar_cap"]
    assert action["finalized"] is True
    assert action["ending_cash"] == action["final_pnl_cash"]
    assert completion["captured_after_start"] is True
    assert completion["prefilled_completion_rejected"] is True


@pytest.mark.contract
def test_prompt6_json_evidence_matches_index_and_has_no_local_paths() -> None:
    index = json.loads((EVIDENCE_ROOT / "index.json").read_text(encoding="utf-8"))
    entries = {entry["path"]: entry["sha256"] for entry in index["artifacts"]}

    for path in EVIDENCE_ROOT.glob("*.json"):
        content = path.read_text(encoding="utf-8")
        assert "C:\\Users\\" not in content
        if path.name != "index.json":
            assert entries[path.name] == hashlib.sha256(path.read_bytes()).hexdigest()
