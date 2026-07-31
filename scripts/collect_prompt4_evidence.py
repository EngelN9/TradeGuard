"""Collect public-safe Prompt 4 evidence without contacting Twelve Data."""

from __future__ import annotations

import hashlib
import json
import xml.etree.ElementTree as ET
from datetime import UTC, date, datetime
from pathlib import Path

from pydantic import SecretStr, ValidationError

from tradeguard.adapters.equity.calendar import fixture_calendar_registry
from tradeguard.adapters.equity.configuration import (
    TwelveDataReleaseConfiguration,
    load_release_configuration,
)
from tradeguard.adapters.equity.connected import ConnectedSmokeResult, run_connected_smoke
from tradeguard.adapters.equity.protocol import EquityDataset, HistoricalBarsRequest
from tradeguard.adapters.equity.transport import HttpRequest, HttpResponse, HttpTransport
from tradeguard.adapters.equity.twelve_data import TwelveDataEquityAdapter
from tradeguard.domain.serialization import canonicalize

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = (
    REPOSITORY_ROOT
    / "tests"
    / "fixtures"
    / "adapters"
    / "twelve_data"
    / "time_series_aapl_1day_sanitized.json"
)
EVIDENCE_ROOT = REPOSITORY_ROOT / "artifacts" / "evidence" / "prompt4"
CONTRACT_XML = EVIDENCE_ROOT / "offline-contract-tests.xml"
RELEASE_CONFIGURATION_PATH = REPOSITORY_ROOT / "configs" / "adapters" / "twelve_data_equity.json"
FIXED_INGESTED_AT = datetime(2024, 1, 11, 12, 0, tzinfo=UTC)


class RecordedTransport(HttpTransport):
    """One-response offline transport used only by this evidence collector."""

    def __init__(self, response: HttpResponse) -> None:
        self._response = response
        self.requests: list[HttpRequest] = []

    def send(self, request: HttpRequest) -> HttpResponse:
        self.requests.append(request)
        return self._response


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(canonicalize(value), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _offline_dataset(
    release_configuration: TwelveDataReleaseConfiguration,
) -> tuple[TwelveDataEquityAdapter, EquityDataset]:
    fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    response_body = json.dumps(fixture["response"], sort_keys=True).encode()
    transport = RecordedTransport(
        HttpResponse(
            status_code=200,
            headers={"x-request-id": "sanitized-fixture-request"},
            body=response_body,
        )
    )
    adapter = TwelveDataEquityAdapter(
        api_key=SecretStr("fixture-credential"),
        calendar_registry=fixture_calendar_registry(),
        release_configuration=release_configuration,
        transport=transport,
        clock=lambda: FIXED_INGESTED_AT,
        sleeper=lambda _: None,
    )
    dataset = adapter.historical_bars(
        HistoricalBarsRequest(
            symbol="AAPL",
            mic="XNAS",
            start_date=date(2024, 1, 2),
            end_date=date(2024, 1, 10),
        )
    )
    return adapter, dataset


def _contract_result(contract_xml: Path) -> dict[str, object]:
    if not contract_xml.exists():
        return {
            "command": (
                "uv run pytest -m contract tests/contract/test_twelve_data_adapter.py "
                "--junitxml=artifacts/evidence/prompt4/offline-contract-tests.xml"
            ),
            "passed": False,
            "status": "BLOCKED_MISSING_TEST_RESULT",
        }
    root = ET.parse(contract_xml).getroot()  # noqa: S314 - locally generated JUnit only
    suites = (root,) if root.tag == "testsuite" else tuple(root.iter("testsuite"))
    failures = sum(int(suite.attrib.get("failures", "0")) for suite in suites)
    errors = sum(int(suite.attrib.get("errors", "0")) for suite in suites)
    tests = sum(int(suite.attrib.get("tests", "0")) for suite in suites)
    skipped = sum(int(suite.attrib.get("skipped", "0")) for suite in suites)
    passed = tests > 0 and failures == 0 and errors == 0
    return {
        "errors": errors,
        "failures": failures,
        "passed": passed,
        "skipped": skipped,
        "status": "PASS" if passed else "FAIL",
        "tests": tests,
    }


def _build_index(evidence_root: Path) -> dict[str, object]:
    entries = []
    for path in sorted(evidence_root.rglob("*")):
        if not path.is_file() or path.name == "index.json":
            continue
        entries.append(
            {
                "path": path.relative_to(evidence_root).as_posix(),
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            }
        )
    return {
        "schema_version": "1.0.0",
        "provider": "twelve_data",
        "raw_market_values_published": False,
        "entries": entries,
    }


def collect_evidence(evidence_root: Path) -> None:
    """Write public-safe evidence without retaining provider market values."""

    release_configuration = load_release_configuration(RELEASE_CONFIGURATION_PATH)
    adapter, dataset = _offline_dataset(release_configuration)
    _write_json(evidence_root / "adapter-capability-report.json", adapter.capabilities)
    _write_json(evidence_root / "reviewed-release-configuration.json", release_configuration)
    _write_json(
        evidence_root / "recorded-response-checksum.json",
        {
            "fixture_path": FIXTURE_PATH.relative_to(REPOSITORY_ROOT).as_posix(),
            "fixture_sha256": hashlib.sha256(FIXTURE_PATH.read_bytes()).hexdigest(),
            "raw_market_values_published": False,
            "raw_market_values_persisted": False,
            "values_are_deterministic_synthetic": True,
        },
    )
    _write_json(evidence_root / "sample-dataset-manifest.json", dataset.manifest)
    _write_json(evidence_root / "sample-quality-report.json", dataset.quality_report)
    _write_json(
        evidence_root / "offline-contract-result.json",
        _contract_result(evidence_root / CONTRACT_XML.name),
    )
    connected_path = evidence_root / "connected-smoke-result.json"
    connected_result_is_current = False
    if connected_path.exists():
        try:
            ConnectedSmokeResult.model_validate_json(connected_path.read_text(encoding="utf-8"))
            connected_result_is_current = True
        except ValidationError:
            connected_result_is_current = False
    if not connected_result_is_current:
        _write_json(
            connected_path,
            run_connected_smoke(
                environment={},
                calendar_registry=fixture_calendar_registry(),
                release_configuration=release_configuration,
                clock=lambda: datetime(2026, 7, 31, tzinfo=UTC),
            ),
        )
    _write_json(
        evidence_root / "licensing-and-usage.json",
        {
            "account_owner_type": release_configuration.account.account_type,
            "exact_plan_name": release_configuration.account.plan_name,
            "intended_use": release_configuration.usage.intended_use,
            "intended_use_approved": release_configuration.usage.approved,
            "license_classification": release_configuration.licensing.classification,
            "license_reviewed_at": "2026-07-31",
            "public_display_allowed": release_configuration.public_display.allowed,
            "redistribution_allowed": (release_configuration.licensing.redistribution_allowed),
            "raw_connected_response": (release_configuration.retention.raw_connected_response),
            "raw_response_publication": (release_configuration.retention.raw_response_publication),
            "terms_reviewed_version": "2026-01-01",
        },
    )
    _write_json(
        evidence_root / "promotion-gate.json",
        {
            "status": "BLOCKED",
            "connected_pass_required": True,
            "provider_contacted_by_collector": False,
            "raw_market_values_published": False,
            "reason": "APPROVED connected-session configuration is missing",
        },
    )
    _write_json(evidence_root / "index.json", _build_index(evidence_root))


def main() -> int:
    collect_evidence(EVIDENCE_ROOT)
    print(EVIDENCE_ROOT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
