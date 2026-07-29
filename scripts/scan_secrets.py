"""Fail a baseline scan on credential-shaped repository content."""

from __future__ import annotations

import re
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
EXCLUDED_DIRECTORIES = {
    ".git",
    ".hypothesis",
    ".mypy_cache",
    ".next",
    ".pytest_cache",
    ".pytest-tmp",
    ".ruff_cache",
    ".venv",
    "artifacts",
    "node_modules",
}
PATTERNS = {
    "private-key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "aws-access-key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "github-token": re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}\b"),
    "slack-token": re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{20,}\b"),
    "jwt": re.compile(r"\beyJ[A-Za-z0-9_-]{15,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b"),
    "generic-assignment": re.compile(
        r"(?i)\b(?:api[_-]?key|client[_-]?secret|access[_-]?token)"
        r"\s*[=:]\s*[\"']?[A-Za-z0-9+/=_-]{24,}"
    ),
}
PLACEHOLDER_WORDS = {
    "<token>",
    "example",
    "fake",
    "placeholder",
    "replace-with",
    "your_api_key",
}


def candidate_files(root: Path) -> list[Path]:
    """Return repository text candidates without generated/dependency trees."""

    files = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in EXCLUDED_DIRECTORIES for part in path.parts):
            continue
        files.append(path)
    return files


def scan_file(path: Path) -> list[tuple[int, str]]:
    """Return redacted finding locations for one text file."""

    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (UnicodeDecodeError, OSError):
        return []

    findings = []
    for line_number, line in enumerate(lines, start=1):
        normalized = line.lower()
        if any(word in normalized for word in PLACEHOLDER_WORDS):
            continue
        for name, pattern in PATTERNS.items():
            if pattern.search(line):
                findings.append((line_number, name))
    return findings


def main() -> int:
    """Scan and print only finding type and path, never the matched value."""

    findings = []
    for path in candidate_files(REPOSITORY_ROOT):
        for line_number, name in scan_file(path):
            findings.append(f"{path.relative_to(REPOSITORY_ROOT)}:{line_number}:{name}")

    if findings:
        print("Secret-shaped content detected:")
        print("\n".join(findings))
        return 1

    print("Secret baseline scan passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
