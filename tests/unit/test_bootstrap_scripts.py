"""Unit tests for bootstrap security and evidence tooling."""

import json
from pathlib import Path

import pytest
from scripts.collect_evidence import build_index, sha256_file, write_json
from scripts.collect_prompt3_evidence import evidence_documents
from scripts.collect_prompt4_evidence import FIXTURE_PATH, collect_evidence
from scripts.collect_prompt5_evidence import sanitize_xml
from scripts.scan_secrets import candidate_files, scan_file
from scripts.validate_workflows import validate_workflow

from tradeguard.domain.serialization import canonical_json


@pytest.mark.unit
def test_evidence_index_uses_stable_sha256(tmp_path: Path) -> None:
    artifact = tmp_path / "report.json"
    write_json(artifact, {"status": "PASS"})

    index = build_index(tmp_path)

    assert index == [{"path": "report.json", "sha256": sha256_file(artifact)}]
    assert len(index[0]["sha256"]) == 64
    assert json.loads(artifact.read_text(encoding="utf-8")) == {"status": "PASS"}


@pytest.mark.unit
def test_secret_scan_redacts_values_from_findings(tmp_path: Path) -> None:
    secret_file = tmp_path / "unsafe.txt"
    secret_file.write_text(
        "access_" + "token=" + "abcdefghijklmnopqrstuvwxyz123456\n",
        encoding="utf-8",
    )

    findings = scan_file(secret_file)

    assert findings == [(1, "generic-assignment")]
    assert "abcdefghijklmnopqrstuvwxyz" not in repr(findings)


@pytest.mark.unit
def test_secret_scan_allows_explicit_placeholder(tmp_path: Path) -> None:
    example = tmp_path / ".env.example"
    example.write_text(
        "access_token=replace-with-data-only-placeholder\n",
        encoding="utf-8",
    )

    assert scan_file(example) == []


@pytest.mark.unit
def test_secret_scan_excludes_pytest_temporary_tree(tmp_path: Path) -> None:
    temporary_tree = tmp_path / ".pytest-tmp"
    temporary_tree.mkdir()
    (temporary_tree / "generated-secret-fixture.txt").write_text(
        "access_" + "token=" + "abcdefghijklmnopqrstuvwxyz123456\n",
        encoding="utf-8",
    )

    assert candidate_files(tmp_path) == []


@pytest.mark.unit
def test_workflow_policy_rejects_mutable_action_and_privileged_trigger(tmp_path: Path) -> None:
    workflow = tmp_path / "unsafe.yml"
    workflow.write_text(
        """
name: unsafe
on:
  pull_request_target:
permissions:
  contents: write
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v7
""".strip(),
        encoding="utf-8",
    )

    errors = validate_workflow(workflow)

    assert "pull_request_target is prohibited" in errors
    assert "top-level permissions must be exactly contents: read" in errors
    assert "action is not pinned to a full SHA: actions/checkout" in errors


@pytest.mark.unit
def test_prompt3_evidence_is_complete_synthetic_and_redacted() -> None:
    documents = evidence_documents()

    assert set(documents) == {
        "fixture-manifests.json",
        "quality-reports.json",
        "quarantined-dataset.json",
        "transformed-dataset-checksum.json",
        "lineage-graph.json",
    }
    serialized = canonical_json(documents)
    assert "synthetic-bad_tick" in serialized
    assert '"validation_evidence_eligible":false' in serialized
    assert "security@your-domain.example" not in serialized
    assert "access_token" not in serialized


@pytest.mark.unit
def test_prompt4_public_evidence_excludes_credentials_and_raw_ohlcv(tmp_path: Path) -> None:
    evidence_root = tmp_path / "prompt4"
    collect_evidence(evidence_root)
    serialized = "\n".join(
        path.read_text(encoding="utf-8") for path in sorted(evidence_root.glob("*.json"))
    )
    fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    assert "fixture-credential" not in serialized
    assert '"raw_market_values_persisted": false' in serialized
    assert '"raw_market_values_published": false' in serialized
    for row in fixture["response"]["values"]:
        for field in ("open", "high", "low", "close", "volume"):
            assert row[field] not in serialized


@pytest.mark.unit
def test_prompt5_xml_evidence_redacts_workstation_identity(tmp_path: Path) -> None:
    evidence = tmp_path / "coverage.xml"
    repository_path = Path(__file__).resolve().parents[2]
    evidence.write_text(
        f'<source>{repository_path}</source><testsuite hostname="private-host" />',
        encoding="utf-8",
    )

    sanitize_xml(evidence)

    sanitized = evidence.read_text(encoding="utf-8")
    assert str(repository_path) not in sanitized
    assert 'hostname="private-host"' not in sanitized
    assert "<source>.</source>" in sanitized
    assert 'hostname="redacted"' in sanitized
