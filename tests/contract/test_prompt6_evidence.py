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

    assert deterministic["synthetic_only"] is True
    assert deterministic["identical"] is True
    assert deterministic["first_result_checksum"] == deterministic["second_result_checksum"]
    assert maintenance["admitted_to_backtest"] is False
    assert maintenance["dataset_quality_status"] == "FAIL"
    assert lookahead["fills"] == 0
    assert lookahead["order"]["status"] == "unfilled"


@pytest.mark.contract
def test_prompt6_json_evidence_matches_index_and_has_no_local_paths() -> None:
    index = json.loads((EVIDENCE_ROOT / "index.json").read_text(encoding="utf-8"))
    entries = {entry["path"]: entry["sha256"] for entry in index["artifacts"]}

    for path in EVIDENCE_ROOT.glob("*.json"):
        content = path.read_text(encoding="utf-8")
        assert "C:\\Users\\" not in content
        if path.name != "index.json":
            assert entries[path.name] == hashlib.sha256(path.read_bytes()).hexdigest()
