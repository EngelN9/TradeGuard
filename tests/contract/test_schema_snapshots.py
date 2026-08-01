"""Contract tests for committed machine-readable schema artifacts."""

import json
from pathlib import Path

import pytest
from scripts.export_schemas import SCHEMA_ROOT, schema_documents

from tradeguard.data.fixtures import FIXTURE_SCENARIOS, build_fixture
from tradeguard.data.package import DatasetPackage
from tradeguard.domain.serialization import canonicalize
from tradeguard.experiments.manifest import RunManifest

EXPECTED_EVENT_MODELS = {
    "Quote",
    "TradeTick",
    "Bar",
    "CorporateAction",
    "InstrumentMetadataChanged",
    "MarketSessionChanged",
    "DataQualityAlert",
    "FeatureSnapshot",
    "Signal",
    "TargetPosition",
    "TradeProposal",
    "RiskDecision",
    "PaperOrder",
    "PaperFill",
    "PositionSnapshot",
    "AccountSnapshot",
    "PnLSnapshot",
    "ExposureSnapshot",
    "ReconciliationDifference",
    "DriftAlert",
    "HealthStatusChanged",
    "ConfigurationChanged",
    "AuditEvent",
}
COMMON_EVENT_FIELDS = {
    "event_id",
    "schema_version",
    "event_type",
    "source",
    "asset_class",
    "venue",
    "symbol",
    "event_time_utc",
    "ingest_time_utc",
    "sequence_number",
    "correlation_id",
    "causation_id",
    "run_id",
    "payload_checksum",
}


@pytest.mark.contract
def test_committed_schema_snapshots_match_current_models() -> None:
    for relative_path, expected in schema_documents().items():
        path = SCHEMA_ROOT / relative_path
        assert path.exists(), f"missing schema artifact: {relative_path}"
        assert json.loads(path.read_text(encoding="utf-8")) == expected


@pytest.mark.contract
def test_event_schema_contains_every_required_model_and_common_field() -> None:
    event_schema = schema_documents()["domain-events.schema.json"]

    assert isinstance(event_schema, dict)
    definitions = event_schema["$defs"]
    assert isinstance(definitions, dict)
    assert set(definitions) >= EXPECTED_EVENT_MODELS
    for model_name in EXPECTED_EVENT_MODELS:
        model_schema = definitions[model_name]
        assert isinstance(model_schema, dict)
        assert set(model_schema["properties"]) >= COMMON_EVENT_FIELDS


@pytest.mark.contract
def test_sample_run_manifest_is_valid_and_clean() -> None:
    path = SCHEMA_ROOT / "examples" / "sample-run-manifest.json"
    sample = RunManifest.model_validate_json(path.read_text(encoding="utf-8"))

    assert sample.dirty_worktree is False
    assert sample.release_qualifiable is True


@pytest.mark.contract
def test_schema_artifacts_contain_no_absolute_local_paths() -> None:
    for path in Path(SCHEMA_ROOT).rglob("*.json"):
        content = path.read_text(encoding="utf-8")
        assert "C:\\Users\\" not in content
        assert "/home/" not in content


@pytest.mark.contract
def test_committed_prompt3_fixtures_match_generators() -> None:
    fixture_root = Path(__file__).resolve().parents[1] / "fixtures" / "market_data"
    for scenario in FIXTURE_SCENARIOS:
        path = fixture_root / f"{scenario}.json"
        assert path.exists()
        committed = DatasetPackage.model_validate_json(path.read_text(encoding="utf-8"))
        assert canonicalize(committed) == canonicalize(build_fixture(scenario))


@pytest.mark.contract
def test_prompt3_schemas_expose_required_contracts() -> None:
    documents = schema_documents()

    assert {
        "market-records.schema.json",
        "instrument-metadata.schema.json",
        "dataset-manifest.schema.json",
        "quality-report.schema.json",
        "dataset-package.schema.json",
    } <= set(documents)
    metadata_schema = documents["instrument-metadata.schema.json"]
    assert isinstance(metadata_schema, dict)
    assert {
        "asset_class",
        "venue",
        "symbol",
        "canonical_symbol",
        "tick_size",
        "step_size",
        "lot_size",
        "minimum_quantity",
        "minimum_notional",
        "active_from",
        "active_to",
        "known_at",
        "metadata_version",
    } <= set(metadata_schema["properties"])


@pytest.mark.contract
def test_prompt6_schemas_expose_plan_artifact_and_ledgers() -> None:
    documents = schema_documents()

    assert {
        "backtest/plan.schema.json",
        "backtest/artifact.schema.json",
        "backtest/order-ledger-entry.schema.json",
        "backtest/fill-ledger-entry.schema.json",
        "backtest/position-ledger-entry.schema.json",
        "backtest/pnl-ledger-entry.schema.json",
    } <= set(documents)
    artifact = documents["backtest/artifact.schema.json"]
    assert isinstance(artifact, dict)
    assert {"manifest", "result"} <= set(artifact["properties"])
