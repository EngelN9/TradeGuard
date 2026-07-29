"""Portable offline dataset package used by fixtures and data CLI commands."""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, ConfigDict, JsonValue

from tradeguard.data.manifest import DatasetManifest
from tradeguard.data.models import (
    CorporateAction,
    InstrumentMetadata,
    MaintenanceInterval,
    MarketSession,
)
from tradeguard.data.quality import (
    QualityContext,
    QualityGate,
    QualityPolicy,
    QualityReport,
    QualityStatus,
)


class DatasetPackage(BaseModel):
    """Self-contained, synthetic/offline input for deterministic validation."""

    model_config = ConfigDict(frozen=True, extra="forbid", validate_default=True)

    manifest: DatasetManifest
    policy: QualityPolicy
    instrument_metadata: tuple[InstrumentMetadata, ...]
    market_sessions: tuple[MarketSession, ...] = ()
    corporate_actions: tuple[CorporateAction, ...] = ()
    maintenance_intervals: tuple[MaintenanceInterval, ...] = ()
    records: tuple[dict[str, JsonValue], ...]
    expected_quality_status: QualityStatus | None = None

    def quality_context(self) -> QualityContext:
        return QualityContext(
            manifest=self.manifest,
            policy=self.policy,
            instrument_metadata=self.instrument_metadata,
            market_sessions=self.market_sessions,
            corporate_actions=self.corporate_actions,
            maintenance_intervals=self.maintenance_intervals,
        )

    def validate_quality(self) -> QualityReport:
        """Run the deterministic quality gate over the packaged records."""

        report = QualityGate().validate(self.records, self.quality_context())
        if (
            self.expected_quality_status is not None
            and report.status is not self.expected_quality_status
        ):
            raise ValueError("quality result differs from fixture expectation")
        return report


def load_dataset_package(path: Path) -> DatasetPackage:
    """Load one UTF-8 JSON package with strict schema validation."""

    return DatasetPackage.model_validate_json(path.read_text(encoding="utf-8"))
