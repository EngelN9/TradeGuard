# TradeGuard v0.1.0 Implementation Matrix

Assessment date: `2026-07-29`

Base Git SHA: `65d3c6f8499a189685c7c21e722c8ff6bf498cdb`

Overall status: `PLANNING / NOT TRADABLE`

Status vocabulary:

- `COMPLETE`: implemented and supported by reviewable evidence.
- `PARTIAL`: some relevant material exists, but acceptance criteria are unmet.
- `MISSING`: no implementation or required artifact exists.
- `BLOCKED`: cannot proceed until a named external/human prerequisite is met.
- `NOT APPLICABLE`: deliberately outside the v0.1.0 contract.

## Repository inventory

At assessment time the remote `main` tree contains exactly:

- `AGENTS.md`
- `PROMPTS.md`
- `README.md`
- `SECURITY.md`

There is no application code, dependency manifest, lockfile, test, CI workflow,
container definition, configuration, schema, database migration, API, dashboard,
adapter, artifact, or release evidence. `CONTRIBUTING.md`, `LICENSE`, and
`CODEOWNERS` are also absent.

The local checkout initially lacked Git metadata. It was safely reattached to
remote commit `65d3c6f` after all four local blob hashes matched the remote.
Prompt 0 work occurs on `agent/prompt-0-contract`.

## Compliance matrix

