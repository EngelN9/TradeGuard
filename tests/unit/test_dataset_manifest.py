"""Unit tests for dataset manifests, lineage, and content-addressed storage."""

from pathlib import Path

import pytest
from pydantic import ValidationError

from tradeguard.data.fixtures import build_fixture
from tradeguard.data.lineage import TransformationGraph, TransformationStep
from tradeguard.data.manifest import DatasetManifest, DatasetPartition
from tradeguard.data.storage import ContentAddressedStore, ContentIntegrityError
from tradeguard.domain.serialization import deterministic_checksum


@pytest.mark.unit
def test_manifest_and_lineage_checksums_are_deterministic() -> None:
    first = build_fixture("normal").manifest
    second = build_fixture("normal").manifest

    assert first == second
    assert first.checksum() == second.checksum()
    assert first.transformation_graph.checksum() == second.transformation_graph.checksum()
    assert first.transformation_graph.steps[-1].output_dataset_id == first.dataset_id


@pytest.mark.unit
def test_manifest_rejects_unsorted_symbols_and_partition_count_mismatch() -> None:
    manifest = build_fixture("normal").manifest
    document = manifest.model_dump(mode="python")
    document["symbols"] = ("ZZZ", "AAA")
    with pytest.raises(ValidationError, match="unique and sorted"):
        DatasetManifest.model_validate(document)

    document = manifest.model_dump(mode="python")
    document["row_count"] = manifest.row_count + 1
    with pytest.raises(ValidationError, match="partition row counts"):
        DatasetManifest.model_validate(document)


@pytest.mark.unit
def test_partition_rejects_absolute_and_traversal_paths() -> None:
    partition = build_fixture("normal").manifest.partition_information[0]
    document = partition.model_dump(mode="python")
    document["relative_path"] = "../secret.json"

    with pytest.raises(ValidationError, match="traversal-free"):
        DatasetPartition.model_validate(document)


@pytest.mark.unit
def test_lineage_rejects_cycles_and_duplicate_outputs() -> None:
    parameters_hash = deterministic_checksum({"fixture": True})
    with pytest.raises(ValidationError, match="acyclic"):
        TransformationGraph(
            steps=(
                TransformationStep(
                    transformation_id="a",
                    operation="test",
                    implementation_version="1",
                    input_dataset_ids=("b-output",),
                    output_dataset_id="a-output",
                    parameters_hash=parameters_hash,
                ),
                TransformationStep(
                    transformation_id="b",
                    operation="test",
                    implementation_version="1",
                    input_dataset_ids=("a-output",),
                    output_dataset_id="b-output",
                    parameters_hash=parameters_hash,
                ),
            )
        )


@pytest.mark.unit
def test_content_addressed_store_is_idempotent_and_detects_tampering(
    tmp_path: Path,
) -> None:
    store = ContentAddressedStore(tmp_path / "raw")
    first = store.put(b"synthetic raw bytes")
    second = store.put(b"synthetic raw bytes")

    assert first.checksum == second.checksum
    assert first.created is True
    assert second.created is False
    assert store.read(first.checksum) == b"synthetic raw bytes"

    blob_path = tmp_path / "raw" / first.relative_path
    blob_path.write_bytes(b"tampered")
    with pytest.raises(ContentIntegrityError):
        store.read(first.checksum)
    with pytest.raises(ContentIntegrityError):
        store.put(b"synthetic raw bytes")


@pytest.mark.unit
def test_content_addressed_store_rejects_invalid_checksum(tmp_path: Path) -> None:
    store = ContentAddressedStore(tmp_path)

    with pytest.raises(ValueError, match="lowercase SHA-256"):
        store.read("not-a-checksum")
