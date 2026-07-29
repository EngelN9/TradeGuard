"""Deterministic transformation lineage with cycle detection."""

from __future__ import annotations

from typing import Annotated, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from tradeguard.domain.serialization import deterministic_checksum

NonEmptyText = Annotated[str, Field(min_length=1, max_length=512)]
Checksum = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]


class LineageModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", validate_default=True)


class TransformationStep(LineageModel):
    """One versioned transformation from one or more datasets to one dataset."""

    transformation_id: NonEmptyText
    operation: NonEmptyText
    implementation_version: NonEmptyText
    input_dataset_ids: Annotated[tuple[NonEmptyText, ...], Field(min_length=1)]
    output_dataset_id: NonEmptyText
    parameters_hash: Checksum

    @model_validator(mode="after")
    def validate_identity(self) -> Self:
        if self.output_dataset_id in self.input_dataset_ids:
            raise ValueError("a transformation cannot directly consume its own output")
        if len(set(self.input_dataset_ids)) != len(self.input_dataset_ids):
            raise ValueError("lineage inputs must be unique")
        return self


class TransformationGraph(LineageModel):
    """Immutable directed acyclic transformation graph."""

    steps: tuple[TransformationStep, ...] = ()

    @model_validator(mode="after")
    def validate_dag(self) -> Self:
        transformation_ids = [step.transformation_id for step in self.steps]
        outputs = [step.output_dataset_id for step in self.steps]
        if len(set(transformation_ids)) != len(transformation_ids):
            raise ValueError("transformation_id values must be unique")
        if len(set(outputs)) != len(outputs):
            raise ValueError("each dataset may be produced by only one transformation")

        dependencies = {
            step.output_dataset_id: {
                input_id for input_id in step.input_dataset_ids if input_id in outputs
            }
            for step in self.steps
        }
        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(dataset_id: str) -> None:
            if dataset_id in visiting:
                raise ValueError("transformation graph must be acyclic")
            if dataset_id in visited:
                return
            visiting.add(dataset_id)
            for dependency in dependencies.get(dataset_id, set()):
                visit(dependency)
            visiting.remove(dataset_id)
            visited.add(dataset_id)

        for output in outputs:
            visit(output)
        return self

    def checksum(self) -> str:
        """Return a deterministic lineage checksum."""

        return deterministic_checksum(self)
