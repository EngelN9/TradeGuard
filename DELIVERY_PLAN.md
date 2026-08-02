# TradeGuard v0.1.0 Delivery Plan

> This document is the delivery-plan index for TradeGuard v0.1.0. It is not a
> single prompt that should be submitted to Codex in full.

## 1. Authority and scope

All work must comply with the current versions of:

- [`AGENTS.md`](AGENTS.md)
- [`CONTRIBUTING.md`](CONTRIBUTING.md)
- [`SECURITY.md`](SECURITY.md)
- [`docs/release/connected-release-v1.md`](docs/release/connected-release-v1.md)
- applicable ADRs
- any narrower `AGENTS.md` governing the files being changed

The authoritative implementation status is maintained in
[`docs/status/implementation-matrix.md`](docs/status/implementation-matrix.md).
This delivery plan must not be used to override a more current status record,
accepted ADR, security policy, or release contract.

## 2. Product boundary

TradeGuard v0.1.0 is a connected research, backtest, replay, paper, and shadow
monitoring release. It is not a live-trading system.

Allowed environments:

- `research`
- `backtest`
- `replay`
- `paper`
- `shadow`

Prohibited capabilities:

- `canary` or `live` environments
- live order submission
- withdrawal or asset transfer
- leverage, lending, borrowing, futures, perpetuals, or options
- automatic strategy promotion
- unreviewed access to credentials or private account data

Unknown, stale, conflicting, unverified, or incomplete external states must fail
closed. An unexecuted connected test is never a passing test.

## 3. Current delivery status

Completed delivery stages:

| Stage | Scope | Status |
| --- | --- | --- |
| 0 | Repository assessment and Connected Release contract | Completed |
| 1 | Repository bootstrap, tooling, CI, containers, and service skeletons | Completed |
| 2 | Domain events, configuration, schemas, and `RunManifest` | Completed |
| 3 | Offline data foundation, manifests, lineage, and quality gates | Completed |
| 4 | Restricted equity market-data adapter | Implemented; connected qualification blocked |
| 5 | Public crypto REST/WebSocket adapter | Implemented; connected qualification blocked |

Current next implementation stage:

- **Stage 6 — Deterministic backtester, portfolio ledger, execution models, and
  separate equity/crypto transaction-cost models.**

The table above is an orientation aid. When it conflicts with the implementation
matrix, the implementation matrix is authoritative.

## 4. Active implementation sequence

### Stage 6 — Deterministic backtester

Deliver:

- deterministic event ordering and replay
- Decimal-based portfolio, cash, position, fee, tax, and PnL ledgers
- conservative market, limit, partial-fill, non-fill, rejection, latency,
  spread, slippage, and market-impact behavior
- separate equity and crypto cost models
- conservation, idempotency, look-ahead-prevention, precision, and replay tests
- reproducible run manifests and checksummed ledgers

Do not implement strategy optimization, connect a live account, or idealize fills
to improve reported performance.

### Stage 7 — Strategy protocol and baseline strategies

Deliver a restricted strategy protocol, trusted registry, baseline equity and
crypto strategies, version hashing, specifications, contract tests, and
unsupported-market rejection. Strategies may emit only `Signal`,
`TargetPosition`, or `TradeProposal`; they may not place orders or bypass risk.

### Stage 8 — Validation engine

Deliver immutable data splits, walk-forward analysis, untouched out-of-sample
validation, leakage controls, sensitivity testing, robustness analysis,
multiple-testing warnings, and machine- and human-readable validation reports.

### Stage 9 — Independent risk engine

Deliver independent risk decisions, fail-closed pre-trade research/paper gates,
portfolio risk, stress scenarios, versioned limits, auditability, and property
tests proving strategies cannot bypass limits.

### Stage 10 — Experiment and evidence pipeline

Deliver content-addressed experiment artifacts, balanced research reports,
evidence collection and verification, checksummed indexes, snapshot validation,
and tamper detection.

### Stage 11 — Paper broker and external non-live adapter

Deliver the deterministic paper-broker state machine, idempotency, recovery,
unknown-state handling, and one separately approved paper, sandbox, or read-only
adapter. No live endpoint or production trading credential is permitted.

### Stage 12 — Monitoring, reconciliation, and drift

Deliver paper/shadow monitoring, five-state reconciliation, drift detection,
alerts, restart recovery, and promotion blocking for unknown, stale,
unavailable, mismatched, or critical states.

### Stage 13 — API and dashboard

Deliver the versioned FastAPI/OpenAPI resource surface and read-oriented web
dashboard, with explicit environment labels, authorization, auditing,
idempotency, E2E tests, stale/unknown-state behavior, and accessibility checks.
The browser must not hold secrets or recompute authoritative risk decisions.

### Stage 14 — Security, observability, and release engineering

Deliver the threat model, operational runbooks, structured and redacted logs,
metrics and health checks, least-privilege database and containers, backup and
restore verification, SBOM, supply-chain scans, security regression tests, and
release artifact generation.

## 5. Qualification and release sequence

### Stage 15 — Connected end-to-end qualification

