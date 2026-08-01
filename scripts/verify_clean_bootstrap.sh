#!/usr/bin/env bash
set -euo pipefail

repository_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${repository_root}"

required_commands=(git uv node npm docker curl)
for command_name in "${required_commands[@]}"; do
  if ! command -v "${command_name}" >/dev/null 2>&1; then
    echo "BLOCKED: required command is unavailable: ${command_name}" >&2
    exit 1
  fi
done

if [[ -n "$(git status --porcelain)" ]]; then
  echo "FAIL: fresh-clone verification requires a clean worktree" >&2
  exit 1
fi

uv sync --locked
npm ci --prefix web

uv run ruff format --check .
uv run ruff check .
uv run mypy
uv run python scripts/validate_workflows.py
uv run python scripts/scan_secrets.py
uv run pytest -m "not connected" --cov=tradeguard --cov-report=term-missing
uv build

npm run check --prefix web
npm test --prefix web
npm run build --prefix web

docker compose config --quiet
docker compose build
docker compose up -d
trap 'docker compose down --volumes' EXIT

for endpoint in \
  "http://127.0.0.1:8000/health/ready" \
  "http://127.0.0.1:8001/health/ready" \
  "http://127.0.0.1:8002/health/ready" \
  "http://127.0.0.1:3000"; do
  ready=0
  for _attempt in $(seq 1 30); do
    if curl --fail --silent --show-error "${endpoint}" >/dev/null; then
      ready=1
      break
    fi
    sleep 2
  done
  if [[ "${ready}" -ne 1 ]]; then
    echo "FAIL: service did not become ready: ${endpoint}" >&2
    exit 1
  fi
done

uv run python scripts/collect_evidence.py
echo "PASS: clean bootstrap verified"