| Area | Requirement | Status | Existing evidence | Gap / next issue |
| --- | --- | --- | --- | --- |
| Governance | Highest-level safety specification | COMPLETE | `AGENTS.md` | Keep synchronized |
| Governance | Prompted delivery stages and gates | COMPLETE | `PROMPTS.md` | Execute sequentially |
| Governance | Product positioning and safety boundary | PARTIAL | `README.md`, `SECURITY.md` | Update as implementation becomes real |
| Governance | Contribution guide | MISSING | None | TG-001 |
| Governance | Public software license | BLOCKED | None | Maintainer selects license before bootstrap approval |
| Governance | CODEOWNERS | MISSING | None | TG-001 |
| Governance | Private security contact | BLOCKED | Placeholder in `SECURITY.md` | Maintainer supplies monitored address/channel |
| Release | Connected Release contract | COMPLETE | `docs/release/connected-release-v1.md` | Human approval required |
| Release | Implementation matrix | COMPLETE | This file | Maintain per issue |
| Architecture | System context | COMPLETE | `docs/architecture/system-context.md` | Human review |
| Architecture | Scope ADR | COMPLETE | `docs/adr/0001-connected-release-scope.md` | Status remains Proposed |
| Bootstrap | Python 3.12 typed package | MISSING | None | TG-001 |
| Bootstrap | `pyproject.toml` and `uv.lock` | MISSING | None | TG-001 |
| Bootstrap | Ruff, mypy, pytest, Hypothesis, coverage | MISSING | None | TG-001 |
| Bootstrap | Pre-commit | MISSING | None | TG-001 |
| Bootstrap | Required Make targets | MISSING | None | TG-001 |
| Bootstrap | Safe opt-in connected test target | MISSING | None | TG-001 |
| Bootstrap | `.gitignore` and fake `.env.example` | MISSING | None | TG-001 |
| CI | Format/lint/type/test workflows | MISSING | None | TG-001 |
| CI | Secret/dependency/container/workflow scans | MISSING | None | TG-001/TG-015 |
| CI | Minimal permissions and SHA-pinned Actions | MISSING | None | TG-001 |
| Container | Secure Dockerfile and Compose | MISSING | None | TG-001/TG-015 |
| Database | PostgreSQL and migrations | MISSING | None | TG-001/TG-015 |
| Health | Liveness and readiness skeleton | MISSING | None | TG-001 |
| Evidence | Bootstrap evidence skeleton | MISSING | None | TG-001 |
| Domain | Versioned immutable events | MISSING | None | TG-002 |
| Domain | Canonical serialization/checksums | MISSING | None | TG-002 |
| Domain | UTC and Decimal validation | MISSING | None | TG-002 |
| Config | Allowed environment validation | MISSING | None | TG-002 |
| Config | Redaction, effective config, config hash | MISSING | None | TG-002 |
| Config | Configuration audit event | MISSING | None | TG-002 |
| Reproducibility | Complete RunManifest | MISSING | None | TG-002 |
| Schema | JSON/OpenAPI-compatible domain schemas | MISSING | None | TG-002 |
| Data | Canonical equity and crypto models | MISSING | None | TG-003 |
| Data | Instrument point-in-time metadata | MISSING | None | TG-003 |
| Data | Dataset manifest and lineage | MISSING | None | TG-003 |
| Data | Append-only/content-addressed raw storage | MISSING | None | TG-003 |
| Data | Shared quality gates | MISSING | None | TG-003 |
| Data | Equity-specific quality gates | MISSING | None | TG-003 |
| Data | Crypto-specific quality gates | MISSING | None | TG-003 |
| Data | Quarantine enforcement | MISSING | None | TG-003 |
| Data | Synthetic fixtures and CLI | MISSING | None | TG-003 |
| Equity adapter | Provider decision | BLOCKED | Candidate matrix only | Human decision after Prompt 0 |
| Equity adapter | Protocol and implementation | BLOCKED | None | TG-004 after decision |
| Equity adapter | Offline/connected/schema-drift tests | BLOCKED | None | TG-004 after decision |
| Crypto adapter | Provider decision | BLOCKED | Candidate matrix only | Human decision after Prompt 0 |
| Crypto adapter | REST/WebSocket implementation | BLOCKED | None | TG-005 after decision |
| Crypto adapter | Reconnect/sequence/connected tests | BLOCKED | None | TG-005 after decision |
| Backtest | Deterministic event loop | MISSING | None | TG-006 |
| Backtest | Decimal portfolio ledger | MISSING | None | TG-006 |
| Backtest | Conservative execution models | MISSING | None | TG-006 |
| Backtest | Separate equity/crypto costs | MISSING | None | TG-006 |
| Backtest | Conservation/look-ahead/replay tests | MISSING | None | TG-006 |
| Strategy | Restricted protocol and registry | MISSING | None | TG-007 |
| Strategy | Equity baseline strategies | MISSING | None | TG-007 |
| Strategy | Crypto baseline strategies | MISSING | None | TG-007 |
| Strategy | Specifications/contracts/version hashes | MISSING | None | TG-007 |
| Validation | Immutable dataset splits | MISSING | None | TG-008 |
| Validation | Walk-forward | MISSING | None | TG-008 |
| Validation | Leakage/overfitting controls | MISSING | None | TG-008 |
| Validation | Sensitivity and regime analysis | MISSING | None | TG-008 |
| Validation | Bootstrap/multiple testing | MISSING | None | TG-008 |
| Risk | Independent decision engine | MISSING | None | TG-009 |
| Risk | Pre-trade research/paper gates | MISSING | None | TG-009 |
| Risk | Portfolio risk and stress scenarios | MISSING | None | TG-009 |
| Risk | Fail-closed property tests | MISSING | None | TG-009 |
| Experiments | Experiment model/store | MISSING | None | TG-010 |
| Reports | Complete balanced research report | MISSING | None | TG-010 |
| Evidence | Collect/verify/index and tamper detection | MISSING | None | TG-010 |
| Paper | Deterministic paper broker | MISSING | None | TG-011 |
| Paper | Order state machine/idempotency/recovery | MISSING | None | TG-011 |
| External adapter | Adapter decision | BLOCKED | Candidate matrix only | Human decision after Prompt 0 |
| External adapter | Non-live implementation/tests | BLOCKED | None | TG-012 after decision |
| Monitoring | Paper/shadow event ingestion | MISSING | None | TG-013 |
| Reconciliation | Five-state reconciliation | MISSING | None | TG-013 |
| Drift | Required drift and alerts | MISSING | None | TG-013 |
| API | FastAPI resource endpoints | MISSING | None | TG-014 |
| API | Authz/audit/idempotent writes | MISSING | None | TG-014 |
| API | Fixed OpenAPI contract | MISSING | None | TG-014 |
| Dashboard | Required pages and environment labels | MISSING | None | TG-014 |
| Dashboard | Unknown/stale/accessibility/E2E tests | MISSING | None | TG-014 |
| Security | Threat model | MISSING | None | TG-015 |
| Security | Structured logs/redaction/correlation | MISSING | None | TG-015 |
| Observability | Metrics and component health | MISSING | None | TG-015 |
| Supply chain | SBOM/inventory/scan reports | MISSING | None | TG-015 |
| Container | Non-root/read-only/minimal/pinned | MISSING | None | TG-015 |
| Database | Least privilege/backup/restore test | MISSING | None | TG-015 |
| Security | Regression suite | MISSING | None | TG-015 |
| Build | Package/container/dashboard/checksums | MISSING | None | TG-015 |
| Qualification | Two clean environments | MISSING | None | TG-016 |
| Qualification | Offline full matrix | MISSING | None | TG-016 |
| Qualification | Connected equity E2E | BLOCKED | No approved adapter | TG-017 |
| Qualification | Connected crypto E2E | BLOCKED | No approved adapter | TG-017 |
| Qualification | External non-live smoke | BLOCKED | No approved adapter/credential | TG-017 |
| Qualification | Failure drills | MISSING | None | TG-016/TG-017 |
| Release | v0.1.0 readiness report | MISSING | None | TG-017 |
| Release | Candidate manifest/artifacts | BLOCKED | Requires Prompt 15 GO | TG-018 |
| Release | Tag and GitHub Release | BLOCKED | Requires Prompt 16 READY_TO_TAG and explicit authorization | TG-019 |
| Prohibited | Canary environment | NOT APPLICABLE | Explicitly prohibited | Must remain absent |
| Prohibited | Live trading | NOT APPLICABLE | Explicitly prohibited | Must remain absent |
| Prohibited | Withdrawal/transfer | NOT APPLICABLE | Explicitly prohibited | Must remain absent |
| Prohibited | Arbitrary untrusted strategy sandbox | NOT APPLICABLE | Explicitly out of v0.1.0 | Trusted local code only |

## Critical gaps

1. The repository has no executable or testable implementation.
2. There is no dependency lock, CI, security scanning, or release evidence.
3. Provider, external non-live adapter, license, and security-contact decisions
   are unapproved.
4. No connected or offline qualification can yet be claimed.
5. GitHub CLI authentication for `EngelN9` was invalid during assessment; this
   blocks future push/PR/release work until the maintainer reauthenticates.

## Prompt 0 promotion result

`BLOCKED — HUMAN REVIEW REQUIRED`

The documentation deliverables exist, and no connected/trading claim is made.
Promotion to Prompt 1 requires the decisions listed in
`docs/release/connected-release-v1.md` Section 18.
