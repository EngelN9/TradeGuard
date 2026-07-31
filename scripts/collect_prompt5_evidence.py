"""Verify Prompt 5 synthetic fixtures and index redacted evidence."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = REPOSITORY_ROOT / "tests" / "fixtures" / "adapters" / "coinbase"
EVIDENCE_ROOT = REPOSITORY_ROOT / "artifacts" / "evidence" / "prompt5"
FIXTURE_NAMES = (
    "candles_btc_usd_sanitized.json",
    "product_btc_usd_sanitized.json",
    "server_time_sanitized.json",
    "ticker_btc_usd_sanitized.json",
    "websocket_btc_usd_sanitized.json",
)
_HOSTNAME_ATTRIBUTE = re.compile(r' hostname="[^"]*"')


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _fixture_checksums() -> dict[str, str]:
    checksums = {}
    for name in FIXTURE_NAMES:
        path = FIXTURE_ROOT / name
        document = json.loads(path.read_text(encoding="utf-8"))
        capture = document["capture"]
        if (
            capture["sanitized"] is not True
            or capture["values_are_deterministic_synthetic"] is not True
            or capture["raw_payload_retained"] is not False
            or capture["raw_payload_published"] is not False
        ):
            raise ValueError(f"unsafe Prompt 5 fixture metadata: {name}")
        relative = path.relative_to(REPOSITORY_ROOT).as_posix()
        checksums[relative] = _sha256(path)
    return checksums


def sanitize_xml(path: Path) -> None:
    """Remove workstation identity from public test and coverage evidence."""

    content = path.read_text(encoding="utf-8")
    content = content.replace(str(REPOSITORY_ROOT), ".")
    content = content.replace(REPOSITORY_ROOT.as_posix(), ".")
    content = _HOSTNAME_ATTRIBUTE.sub(' hostname="redacted"', content)
    path.write_text(content, encoding="utf-8", newline="\n")


def _index() -> list[dict[str, str]]:
    entries = []
    for path in sorted(candidate for candidate in EVIDENCE_ROOT.iterdir() if candidate.is_file()):
        if path.name == "index.json":
            continue
        entries.append({"path": path.name, "sha256": _sha256(path)})
    return entries


def main() -> int:
    for path in EVIDENCE_ROOT.glob("*.xml"):
        sanitize_xml(path)
    checksums = _fixture_checksums()
    _write_json(
        EVIDENCE_ROOT / "fixture-checksums.json",
        {
            "algorithm": "sha256",
            "schema_version": "1.0.0",
            "values_are_deterministic_synthetic": True,
            "raw_payload_retained": False,
            "raw_payload_published": False,
            "fixtures": checksums,
            "rest_fixture_sha256": checksums[
                "tests/fixtures/adapters/coinbase/ticker_btc_usd_sanitized.json"
            ],
            "websocket_fixture_sha256": checksums[
                "tests/fixtures/adapters/coinbase/websocket_btc_usd_sanitized.json"
            ],
        },
    )
    _write_json(
        EVIDENCE_ROOT / "index.json",
        {
            "schema_version": "1.0.0",
            "evidence_stage": "prompt5",
            "artifacts": _index(),
        },
    )
    print(EVIDENCE_ROOT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
