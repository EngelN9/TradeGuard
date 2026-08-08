# AGENTS.md — TradeGuard repository-wide agent rules

This file is the highest-priority repository instruction for AI coding agents.
It applies to the whole repository unless a narrower `AGENTS.md` imposes
stricter requirements. Product and engineering specifications live under
`docs/`; this file defines how an agent must discover, change, and validate
them.

TradeGuard is a safety-first research system. It does not guarantee profit,
does not provide investment advice, and is not a live-trading system.

## 1. Normative language and authority

- **MUST / MUST NOT** are non-negotiable.
- **SHOULD / SHOULD NOT** require a written, reviewable reason to deviate.
- **FAIL CLOSED** means that unknown, stale, conflicting, or invalid state
  cannot create a new risk-increasing proposal, action, or promotion.
- **POINT-IN-TIME** means that research may use only information available at
  the historical decision time.
- **PROMOTION** means moving a capability, strategy, or release to a stage with
  greater operational consequence. Promotion is never automatic.

When priorities conflict, use this order:

1. correctness;
2. data integrity;
3. reproducibility;
4. information security;
5. legal and licensing compliance;
6. risk limits;
7. auditability;
8. user asset safety;
9. delivery speed or performance presentation.

Repository authority, from broad to specific:

1. this file and any narrower `AGENTS.md`;
2. accepted ADRs;
3. the durable governance and architecture documents linked below;
4. the current release/scope ladders and implementation matrix;
5. task-specific instructions.

If two sources conflict, stop, identify the conflict, and apply the stricter
safety/correctness rule until a maintainer resolves it. Historical prompt
numbers are not authority.

## 2. Required navigation

Before changing anything, read:

- [`README.md`](README.md) for public positioning and supported behavior;
- [`docs/README.md`](docs/README.md) for the documentation map;
- [`docs/governance/product-safety.md`](docs/governance/product-safety.md) for
  product, market, data, integration, security, and AI boundaries;
- [`docs/governance/engineering-standards.md`](docs/governance/engineering-standards.md)
  for numerical, configuration, testing, CI, evidence, and repository rules;
- [`docs/governance/research-risk-and-promotion.md`](docs/governance/research-risk-and-promotion.md)
  for backtest, validation, risk, paper/shadow, reporting, alert, incident, and
  promotion requirements;
- [`docs/roadmap/scope-ladder.md`](docs/roadmap/scope-ladder.md) for the maximum
  authorized stage of every domain;
- [`docs/roadmap/release-ladder.md`](docs/roadmap/release-ladder.md) for stable
  stopping points and promotion gates;
- [`docs/status/implementation-matrix.md`](docs/status/implementation-matrix.md)
  for what is actually implemented now;
- [`SECURITY.md`](SECURITY.md) and [`CONTRIBUTING.md`](CONTRIBUTING.md);
- all relevant code, tests, ADRs, and narrower instructions.

The implementation matrix describes reality. The scope ladder describes the
maximum planned envelope. A future stage is not an implemented claim.

## 3. Absolute safety boundaries

Agents MUST NOT:

- add, enable, simulate, or hide `canary` or `live` trading;
- create `make live`, `live.yaml`, live-order endpoints, or production-trading
  aliases;
- request, handle, disclose, or commit real credentials or private account
  data;
- add withdrawal, transfer, sub-account, API-key-management, leverage,
  borrowing, shorting, derivatives, custody, or customer-fund capability;
- call a broker/exchange order API or let strategy code do so;
- let a strategy access credentials, provider clients, risk configuration, or
  mutable audit/evidence stores;
- let an LLM make an authoritative financial calculation, risk decision,
  promotion decision, or order decision;
- label historical, backtest, paper, or shadow results as live performance;
- promise profit or describe a baseline as an investment recommendation;
- infer an unknown provider, market, order, position, account, or reconciliation
  state as success;
- silently fall back to another provider, endpoint, dataset, schema, cost model,
  or market rule;
- delete, rewrite, or hide adverse research, validation, security, incident, or
  audit evidence.

The only supported runtime environments are:

- `research` (default);
- `backtest`;
- `replay`;
- `paper`;
- `shadow` (maximum, read-only account observation only).

Any other value MUST fail validation. Strategy output is limited to `Signal`,
`TargetPosition`, and `TradeProposal`; an independent risk boundary owns any
later accept, adjust, reject, halt, or human-review decision.

## 4. Correctness and reproducibility invariants

Agents MUST preserve:

