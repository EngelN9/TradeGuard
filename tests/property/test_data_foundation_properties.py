"""Property checks for point-in-time, storage, and evidence invariants."""

import hashlib
import tempfile
from datetime import timedelta
from pathlib import Path

import pytest
from hypothesis import given
from hypothesis import strategies as st

from tradeguard.data.fixtures import build_fixture
from tradeguard.data.quality import (
    QualityStatus,
    ValidationEvidenceRejectedError,
    require_validation_evidence_eligible,
)
from tradeguard.data.storage import ContentAddressedStore


@pytest.mark.property
@given(st.binary(max_size=512))
def test_content_address_is_deterministic_and_content_sensitive(content: bytes) -> None:
    assert ContentAddressedStore.checksum_bytes(content) == hashlib.sha256(content).hexdigest()
    assert ContentAddressedStore.checksum_bytes(content) == ContentAddressedStore.checksum_bytes(
        bytes(content)
    )
    if content:
        changed = bytes([content[0] ^ 1]) + content[1:]
        assert ContentAddressedStore.checksum_bytes(
            content
        ) != ContentAddressedStore.checksum_bytes(changed)


@pytest.mark.property
@given(st.integers(min_value=-365, max_value=365))
def test_metadata_is_never_known_before_known_at(offset_days: int) -> None:
    metadata = build_fixture("normal").instrument_metadata[0]
    knowledge_time = metadata.known_at + timedelta(days=offset_days)

    assert metadata.is_known_at(knowledge_time) is (offset_days >= 0)


@pytest.mark.property
@given(st.sampled_from([QualityStatus.FAIL, QualityStatus.QUARANTINED]))
def test_unsafe_quality_status_never_enters_validation_evidence(
    status: QualityStatus,
) -> None:
    scenario = "gap" if status is QualityStatus.FAIL else "bad_tick"
    package = build_fixture(scenario)
    report = package.validate_quality()

    assert report.status is status
    with pytest.raises(ValidationEvidenceRejectedError):
        require_validation_evidence_eligible(package.manifest, report)


@pytest.mark.property
@given(st.binary(min_size=1, max_size=128))
def test_content_store_repeated_write_never_creates_second_blob(
    content: bytes,
) -> None:
    with tempfile.TemporaryDirectory() as directory:
        store = ContentAddressedStore(Path(directory))

        first = store.put(content)
        second = store.put(content)

        assert first.checksum == second.checksum
        assert first.created is True
        assert second.created is False


@pytest.mark.property
def test_transformed_dataset_identity_rebuilds_exactly() -> None:
    first = build_fixture("normal")
    second = build_fixture("normal")

    assert first.manifest.checksum() == second.manifest.checksum()
    assert first.manifest.transformation_graph.checksum() == (
        second.manifest.transformation_graph.checksum()
    )
