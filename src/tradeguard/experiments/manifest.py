"""Immutable reproducibility manifest for research and validation runs."""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated, Literal, Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from tradeguard.domain.serialization import UtcDateTime, deterministic_checksum

Checksum = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
GitSha = Annotated[str, Field(pattern=r"^[0-9a-f]{40}$")]
NonEmptyText = Annotated[str, Field(min_length=1, max_length=512)]


class RunType(StrEnum):
    RESEARCH = "research"
    BACKTEST = "backtest"
    REPLAY = "replay"
    VALIDATION = "validation"
    PAPER = "paper"
    SHADOW = "shadow"


class ManifestModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", validate_default=True)


class DatasetManifestReference(ManifestModel):
    dataset_id: NonEmptyText
    dataset_version: NonEmptyText
    checksum: Checksum


class RunDateRange(ManifestModel):
    start_utc: UtcDateTime
    end_utc: UtcDateTime

    @model_validator(mode="after")
    def validate_order(self) -> Self:
        if self.end_utc < self.start_utc:
            raise ValueError("run date range must not be reversed")
        return self


class RunManifest(ManifestModel):
    """Complete, immutable run identity and reproducibility record."""

    schema_version: Literal["1.0.0"] = "1.0.0"
    run_id: UUID
    run_type: RunType
    strategy_id: NonEmptyText
    strategy_version: NonEmptyText
    git_sha: GitSha
    dirty_worktree: bool
    config_hash: Checksum
    dataset_manifests: Annotated[tuple[DatasetManifestReference, ...], Field(min_length=1)]
    date_range: RunDateRange
    universe: Annotated[tuple[NonEmptyText, ...], Field(min_length=1)]
    random_seed: Annotated[int, Field(ge=0)]
    python_version: NonEmptyText
    platform: NonEmptyText
    dependency_lock_hash: Checksum
    cost_model_version: NonEmptyText
    execution_model_version: NonEmptyText
    started_at: UtcDateTime
    completed_at: UtcDateTime | None = None
    result_checksum: Checksum | None = None
    warnings: tuple[NonEmptyText, ...] = ()
    validation_failures: tuple[NonEmptyText, ...] = ()

    @model_validator(mode="after")
    def validate_completion(self) -> Self:
        if self.completed_at is not None and self.completed_at < self.started_at:
            raise ValueError("completed_at must not precede started_at")
        if (self.completed_at is None) != (self.result_checksum is None):
            raise ValueError("completed_at and result_checksum must be set together")
        return self

    @property
    def release_qualifiable(self) -> bool:
        """Return whether this result may enter release qualification."""

        return (
            not self.dirty_worktree
            and self.completed_at is not None
            and self.result_checksum is not None
            and not self.validation_failures
        )

    def require_release_qualifiable(self) -> None:
        """Fail closed when a run cannot support release qualification."""

        if not self.release_qualifiable:
            raise ValueError("run manifest is not eligible for release qualification")

    def checksum(self) -> str:
        """Return a deterministic checksum of the complete manifest."""

        return deterministic_checksum(self)