- `Decimal` or an explicit decimal database type for authoritative money,
  price, quantity, fee, tax, exposure, and balance values;
- timezone-aware UTC internally; naive datetimes are rejected;
- immutable/versioned domain records and deterministic canonical checksums;
- append-only or content-addressed raw data and evidence;
- dataset manifests, lineage, licensing notes, checksums, knowledge time, and
  point-in-time semantics;
- explicit separation of equity and crypto sessions, precision, costs, fills,
  annualization, risk budgets, and corporate-action/stablecoin rules;
- deterministic run manifests binding code, config, data, seed, models,
  environment, result, warnings, and validation failures;
- dirty/incomplete/tampered results being ineligible for qualification;
- fail-closed data-quality, look-ahead, leakage, cost, risk, reconciliation,
  connected-test, and promotion gates;
- conservative execution assumptions, explicit costs, partial/non-fill, and
  no same-close look-ahead fill;
- human approval for every promotion and every credential/provider/license
  decision.

Never edit data, thresholds, models, tolerances, or tests to improve a reported
result. Statistical and floating-point work may use floats only behind an
explicit conversion/tolerance boundary documented in code and tests.

## 5. Progressive scope control

Every change MUST fit the current or explicitly approved next stage in the
scope and release ladders.

Use these rules:

1. implement one working vertical slice;
2. stabilize its contract with tests and evidence;
3. add a second implementation only after the first contract is useful;
4. refine an abstraction only when the two implementations prove the need.

Prefer a modular monolith. Do not add a service, dependency, database,
abstraction, plugin system, provider, workflow, queue, or operator runbook
without a current acceptance criterion and an owner. Stage 0 interface-only
work is allowed only when an immediate consumer is named.

If a request exceeds the current stage:

- implement only the smallest independently useful authorized slice;
- mark the remainder `LATER`, `OPTIONAL`, `BLOCKED`, or `OUT OF SCOPE`;
- do not create placeholders that imply future capability;
- request human approval when the scope ladder names a promotion authority.

## 6. Required task workflow

Before editing, inspect:

1. Git status, branch, base, and existing user changes;
2. relevant documentation and ADRs;
3. relevant source and tests;
4. current implementation and roadmap status;
5. whether the task changes an external, security, data, risk, or release
   boundary.

Before modification, report briefly:

- Objective
- Current repository status
- Assumptions
- Human decisions required
- Files expected to change
- Validation plan
- Risk impact
- Rollback approach

During implementation:

- keep changes small and backward compatible;
- use clear types and validated boundaries;
- avoid global mutable state, hidden I/O, hidden network access, and
  undocumented randomness;
- add tests for new behavior and a regression test for each bug fix;
- add negative tests for safety or risk behavior;
- update affected docs, schema snapshots, manifests, and evidence;
- preserve unrelated worktree changes;
- never fabricate test, market, benchmark, connected, or release evidence.

Do not commit, push, merge, tag, publish, connect credentials, or modify GitHub
state unless the user explicitly authorizes that action. A request to edit or
review the repository is not implicit publication authority.

## 7. Validation requirements

Run the smallest focused tests first, then the broader applicable gates.
Depending on the change, validation includes:

- format and lint;
- strict type checking;
- unit, property, integration, contract, replay, regression, security, and E2E
  tests;
- schema/OpenAPI snapshot validation;
- deterministic checksum/replay validation;
- workflow-permission and secret scans;
- dependency/container scans where dependencies or images changed;
- package/dashboard/container builds where build inputs changed;
- migration and rollback validation where persistence changed.

Default CI and ordinary local validation MUST NOT require provider credentials
or connected network access. Connected tests are separately opted in, bounded,
redacted, never run for untrusted fork code, and report unexecuted work as
`BLOCKED` or `SKIP`, never `PASS`.

Never make CI pass by deleting a test, weakening a risk/data/security gate,
turning an assertion into a log, swallowing an exception, omitting costs, or
adding an unjustified tolerance.

## 8. Completion and handoff

A task is complete only when its scoped behavior, tests, documentation,
evidence, limitations, rollback, and status are internally consistent. A stage
is not promoted by automated checks alone.

After work, report:

- Summary
- Files changed
- Behavior changes
- Architecture decisions
- Risk impact
- Security impact
- Tests executed and exact results
- Evidence generated
- Known limitations
- Rollback plan
- Remaining/deferred work
- Promotion gate result: `PASS`, `FAIL`, or `BLOCKED`

If a test was not run, say so. Do not imply that local success equals connected
qualification, human approval, merge, release, or future profitability.
