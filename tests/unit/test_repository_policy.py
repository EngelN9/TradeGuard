"""Repository-level policy tests for the Prompt 1 bootstrap."""

from pathlib import Path

import pytest
import yaml

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.unit
def test_compose_declares_required_services_and_non_live_security() -> None:
    compose = yaml.safe_load((REPOSITORY_ROOT / "docker-compose.yml").read_text(encoding="utf-8"))
    services = compose["services"]

    assert {
        "postgres",
        "api",
        "worker",
        "mock-market-data",
        "paper-broker",
        "dashboard",
    } <= set(services)
    assert "live" not in services
    for service_name in ("api", "worker", "mock-market-data", "paper-broker", "dashboard"):
        service = services[service_name]
        assert service["read_only"] is True
        assert service["cap_drop"] == ["ALL"]
        assert "no-new-privileges:true" in service["security_opt"]


@pytest.mark.unit
def test_makefile_has_required_targets_and_no_live_target() -> None:
    makefile = (REPOSITORY_ROOT / "Makefile").read_text(encoding="utf-8")
    required_targets = {
        "setup",
        "format",
        "lint",
        "typecheck",
        "test",
        "test-unit",
        "test-property",
        "test-integration",
        "test-contract",
        "test-replay",
        "test-connected",
        "evidence",
        "dev-up",
        "dev-down",
    }

    for target in required_targets:
        assert f"\n{target}:" in f"\n{makefile}"
    assert "\nlive:" not in f"\n{makefile}"
    assert 'TRADEGUARD_RUN_CONNECTED" != "1"' in makefile


@pytest.mark.unit
def test_backend_container_runs_as_non_root() -> None:
    dockerfile = (REPOSITORY_ROOT / "Dockerfile").read_text(encoding="utf-8")

    assert "USER tradeguard" in dockerfile
    assert "uv==" in dockerfile
    assert "COPY .env" not in dockerfile
    assert "docker.sock" not in dockerfile


@pytest.mark.unit
def test_example_environment_contains_only_safe_defaults() -> None:
    example = (REPOSITORY_ROOT / ".env.example").read_text(encoding="utf-8")

    assert "TRADEGUARD_ENV=research" in example
    assert "TRADEGUARD_RUN_CONNECTED=0" in example
    assert "local-development-only" in example
    assert "live" not in example.lower()
