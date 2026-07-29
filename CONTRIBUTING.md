# Contributing to TradeGuard

TradeGuard accepts contributions that preserve correctness, reproducibility,
security, risk controls, and the non-live v0.1.0 boundary.

## Before changing code

1. Read `AGENTS.md`, `README.md`, `SECURITY.md`, the relevant ADRs, and any
   narrower `AGENTS.md`.
2. Work on a branch; do not commit directly to `main`.
3. State the objective, assumptions, expected files, validation, risk impact,
   and rollback.
4. Do not request or include real credentials, private account data, or
   restricted provider data.
5. Do not introduce `canary`, `live`, withdrawal, transfer, leverage, borrowing,
   or an order path that bypasses risk review.

## Local setup

Requirements:

- Python 3.12 or newer
- `uv`
- Node.js 22 or newer
- Docker and Docker Compose for the full service skeleton
- GNU Make for the documented convenience targets

```bash
make setup
make lint
make typecheck
make test
```

Without Make:

```bash
uv sync --locked
uv run ruff format --check .
uv run ruff check .
uv run mypy
uv run pytest -m "not connected"
npm ci --prefix web
npm run check --prefix web
npm test --prefix web
npm run build --prefix web
```

Connected tests are never part of default CI. They require an explicit
`TRADEGUARD_RUN_CONNECTED=1`, an approved provider, and the least privilege
described in `docs/release/connected-release-v1.md`.

## Pull requests

- Keep changes small and independently reviewable.
- Add tests for all new behavior and regression tests for fixes.
- Preserve Decimal authority boundaries and timezone-aware UTC.
- Update documentation, manifests, schema snapshots, and evidence as applicable.
- Report failed or blocked validation honestly.
- Never delete an adverse result or weaken a risk gate to pass CI.

Security vulnerabilities must be reported through the private channel in
[SECURITY.md](SECURITY.md), not a public issue.
