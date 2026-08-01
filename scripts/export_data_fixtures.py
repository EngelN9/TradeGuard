"""Export deterministic synthetic Prompt 3 dataset packages."""

from __future__ import annotations

import json
from pathlib import Path

from tradeguard.data.fixtures import all_fixtures
from tradeguard.domain.serialization import canonicalize

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = REPOSITORY_ROOT / "tests" / "fixtures" / "market_data"


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(canonicalize(value), indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def main() -> int:
    for scenario, package in all_fixtures().items():
        write_json(FIXTURE_ROOT / f"{scenario}.json", package)
    print(FIXTURE_ROOT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
