"""Run the manually opted-in Twelve Data smoke and write redacted evidence."""

from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from pathlib import Path

from tradeguard.adapters.equity.calendar import (
    DeterministicMicCalendarRegistry,
    MarketCalendarUnavailableError,
    ReviewedCalendarDocument,
)
from tradeguard.adapters.equity.connected import (
    CREDENTIAL_VARIABLE,
    RUN_CONNECTED_VARIABLE,
    ConnectedSmokeResult,
    ConnectedSmokeStatus,
    run_connected_smoke,
)
from tradeguard.domain.serialization import canonicalize

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
CALENDAR_PATH = REPOSITORY_ROOT / "configs" / "markets" / "equities_connected_sessions.json"
OUTPUT_PATH = REPOSITORY_ROOT / "artifacts" / "evidence" / "prompt4" / "connected-smoke-result.json"


def _calendar_or_blocked() -> DeterministicMicCalendarRegistry:
    document = ReviewedCalendarDocument.model_validate_json(
        CALENDAR_PATH.read_text(encoding="utf-8")
    )
    return document.to_registry()


def _write(result: ConnectedSmokeResult) -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        json.dumps(canonicalize(result), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def main() -> int:
    observed_at = datetime.now(UTC)
    if OUTPUT_PATH.exists():
        existing = ConnectedSmokeResult.model_validate_json(OUTPUT_PATH.read_text(encoding="utf-8"))
        if os.environ.get(RUN_CONNECTED_VARIABLE) != "1":
            print(existing.status.value)
            return 0
        if existing.status is not ConnectedSmokeStatus.SKIP_NOT_OPTED_IN:
            print("BLOCKED_ALREADY_RUN_FOR_THIS_EVIDENCE_DIRECTORY")
            return 2
    opted_in = os.environ.get(RUN_CONNECTED_VARIABLE) == "1"
    credential_present = bool(os.environ.get(CREDENTIAL_VARIABLE, "").strip())
    if opted_in and credential_present:
        try:
            registry = _calendar_or_blocked()
        except MarketCalendarUnavailableError:
            result = ConnectedSmokeResult(
                status=ConnectedSmokeStatus.BLOCKED_MARKET_CALENDAR,
                reason_code=ConnectedSmokeStatus.BLOCKED_MARKET_CALENDAR.value,
                passed=False,
                provider_contacted=False,
                observed_at=observed_at,
                request_attempts=0,
                record_count=0,
            )
            _write(result)
            print(result.status.value)
            return 2
    else:
        registry = DeterministicMicCalendarRegistry()
    result = run_connected_smoke(
        environment=os.environ,
        calendar_registry=registry,
        clock=lambda: observed_at,
    )
    _write(result)
    print(result.status.value)
    return (
        0
        if result.status
        in {
            ConnectedSmokeStatus.SKIP_NOT_OPTED_IN,
            ConnectedSmokeStatus.PASS,
        }
        else 2
    )


if __name__ == "__main__":
    raise SystemExit(main())
