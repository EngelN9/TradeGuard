# TradeGuard v0.1.0 Implementation Matrix

Assessment date: `2026-07-29`

Base Git SHA: `65d3c6f8499a189685c7c21e722c8ff6bf498cdb`

Overall status: `BOOTSTRAP / NOT TRADABLE`

Status vocabulary:

- `COMPLETE`: implemented and supported by reviewable evidence.
- `PARTIAL`: some relevant material exists, but acceptance criteria are unmet.
- `MISSING`: no implementation or required artifact exists.
- `BLOCKED`: cannot proceed until a named external/human prerequisite is met.
- `NOT APPLICABLE`: deliberately outside the v0.1.0 contract.

## Repository inventory

At Prompt 0 assessment time the remote `main` tree contained exactly:

- `AGENTS.md`
- `PROMPTS.md`
- `README.md`
- `SECURITY.md`

Prompt 1 on `agent/prompt-1-bootstrap` now adds the typed Python package, locked
Python and dashboard dependencies, tests, local tooling, CI workflow
definitions, container definitions, service skeletons, a dashboard placeholder,
and bootstrap evidence generation. It does not add a strategy, external adapter,
account connection, or order-submission route.

The local checkout initially lacked Git metadata. It was safely reattached to
remote commit `65d3c6f` after all four local blob hashes matched the remote.
Prompt 0 work occurs on `agent/prompt-0-contract`.

## Compliance matrix

| Area | Requirement | Status | Existing evidence | Gap / next issue |
| --- | --- | --- | --- | --- |
| Governance | Highest-level safety specification | COMPLETE | `AGENTS.md` | Keep synchronized |
| Governance | Prompted delivery stages and gates | COMPLETE | `PROMPTS.md` | Execute sequentially |
| Governance | Product positioning and safety boundary | COMPLETE | `README.md`, `SECURITY.md`, runtime policy tests | Keep synchronized |
| Governance | Contribution guide | COMPLETE | `CONTRIBUTING.md` | Maintain with tooling |
| Governance | Public software license | COMPLETE | `LICENSE`, Apache-2.0 approved on 2026-07-29 | Recheck dependency licenses before release |
| Governance | CODEOWNERS | COMPLETE | `CODEOWNERS` | Verify repository team/user resolution after push |
| Governance | Private security contact | COMPLETE | GitHub Private Vulnerability Reporting approved | Verify repository feature before release |
| Release | Connected Release contract | COMPLETE | `docs/release/connected-release-v1.md` | Human approval required |
| Release | Implementation matrix | COMPLETE | This file | Maintain per issue |
| Architecture | System context | COMPLETE | `docs/architecture/system-context.md` | Human review |
| Architecture | Scope ADR | COMPLETE | `docs/adr/0001-connected-release-scope.md` | Accepted 2026-07-29 |
| Bootstrap | Python 3.12 typed package | COMPLETE | `pyproject.toml`, `src/tradeguard/`, package build | Domain implementation begins in TG-002 |
| Bootstrap | `pyproject.toml` and `uv.lock` | COMPLETE | Locked sync succeeded in the working tree and an independent clean clone | Revalidate on Python 3.12 CI |
| Bootstrap | Ruff, mypy, pytest, Hypothesis, coverage | COMPLETE | 39 offline tests pass; 95.86% coverage | Re-run in CI |
| Bootstrap | Pre-commit | COMPLETE | `.pre-commit-config.yaml` with local deterministic hooks | Installation not exercised because GNU Make is unavailable |
| Bootstrap | Required Make targets | COMPLETE | `Makefile`, repository policy tests | GNU Make unavailable locally; direct equivalents passed |
| Bootstrap | Safe opt-in connected test target | COMPLETE | `make test-connected`, safe-skip test | No adapter or credentials used |
| Bootstrap | `.gitignore` and fake `.env.example` | COMPLETE | Files and policy tests | Keep placeholders non-sensitive |
| CI | Format/lint/type/test workflows | COMPLETE | `.github/workflows/ci.yml`, workflow validator | Remote execution pending later push |
| CI | Secret/dependency/container/workflow scans | PARTIAL | Local secret, Python, npm, workflow scans pass; security workflow exists | Container scan cannot run without Docker or remote CI |
| CI | Minimal permissions and SHA-pinned Actions | COMPLETE | Workflow validator passes for two workflows | Recheck pins before release |
| Container | Secure Dockerfile and Compose | PARTIAL | Non-root/read-only definitions and static policy tests pass | Docker unavailable; Compose build/start is unverified |
| Database | PostgreSQL and migrations | PARTIAL | PostgreSQL Compose service exists | Migrations are deferred to TG-015 |
| Health | Liveness and readiness skeleton | COMPLETE | Integration tests and actual localhost probe pass | Container probe pending |
| Evidence | Bootstrap evidence skeleton | COMPLETE | `scripts/collect_evidence.py`, checksum index, evidence documentation | Container metadata remains explicitly unpopulated |
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
| Equity adapter | Provider decision | COMPLETE | Twelve Data approved 2026-07-29 | Terms recheck before TG-004 |
| Equity adapter | Protocol and implementation | BLOCKED | None | TG-004 after decision |
| Equity adapter | Offline/connected/schema-drift tests | BLOCKED | None | TG-004 after decision |
| Crypto adapter | Provider decision | COMPLETE | Coinbase public API approved 2026-07-29 | Terms recheck before TG-005 |
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
| Paper | Deterministic paper broker | PARTIAL | Non-ordering deterministic broker skeleton and negative route test | State machine and fills remain TG-011 |
| Paper | Order state machine/idempotency/recovery | MISSING | None | TG-011 |
| External adapter | Adapter decision | COMPLETE | Coinbase static sandbox approved 2026-07-29 | Static behavior is a known limitation |
| External adapter | Non-live implementation/tests | BLOCKED | None | TG-012 after decision |
| Monitoring | Paper/shadow event ingestion | MISSING | None | TG-013 |
| Reconciliation | Five-state reconciliation | MISSING | None | TG-013 |
| Drift | Required drift and alerts | MISSING | None | TG-013 |
| API | FastAPI resource endpoints | PARTIAL | Root and health skeleton only | Resource APIs remain TG-014 |
| API | Authz/audit/idempotent writes | MISSING | None | TG-014 |
| API | Fixed OpenAPI contract | PARTIAL | Bootstrap OpenAPI contract tests | Versioned resource contract remains TG-014 |
| Dashboard | Required pages and environment labels | PARTIAL | Responsive non-tradable placeholder with environment label | Required operational pages remain TG-014 |
| Dashboard | Unknown/stale/accessibility/E2E tests | MISSING | None | TG-014 |
| Security | Threat model | MISSING | None | TG-015 |
| Security | Structured logs/redaction/correlation | MISSING | None | TG-015 |
| Observability | Metrics and component health | MISSING | None | TG-015 |
| Supply chain | SBOM/inventory/scan reports | MISSING | None | TG-015 |
| Container | Non-root/read-only/minimal/pinned | MISSING | None | TG-015 |
| Database | Least privilege/backup/restore test | MISSING | None | TG-015 |
| Security | Regression suite | MISSING | None | TG-015 |
| Build | Package/container/dashboard/checksums | PARTIAL | Python wheel/sdist, dashboard production build, evidence checksums pass | Container build is unverified |
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

