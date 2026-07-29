"""Validate minimal GitHub Actions permissions and immutable action pins."""

from __future__ import annotations

import re
from collections.abc import Iterator
from pathlib import Path

import yaml

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_ROOT = REPOSITORY_ROOT / ".github" / "workflows"
FULL_SHA = re.compile(r"^[0-9a-f]{40}$")


def walk_values(value: object) -> Iterator[object]:
    """Yield nested YAML values."""

    yield value
    if isinstance(value, dict):
        for child in value.values():
            yield from walk_values(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk_values(child)


def validate_workflow(path: Path) -> list[str]:
    """Return policy violations for one workflow."""

    raw = path.read_text(encoding="utf-8")
    document = yaml.safe_load(raw)
    if not isinstance(document, dict):
        return ["workflow root must be a mapping"]

    errors = []
    triggers = document.get("on", document.get(True, {}))
    if isinstance(triggers, dict) and "pull_request_target" in triggers:
        errors.append("pull_request_target is prohibited")
    if "pull_request_target" in raw:
        errors.append("pull_request_target text is prohibited")

    if document.get("permissions") != {"contents": "read"}:
        errors.append("top-level permissions must be exactly contents: read")

    if "${{ secrets." in raw:
        errors.append("default workflows must not reference repository secrets")

    for value in walk_values(document):
        if not isinstance(value, str) or "@" not in value:
            continue
        if value.startswith("./"):
            continue
        if "/" not in value:
            continue
        reference = value.rsplit("@", maxsplit=1)[1]
        if not FULL_SHA.fullmatch(reference):
            errors.append(f"action is not pinned to a full SHA: {value.split('@', maxsplit=1)[0]}")

    return sorted(set(errors))


def main() -> int:
    """Validate every workflow."""

    workflows = sorted([*WORKFLOW_ROOT.glob("*.yml"), *WORKFLOW_ROOT.glob("*.yaml")])
    if not workflows:
        print("No GitHub Actions workflows found")
        return 1

    violations = []
    for workflow in workflows:
        violations.extend(
            f"{workflow.relative_to(REPOSITORY_ROOT)}: {error}"
            for error in validate_workflow(workflow)
        )

    if violations:
        print("\n".join(violations))
        return 1

    print(f"Validated {len(workflows)} workflow(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
