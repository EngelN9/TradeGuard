"""Run the manually opted-in Coinbase public smoke and write redacted evidence."""

from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from pathlib import Path

from tradeguard.adapters.crypto.configuration import load_release_configuration
from tradeguard.adapters.crypto.connected import (
    ConnectedSmokeStatus,
    CryptoConnectedSmokeResult,
    run_connected_smoke,
)
from tradeguard.domain.serialization import canonicalize

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
RELEASE_CONFIGURATION_PATH = REPOSITORY_ROOT / "configs" / "adapters" / "coinbase_crypto.json"
OUTPUT_PATH = REPOSITORY_ROOT / "artifacts" / "evidence" / "prompt5" / "connected-smoke-result.json"


def _write(result: CryptoConnectedSmokeResult) -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        json.dumps(canonicalize(result), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def main() -> int:
    result = run_connected_smoke(
        environment=os.environ,
        release_configuration=load_release_configuration(RELEASE_CONFIGURATION_PATH),
        clock=lambda: datetime.now(UTC),
    )
    _write(result)
    print(result.status.value)
    return (
        0
        if result.status in {ConnectedSmokeStatus.SKIP_NOT_OPTED_IN, ConnectedSmokeStatus.PASS}
        else 2
    )


if __name__ == "__main__":
    raise SystemExit(main())
