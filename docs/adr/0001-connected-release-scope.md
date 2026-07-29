# ADR 0001: Connected Release v0.1.0 Scope

- Status: Proposed — human approval required
- Date: 2026-07-29
- Decision owners: Unassigned
- Target release: v0.1.0

## Context

TradeGuard currently contains planning and safety documentation but no executable
implementation. `PROMPTS.md` defines a Connected Release that must demonstrate
real public equity data, real public crypto REST/WebSocket data, deterministic
paper behavior, one external non-live integration, validation, risk, monitoring,
API/dashboard, and reproducible evidence.

The main risk is not simply software failure. A false claim of data quality,
backtest validity, reconciliation health, or release readiness could mislead a
researcher. A live-capable or over-privileged adapter would also violate the
project boundary.

Provider and credential choices introduce licensing, entitlement, regional,
rate-limit, schema, endpoint-confusion, and evidence-retention risks. Those
choices require explicit human approval and cannot be inferred from convenience.

## Proposed decision

Build v0.1.0 as a modular monolith for a trusted single-user or small-team
deployment with:

- Python 3.12+, FastAPI, Pydantic, SQLAlchemy/Alembic, PostgreSQL, and a
  reproducible `uv` lock;
- TypeScript/React/Next.js dashboard consuming only the backend API;
- content-addressed data and artifacts;
- a deterministic event-driven backtester and internal paper broker;
- separate equity-cash and crypto-spot market/cost/execution rules;
- immutable manifests and evidence;
- one human-approved public equity data provider;
- one human-approved public crypto REST/WebSocket provider;
- one human-approved paper, sandbox, or read-only account adapter;
- default offline CI with recorded fixtures;
- separately invoked opt-in connected qualification;
- supported environments limited to `research`, `backtest`, `replay`, `paper`,
  and `shadow`.

`research` is the default and `shadow` is the maximum environment. `canary`,
`live`, leverage, borrowing, shorting, derivatives, withdrawal, transfer, and
credential management are absent.

Strategies are trusted local packages registered through an allowlist. They may
only emit `Signal`, `TargetPosition`, or `TradeProposal`. They cannot access
provider clients, credentials, risk configuration, or direct order APIs.

## Decisions deliberately deferred

- Equity public-data provider.
- Crypto public REST/WebSocket provider.
- External non-live adapter.
- Credential scopes and endpoint allowlists for those providers.
- Software license.
- Security contact.
- Owners and accepted provider terms.

The candidate matrix and decision record requirements are in
`docs/release/connected-release-v1.md`.

## Alternatives considered

### Documentation-only or fully offline v0.1.0

Rejected as the Connected Release target because it would not qualify external
schema, timestamp, rate-limit, reconnect, or regional behavior. Offline fixtures
remain mandatory but cannot be mislabeled as connected evidence.

### Live-capable unified trading adapter

Rejected. A shared adapter that can switch between paper and live creates an
unacceptable environment-confusion path for the first release. External
integration is paper-, sandbox-, or read-only-specific and rejects production
trading endpoints.

### Microservices from the first milestone

Rejected for v0.1.0. They increase deployment, identity, network, ordering, and
reproducibility complexity without a demonstrated need. Module boundaries and
protocols remain explicit so later extraction is possible through a new ADR.

### Browser-only research engine

Rejected. Backtests, ingestion, monitoring, and evidence collection are backend
jobs. The browser is not a durable or authoritative execution environment.

### Arbitrary uploaded Python strategies

Rejected for v0.1.0. Python language-level restrictions do not safely sandbox
untrusted code. Trusted local code plus a narrow protocol is the supported
boundary until process/container isolation is separately designed and reviewed.

### Automatic provider fallback

Rejected. Silent fallback can mix licenses, schemas, timestamps, adjustment
semantics, or data quality. A provider change requires explicit configuration,
new manifests, and evidence.

## Consequences

### Positive

- Research claims have deterministic, reviewable evidence.
- Strategies cannot bypass an independent risk decision.
- Offline CI is reproducible without secrets.
- Connected failures and unavailable credentials are visible as `FAIL` or
  `BLOCKED`, never fabricated as success.
- Market-specific costs, sessions, precision, and stress risks remain separate.
- The absence of live-capable endpoints reduces asset-safety risk.

### Costs and limitations

- A human must review providers, terms, permissions, and release gates.
- Connected qualification cannot be a default fork-PR gate.
- Provider snapshots may differ across observation windows; reproducibility
  applies to captured bytes and normalized results, not to an ever-changing live
  market.
- The first release is not multi-tenant and does not safely run untrusted code.
- A modular monolith limits independent scaling until a later ADR.
- Some connected tests may truthfully remain `BLOCKED` due to credentials,
  geography, market hours, or provider availability.

## Acceptance criteria

This ADR may become `Accepted` only when a maintainer:

1. approves the release contract and non-goals;
2. selects the three required adapter categories and records terms review;
3. approves hostname/environment allowlists and least-privilege scopes;
4. selects a software license and security contact;
5. assigns data, risk, security, release, and connected-test owners.

Implementation promotion still follows every later Prompt and human review gate.
Acceptance of this ADR is not approval to publish, tag, connect credentials, or
trade.

## Rollback

Before implementation, rollback is deletion/reversion of this proposed decision.
After implementation, any scope reversal requires:

- disabling affected adapters;
- retaining adverse evidence and audit history;
- invalidating impacted qualification results;
- reverting to the last verified schema/config/model version;
- updating this ADR or superseding it with a new reviewed ADR.

Rollback must never introduce a live fallback or rewrite historical evidence.
