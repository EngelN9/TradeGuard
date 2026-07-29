"""Unit tests for reproducible run manifests."""

from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError
from tests.factories import completed_run_manifest

from tradeguard.experiments.manifest import RunDateRange, RunManifest


@pytest.mark.unit
def test_completed_clean_manifest_is_release_qualifiable() -> None:
    manifest = completed_run_manifest()

    assert manifest.release_qualifiable is True
    assert len(manifest.checksum()) == 64
    manifest.require_release_qualifiable()


@pytest.mark.unit
def test_dirty_manifest_is_recorded_and_rejected_for_release() -> None:
    manifest = completed_run_manifest(dirty=True)

    assert manifest.dirty_worktree is True
    assert manifest.release_qualifiable is False
    with pytest.raises(ValueError, match="not eligible"):
        manifest.require_release_qualifiable()


@pytest.mark.unit
def test_manifest_rejects_naive_time_and_incomplete_result_pair() -> None:
    payload = completed_run_manifest().model_dump(mode="python")
    payload["started_at"] = datetime(2024, 1, 1)  # noqa: DTZ001 - intentional invalid input
    with pytest.raises(ValidationError, match="timezone-aware"):
        RunManifest.model_validate(payload)

    payload = completed_run_manifest().model_dump(mode="python")
    payload["result_checksum"] = None
    with pytest.raises(ValidationError, match="must be set together"):
        RunManifest.model_validate(payload)


@pytest.mark.unit
def test_manifest_rejects_reversed_ranges_and_completion() -> None:
    now = datetime(2024, 1, 2, tzinfo=UTC)
    with pytest.raises(ValidationError, match="must not be reversed"):
        RunDateRange(start_utc=now, end_utc=now - timedelta(seconds=1))

    payload = completed_run_manifest().model_dump(mode="python")
    payload["completed_at"] = payload["started_at"] - timedelta(seconds=1)  # type: ignore[operator]
    with pytest.raises(ValidationError, match="must not precede"):
        RunManifest.model_validate(payload)


@pytest.mark.unit
def test_validation_failure_blocks_release_qualification() -> None:
    manifest = completed_run_manifest().model_copy(
        update={"validation_failures": ("data quality gate failed",)}
    )

    assert manifest.release_qualifiable is False