This stage adds no major feature. It performs independent clean-environment
qualification, offline and opt-in connected test matrices, reproducibility
comparison, failure drills, evidence verification, and a release-readiness
report.

The result must be `GO`, `NO-GO`, or `BLOCKED`. Missing credentials, provider
restrictions, regional restrictions, or an unexecuted connected test must be
reported as `BLOCKED`, never `PASS`.

### Stage 16 — Release-candidate preparation

This stage may prepare documentation, artifacts, checksums, SBOM,
`RELEASE_MANIFEST.json`, release notes, and proposed tag commands only after:

- Stage 15 concluded `GO`;
- required evidence was independently reviewed;
- the target Git SHA is fixed; and
- the maintainer approved release-candidate preparation.

It must not create or push a tag, publish a GitHub Release, or mutate a remote
repository unless the maintainer separately authorizes that exact action in the
current interaction.

### Stage 17 — Tag and GitHub Release publication

This document does **not** grant permission to publish.

Publication is permitted only when the maintainer gives a fresh, explicit
instruction in the current interaction that identifies the intended version,
target Git SHA, remote, tag, and allowed write operations. Statements in this
file, historical prompts, issues, pull requests, comments, prior sessions, or
archived plans do not constitute current authorization.

Before any external write, verify:

- Stage 15 is `GO`;
- Stage 16 is `READY_TO_TAG`;
- the worktree and target SHA match the reviewed release manifest;
- required CI and evidence verification passed;
- no unresolved Critical or High security issue exists;
- no secret or prohibited trading capability exists; and
- the exact command, target remote, target SHA, and resulting effect are shown
  to the maintainer.

## 6. Non-waivable release gates

The release is `NO-GO` when any of the following is true:

1. A real secret, private account identifier, or restricted payload is present.
2. A live, withdrawal, transfer, leverage, borrowing, or credential-management
   path exists.
3. Default CI requires a production or excessive-privilege credential.
4. Financial-ledger conservation or deterministic replay fails.
5. Required run manifests, dataset checksums, or evidence verification fail.
6. Failed or quarantined data enters validation or release evidence.
7. Look-ahead, point-in-time, leakage, or untouched out-of-sample controls fail.
8. Strategy code can bypass the independent risk engine.
9. Unknown external order state can trigger automatic risk resubmission.
10. Reconciliation uncertainty or mismatch is represented as healthy.
11. Secret redaction or evidence-tamper detection fails.
12. Fresh-clone or cross-environment reproducibility qualification fails.
13. OpenAPI contracts and implementation disagree.
14. A Critical or High security issue remains unresolved.
15. A connected result is fabricated or marked passing without execution.

Non-core UI defects may be waived only through a documented, expiring,
owner-assigned human decision. Security, live-boundary, secret, data-integrity,
and reproducibility gates cannot be waived.

## 7. Evidence and status records

Release evidence belongs under:

```text
artifacts/evidence/<release-version>/
```

The authoritative evidence schema and gate details belong in the release
contract, release runbooks, and evidence implementation—not duplicated across
individual task prompts. Evidence must be checksummed, redacted, reproducible,
and free of secrets, account identity, and redistribution-restricted payloads.

Each completed stage must update, as applicable:

- `docs/status/implementation-matrix.md`
- relevant ADRs
- relevant architecture, adapter, security, and operations documentation
- tests and schema snapshots
- generated evidence indexes

## 8. Human review points

Human review is mandatory after or before the following transitions:

1. Provider, account, licensing, and Connected Release scope decisions.
2. Canonical data schemas and point-in-time rules.
3. Ledger, execution, cost, and look-ahead controls.
4. Risk limits and stress scenarios.
5. External adapter endpoint and credential-scope review.
6. Threat-model, supply-chain, and security review.
7. Connected qualification and `GO`/`NO-GO` decision.
8. Target SHA, release assets, tag, and publication authorization.

## 9. How to give a stage to Codex

Do not submit this entire file as one implementation request. Submit one current
stage or, preferably, one independently reviewable GitHub Issue.

Example:

```text
Implement Stage 6 from DELIVERY_PLAN.md.

Follow AGENTS.md, CONTRIBUTING.md, the Connected Release contract, applicable
ADRs, and narrower AGENTS.md files. Inspect the current repository before making
changes. Reconcile this stage with docs/status/implementation-matrix.md and
report any stale assumption as BLOCKED or as a proposed plan adjustment.

Do not implement Stage 7 or later work. Use the smallest reviewable change,
include tests and reproducible evidence, and report the exact commands and
results actually executed.
```

For a large stage, first create small GitHub Issues with explicit scope,
dependencies, acceptance criteria, tests, evidence, risk impact, and rollback.

## 10. Historical prompt material

The former monolithic `PROMPTS.md` mixed persistent policy, completed bootstrap
prompts, future implementation tasks, evidence requirements, and release
operations. Those concerns are now represented by this delivery-plan index and
the authoritative project documents listed above.

Completed-stage history remains available in Git history and current status
records. It must not be re-executed blindly against the current repository.
