# Engineering, testing, and evidence standards

Status: `NORMATIVE`

## Architecture and dependency policy

TradeGuard is a modular monolith until an accepted ADR demonstrates a concrete
isolation or scaling need. Research, monitoring, and control are logical
planes, not automatic microservice boundaries. Long-running work runs in a
backend process, never only in a browser.

The current baseline is Python 3.12+, Pydantic, FastAPI, a reproducible `uv`
lock, pytest/Hypothesis, Ruff, strict mypy, Docker/Compose, GitHub Actions, and
a TypeScript/React/Next.js read-oriented dashboard. PostgreSQL, SQLAlchemy,
Alembic, analytical libraries, a queue, cache, or new service are added only
when a current vertical slice needs them. A durable queue requires an ADR.

Every new dependency needs a current consumer, lockfile update, license and
vulnerability review, maintenance owner, removal path, and evidence that an
existing dependency or standard library is insufficient.

## Authoritative values and time

Money, prices, quantities, fees, taxes, notional exposure, and balances use
`decimal.Decimal` or an explicit decimal database type at authoritative
boundaries. Binary floats are rejected there. Statistical/matrix computation
may use floats only with documented conversions, tolerances, and boundary
tests.

Every authoritative timestamp is timezone-aware. Internal time is UTC; display
conversion is non-authoritative. Naive datetimes and guessed timezones fail.

## Configuration

Configuration is versioned, schema-validated, deterministically hashed,
inspectable in its effective merged form, separated into sensitive and
non-sensitive fields, redacted for display, audited, and rollback-capable.

Supported layers are base, environment, market, venue, data, strategy,
portfolio, risk, cost, monitoring, alerting, and an explicitly reviewed user
override. Changes record actor, reason, time, environment, before/after hashes,
and version. Invalid configuration rejects startup.

Only `research`, `backtest`, `replay`, `paper`, and `shadow` are valid runtime
environments. The repository must not contain a live/canary alias or target.

## Reproducible runs

Each research, backtest, replay, paper qualification, and validation run binds:

- `run_id`, run type, strategy ID/version;
- Git SHA and dirty-worktree flag;
- effective config version/hash;
- dataset IDs/manifests, range, universe, and point-in-time cut-off;
- random seed;
- Python, platform/container, and dependency-lock identity;
- cost, slippage, and execution model versions;
- start/completion UTC times;
- result checksum, warnings, and validation failures.

Equivalent input, version, configuration, seed, cost, and execution model must
produce the same deterministic result. Dirty, incomplete, unbound, or
validation-failing runs cannot qualify a release or promotion.

## Test architecture

Tests must be proportional to the behavior and risk.

### Unit

Cover Decimal/precision, UTC/timezone, sessions, corporate actions, costs,
fills, risk limits, configuration, data quality, metrics, strategy contracts,
and every new branch with material semantics.

### Property

Cover cash and asset conservation, post-fill position consistency, non-negative
fees, exposure consistency, fill idempotency, event idempotency, monotonic time,
risk non-bypass, fail-closed unknown state, and reconciliation differences not
being ignored.

### Integration and contract

Cover data-to-backtest, strategy-to-risk, risk-to-report, paper ingestion,
adapter reconnect, persistence when present, API/OpenAPI, and dashboard read
paths. External adapters require sanitized recorded contracts and schema-drift
tests. Connected tests are separate and opt-in.

### Replay and regression

Replay fixtures cover gaps, duplicates, disorder, bad timestamps, partial and
rejected fills, rate limits, timeouts, reconnect, maintenance, halts, splits,
stablecoin depeg, spread expansion, crashes, and source mispricing as the
corresponding modules become current.

Every material bug fix adds a minimal fixture, a regression test, a root-cause
note, and a prevention check. Do not add future replay fixtures merely to imply
an unimplemented capability.

## CI and supply chain

Every applicable pull request runs formatting, lint, strict typing, unit,
property, integration, contract, replay/regression, security/policy checks, and
builds. E2E, migrations, schemas, dependency/container scans, and golden files
are required when their surfaces change.

GitHub workflows use minimal permissions, SHA-pinned third-party actions, no
privileged `pull_request_target` execution of untrusted code, and no secrets in
fork/default CI. A connected smoke is never a default gate and an unexecuted
smoke is never `PASS`.

It is prohibited to make CI pass by deleting tests, weakening controls,
ignoring costs, swallowing exceptions, converting assertions to logs, adding
unjustified tolerance, making deterministic tests flaky, or fabricating
output.

## Evidence and reports

Generated evidence records producer, Git SHA, run ID, config/data/model
identity, checksum, creation time, and validation status. Finalized evidence is
content-addressed or append-only, path-traversal safe, redacted, tamper-
detectable, and never silently replaced.

Reports show favorable and unfavorable results, failed splits, warnings,
missing evidence, point-in-time limits, costs, execution assumptions, risk,
known limitations, failure conditions, manifests, and checksums. No report may
hide a failed validation or imply that simulation is live performance.

`reports/` and `artifacts/` must not contain credentials, private account data,
licensed raw payloads whose publication is forbidden, or workstation identity
that is unnecessary for verification.

## Repository structure and changes

Use the existing module layout under `src/tradeguard/`, tests under `tests/`,
configuration under `configs/`, and durable specifications under `docs/`.
Create a new top-level directory only for a current, owned capability.

Changes are small, typed, independently reviewable, and backward compatible
unless a versioned migration is explicitly approved. Avoid global mutable
state, implicit I/O, hidden external calls, unvalidated inputs, and
undocumented randomness.

Schema changes require a version/compatibility policy, generated snapshot, and
migration or explicit fail-closed rejection. Data corrections create new
lineage; old source/evidence is retained.

## Pull request acceptance

An applicable PR must state objective, scope/non-goals, assumptions, files,
behavior, architecture decisions, risk/security impact, tests and exact
results, evidence, limitations, rollback, remaining work, and promotion state.

Review verifies at minimum:

- no secrets, private account data, or restricted raw provider data;
- no live/canary/order/withdrawal/transfer path;
- UTC/Decimal/point-in-time and market-specific rules remain intact;
- data, cost, look-ahead, risk, reconciliation, and evidence gates are not
  weakened;
- relevant tests, schemas, builds, scans, and rollback pass;
- public status and implementation matrix match the actual branch;
- automated checks are not described as human promotion approval.

## Rollback and maintenance

Every stage has a defined rollback to the last verified contract/model/data
version. Rollback preserves adverse evidence and never activates a fallback
provider or live endpoint. Migrations must be reversible or document an
approved forward-recovery plan before use.

The owner named by the scope/release ladder maintains dependencies, provider
terms, schemas, fixtures, gates, runbooks, and deprecation. An unowned feature
does not advance.
