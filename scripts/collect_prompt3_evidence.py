"""Generate redacted, deterministic Prompt 3 acceptance evidence."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from tradeguard.data.fixtures import all_fixtures
from tradeguard.domain.serialization import canonicalize, deterministic_checksum

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_ROOT = REPOSITORY_ROOT / "artifacts" / "evidence" / "prompt3"


def _file_checksum(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(canonicalize(value), indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def evidence_documents() -> dict[str, object]:
    fixtures = all_fixtures()
    reports = {name: package.validate_quality() for name, package in fixtures.items()}
    manifests = {
        name: {
            "manifest": package.manifest,
            "manifest_checksum": package.manifest.checksum(),
        }
        for name, package in fixtures.items()
    }
    lineage = {
        name: {
            "dataset_id": package.manifest.dataset_id,
            "graph": package.manifest.transformation_graph,
            "lineage_checksum": package.manifest.transformation_graph.checksum(),
        }
        for name, package in fixtures.items()
    }
    normal = fixtures["normal"]
    quarantined = fixtures["bad_tick"]
    return {
        "fixture-manifests.json": manifests,
        "quality-reports.json": reports,
        "quarantined-dataset.json": {
            "package": quarantined,
            "quality_report": reports["bad_tick"],
            "validation_evidence_eligible": False,
        },
        "transformed-dataset-checksum.json": {
            "dataset_id": normal.manifest.dataset_id,
            "records_checksum": deterministic_checksum(normal.records),
            "manifest_checksum": normal.manifest.checksum(),
            "lineage_checksum": normal.manifest.transformation_graph.checksum(),
        },
        "lineage-graph.json": lineage,
    }


def main() -> int:
    documents = evidence_documents()
    for name, document in documents.items():
        _write_json(EVIDENCE_ROOT / name, document)
    index = {name: _file_checksum(EVIDENCE_ROOT / name) for name in sorted(documents)}
    _write_json(EVIDENCE_ROOT / "index.json", index)
    print(EVIDENCE_ROOT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
