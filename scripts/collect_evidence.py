"""Collect a redacted bootstrap evidence skeleton."""

from __future__ import annotations

import hashlib
import json
import platform
import shutil
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

type JsonValue = str | int | float | bool | list["JsonValue"] | dict[str, "JsonValue"] | None

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_ROOT = REPOSITORY_ROOT / "artifacts" / "evidence" / "bootstrap"


def sha256_file(path: Path) -> str:
    """Return a streaming SHA-256 digest."""

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run_version(command: list[str]) -> dict[str, str]:
    """Run a local version command without failing collection when unavailable."""

    executable = shutil.which(command[0])
    if executable is None:
        return {"status": "unavailable", "value": "command not installed"}
    result = subprocess.run(  # noqa: S603 - executable and arguments are internal
        [executable, *command[1:]],
        cwd=REPOSITORY_ROOT,
        check=False,
        capture_output=True,
        text=True,
        timeout=10,
    )
    output = (result.stdout or result.stderr).strip().splitlines()
    value = output[0] if output else f"exit {result.returncode}"
    return {"status": "available" if result.returncode == 0 else "error", "value": value}


def git_value(*arguments: str) -> str:
    """Read bounded Git metadata."""

    executable = shutil.which("git")
    if executable is None:
        return "unavailable"
    result = subprocess.run(  # noqa: S603 - bounded read-only Git arguments
        [executable, "-c", f"safe.directory={REPOSITORY_ROOT.as_posix()}", *arguments],
        cwd=REPOSITORY_ROOT,
        check=False,
        capture_output=True,
        text=True,
        timeout=10,
    )
    return result.stdout.strip() if result.returncode == 0 else "unavailable"


def collect_metadata() -> dict[str, JsonValue]:
    """Collect tool, lock, Git, and container metadata without environment values."""

    lockfiles = {}
    for relative_path in ("uv.lock", "web/package-lock.json"):
        path = REPOSITORY_ROOT / relative_path
        lockfiles[relative_path] = sha256_file(path) if path.exists() else "missing"

    return {
        "schema_version": "1.0.0",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "git": {
            "sha": git_value("rev-parse", "HEAD"),
            "branch": git_value("branch", "--show-current"),
            "dirty": bool(git_value("status", "--porcelain")),
        },
        "platform": platform.platform(),
        "python": sys.version.split()[0],
        "tools": {
            "uv": run_version(["uv", "--version"]),
            "node": run_version(["node", "--version"]),
            "npm": run_version(["npm", "--version"]),
            "docker": run_version(["docker", "--version"]),
        },
        "lockfiles": lockfiles,
        "container_build": {
            "status": "not-built-by-collector",
            "reason": "container build metadata is populated by CI or release qualification",
        },
        "redaction": {
            "environment_values_collected": False,
            "secrets_collected": False,
        },
    }


def build_index(root: Path) -> list[dict[str, str]]:
    """Index evidence files except the index itself."""

    entries = []
    for path in sorted(candidate for candidate in root.rglob("*") if candidate.is_file()):
        relative = path.relative_to(root).as_posix()
        if relative == "index.json":
            continue
        entries.append(
            {
                "path": relative,
                "sha256": sha256_file(path),
            }
        )
    return entries


def write_json(path: Path, value: JsonValue) -> None:
    """Write stable human-readable JSON."""

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def main() -> int:
    """Create bootstrap metadata and its checksum index."""

    build_directory = EVIDENCE_ROOT / "build"
    tests_directory = EVIDENCE_ROOT / "tests"
    build_directory.mkdir(parents=True, exist_ok=True)
    tests_directory.mkdir(parents=True, exist_ok=True)
    write_json(build_directory / "build-metadata.json", collect_metadata())
    write_json(
        EVIDENCE_ROOT / "index.json",
        {
            "schema_version": "1.0.0",
            "evidence_stage": "bootstrap",
            "artifacts": build_index(EVIDENCE_ROOT),
        },
    )
    print(EVIDENCE_ROOT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