1. Domain events, versioned configuration, data, backtesting, strategies,
   validation, risk, monitoring, and complete API/dashboard functionality remain
   future sequential prompts.
2. An independent clean clone passed locked Python/npm installation, static
   checks, offline tests, and both production builds. Docker, Docker Compose,
   GNU Make, and Bash are unavailable on the local host. Static container policy
   checks pass, but Compose build/start and the strict shell verification script
   cannot be truthfully claimed as executed.
3. Prompt 1 does not permit push. Remote GitHub Actions therefore have not run;
   GitHub CLI authentication for `EngelN9` was also invalid during assessment
   and must be repaired before the later authorized publication stage.
4. No connected qualification can be claimed; no provider, account, or broker
   connection was attempted.
5. The repository remains non-tradable and has no order-submission, withdrawal,
   transfer, canary, or live path.

## Prompt 0 promotion result

`PASS`

The documentation deliverables exist, the required decisions are recorded, and
no connected/trading claim is made. Prompt 1 implementation is authorized.

## Prompt 1 promotion result

`BLOCKED`

Verified locally:

- Ruff format and lint pass.
- mypy passes.
- 39 offline Python tests pass and one connected test is safely deselected.
- Coverage is 95.86%, above the 90% gate.
- Dashboard typecheck, two safety tests, and production build pass.
- Python and production npm dependency audits report no known vulnerabilities.
- Workflow permission/SHA validation and the redacted secret scan pass.
- Python wheel and source distribution build successfully.
- An independent local clone at commit `ae8c0d5` completed locked Python/npm
  installation, Ruff, mypy, 39 offline Python tests, dashboard checks/tests,
  dashboard production build, and Python package build; the temporary clone was
  removed after verification.
- Actual localhost `/health/live` and `/health/ready` probes return healthy
  `research` status.
- Bootstrap evidence and its checksum index are generated.

Minimum unblock:

1. Run `scripts/verify_clean_bootstrap.sh` from a clean clone on a host with
   Git, Python 3.12, uv, Node.js, npm, Bash, Docker, and Docker Compose.
2. Confirm `docker compose up --build -d`, all health probes, and cleanup pass.
3. Attach the container results to the Prompt 1 review before authorizing
   Prompt 2.
