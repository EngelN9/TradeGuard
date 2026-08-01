"""Immutable dataset manifests and reproducible partition identity."""

from __future__ import annotations

from typing import Annotated, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from tradeguard.data.lineage import TransformationGraph
from tradeguard.data.models import SupportedAssetClass
from tradeguard.domain.serialization import UtcDateTime, deterministic_checksum

DATASET_MANIFEST_SCHEMA_VERSION = "1.0.0"
NonEmptyText = Annotated[str, Field(min_length=1, max_length=2048)]
Checksum = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]


class ManifestModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", validate_default=True)


class DataInterval(ManifestModel):
    start_utc: UtcDateTime
    end_utc: UtcDateTime

    @model_validator(mode="after")
    def validate_order(self) -> Self:
        if self.end_utc <= self.start_utc:
            raise ValueError("data interval end must follow start")
        return self


class DatasetPartition(ManifestModel):
    partition_id: NonEmptyText
    relative_path: NonEmptyText
    row_count: Annotated[int, Field(ge=0)]
    date_range: DataInterval
    checksum: Checksum

    @model_validator(mode="after")
    def validate_relative_path(self) -> Self:
        normalized = self.relative_path.replace("\\", "/")
        if (
            normalized.startswith("/")
            or ":" in normalized.split("/", maxsplit=1)[0]
            or ".." in normalized.split("/")
        ):
            raise ValueError("partition path must be repository-relative and traversal-free")
        return self


class MissingInterval(ManifestModel):
    date_range: DataInterval
    reason: NonEmptyText


class DataCorrection(ManifestModel):
    correction_id: NonEmptyText
    description: NonEmptyText
    known_at: UtcDateTime
    affected_range: DataInterval
    previous_checksum: Checksum
    corrected_checksum: Checksum


class ParentDataset(ManifestModel):
    dataset_id: NonEmptyText
    manifest_checksum: Checksum


class DatasetManifest(ManifestModel):
    """Complete identity, provenance, and quality context for one dataset."""

    schema_version: Literal["1.0.0"] = "1.0.0"
    dataset_id: NonEmptyText
    dataset_version: NonEmptyText
    source: NonEmptyText
    asset_class: SupportedAssetClass
    symbols: Annotated[tuple[NonEmptyText, ...], Field(min_length=1)]
    date_range: DataInterval
    row_count: Annotated[int, Field(ge=0)]
    partition_information: Annotated[tuple[DatasetPartition, ...], Field(min_length=1)]
    checksums: dict[NonEmptyText, Checksum]
    created_at: UtcDateTime
    ingested_at: UtcDateTime
    licensing_notes: NonEmptyText
    missing_intervals: tuple[MissingInterval, ...] = ()
    corrections: tuple[DataCorrection, ...] = ()
    parent_dataset: ParentDataset | None = None
    transformation_graph: TransformationGraph = Field(default_factory=TransformationGraph)

    @model_validator(mode="after")
    def validate_manifest_integrity(self) -> Self:
        if tuple(sorted(set(self.symbols))) != self.symbols:
            raise ValueError("symbols must be unique and sorted")
        if not self.checksums:
            raise ValueError("at least one dataset checksum is required")
        partition_ids = [partition.partition_id for partition in self.partition_information]
        if len(set(partition_ids)) != len(partition_ids):
            raise ValueError("partition_id values must be unique")
        if sum(partition.row_count for partition in self.partition_information) != self.row_count:
            raise ValueError("partition row counts must equal manifest row_count")
        for partition in self.partition_information:
            if (
                partition.date_range.start_utc < self.date_range.start_utc
                or partition.date_range.end_utc > self.date_range.end_utc
            ):
                raise ValueError("partition date range must be inside dataset date range")
        if self.ingested_at < self.created_at:
            raise ValueError("ingested_at must not precede created_at")
        if self.transformation_graph.steps:
            final_output = self.transformation_graph.steps[-1].output_dataset_id
            if final_output != self.dataset_id:
                raise ValueError("final lineage output must equal dataset_id")
        return self

    def checksum(self) -> str:
        """Return the deterministic checksum of the complete manifest."""

        return deterministic_checksum(self)
