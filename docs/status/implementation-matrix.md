# TradeGuard v0.1.0 Implementation Matrix

Assessment date: `2026-07-31`

Base Git SHA before Prompt 4: `219fce6e75c07c05d3f6e662cac70db397316b3f`

Base Git SHA before Prompt 5: `3e8e3c0`

Overall status: `EQUITY AND CRYPTO ADAPTERS IMPLEMENTED / NOT TRADABLE`

Status vocabulary:

- `COMPLETE`: implemented and supported by reviewable evidence.
- `PARTIAL`: some relevant material exists, but acceptance criteria are unmet.
- `MISSING`: no implementation or required artifact exists.
- `BLOCKED`: cannot proceed until a named external/human prerequisite is met.
- `NOT APPLICABLE`: deliberately outside the v0.1.0 contract.

## Repository inventory

At Prompt 0 assessment time, the remote `main` tree contained four files:
`AGENTS.md`, `README.md`, `SECURITY.md`, and the original monolithic delivery-plan
document. That document has since been superseded by `DELIVERY_PLAN.md`.

Prompt 1 on `agent/prompt-1-bootstrap` now adds the typed Python package, locked
Python and dashboard dependencies, tests, local tooling, CI workflow
definitions, container definitions, service skeletons, a dashboard placeholder,
and bootstrap evidence generation. It does not add a strategy, external adapter,
account connection, or order-submission route.

Prompt 2 on `agent/prompt-2-domain-config` adds immutable domain events,
canonical serialization and checksums, fail-closed schema parsing, layered
configuration with redaction and audit events, reproducible run manifests, and
versioned JSON Schema snapshots. It does not add market-data connectivity,
strategy execution, account access, or order submission.

Prompt 3 on `codex/prompt-3-data-foundation` adds canonical equity and crypto
records, point-in-time reference data, content-addressed raw storage, complete
dataset manifests and lineage, deterministic quality gates, synthetic fixtures,
and an offline data CLI. It does not connect to a real provider or account.

Prompt 4 on `codex/prompt-4-twelve-data-adapter` adds a provider-neutral equity
data protocol, a tightly allowlisted Twelve Data daily-bar adapter, sanitized
synthetic contract fixtures, strict UTC/session normalization, schema-drift and
resilience tests, and an opt-in connected state machine. It adds no broker,
account, order, fallback-provider, real-time, corporate-action, or live
capability. Connected qualification was not attempted.

Prompt 5 on `codex/prompt-5-coinbase-adapter` adds a public-only crypto
protocol, tightly allowlisted Coinbase Advanced Trade REST and WebSocket
adapters, synthetic provider-shaped fixtures, strict metadata and sequence
gates, bounded reconnect/resubscription, controlled shutdown, and opt-in
connected evidence. It adds no credential, user channel, account, order,
transfer, withdrawal, derivatives, leverage, fallback, canary, or live
capability. Connected qualification was not attempted.

## Compliance matrix

| Area | Requirement | Status | Existing evidence | Gap / next issue |
| --- | --- | --- | --- | --- |
| Governance | Highest-level safety specification | COMPLETE | `AGENTS.md` | Keep synchronized |
| Governance | Delivery stages and review gates | COMPLETE | `DELIVERY_PLAN.md` | Execute one current stage at a time |
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
| CI | Secret/dependency/container/workflow scans | COMPLETE | Local secret, Python, npm, and workflow scans pass; container scan workflow is validated; Docker images build locally | Execute pinned Trivy Action after later authorized push |
| CI | Minimal permissions and SHA-pinned Actions | COMPLETE | Workflow validator passes for two workflows | Recheck pins before release |
| Container | Secure Dockerfile and Compose | COMPLETE | Docker Desktop build/start, health probes, non-root/read-only/cap-drop inspection, and cleanup pass | Re-run in remote CI after later authorized push |
| Database | PostgreSQL and migrations | PARTIAL | PostgreSQL Compose service exists | Migrations are deferred to TG-015 |
| Health | Liveness and readiness skeleton | COMPLETE | Integration tests and actual localhost probe pass | Container probe pending |
| Evidence | Bootstrap evidence skeleton | COMPLETE | `scripts/collect_evidence.py`, checksum index, evidence documentation | Container metadata remains explicitly unpopulated |
| Domain | Versioned immutable events | COMPLETE | 23 strict event models, discriminated schema, parser policy | Extend only with reviewed schema migration |
| Domain | Canonical serialization/checksums | COMPLETE | Canonical JSON, SHA-256 event checksum, tamper tests | Preserve snapshot compatibility |
| Domain | UTC and Decimal validation | COMPLETE | UTC normalization, naive-time rejection, binary-float rejection | Data models extend this boundary in TG-003 |
| Config | Allowed environment validation | COMPLETE | Five allowlisted environments and property tests | No canary/live configuration |
| Config | Redaction, effective config, config hash | COMPLETE | Ordered safe-YAML layers, redacted inspection, deterministic hash | Secret providers remain future adapter work |
| Config | Configuration audit event | COMPLETE | Checksummed `ConfigurationChanged` event with before/after hashes | Persistence remains TG-015 |
| Reproducibility | Complete RunManifest | COMPLETE | Immutable manifest, dataset references, clean/dirty qualification gate | Run producers arrive in later prompts |
| Schema | JSON/OpenAPI-compatible domain schemas | COMPLETE | Eight generated JSON Schema snapshots and synthetic examples | Regenerate with `make schemas` |
| Data | Canonical equity and crypto models | COMPLETE | Strict immutable Quote, Trade, OHLCV, session, action, and metadata models | Connected provider normalization remains TG-004/TG-005 |
| Data | Instrument point-in-time metadata | COMPLETE | Effective-time and knowledge-time validation with market-specific identity | Provider histories remain TG-004/TG-005 |
| Data | Dataset manifest and lineage | COMPLETE | Checksummed partitions, corrections, parents, and acyclic transformation graph | Persistent catalog remains later work |
| Data | Append-only/content-addressed raw storage | COMPLETE | Write-once SHA-256 store with idempotency and tamper tests | Backup/retention remains TG-015 |
| Data | Shared quality gates | COMPLETE | Ten shared checks plus manifest row-count/checksum binding | Provider calibration remains TG-004/TG-005 |
| Data | Equity-specific quality gates | COMPLETE | Sessions, half days, corporate actions, splits, delisting, PIT universe | Real calendar/action feeds remain TG-004 |
| Data | Crypto-specific quality gates | COMPLETE | 24/7 gaps, precision, notional, maintenance, quote/spread/asset checks | Real venue semantics remain TG-005 |
| Data | Quarantine enforcement | COMPLETE | FAIL/QUARANTINED reports cannot enter validation evidence | Persistence and operator workflow remain later work |
| Data | Synthetic fixtures and CLI | COMPLETE | Eleven committed fixtures; validate/manifest/inspect commands; evidence bundle | No external data is claimed |
| Equity adapter | Provider decision | COMPLETE | ADR 0002, approved with conditions 2026-07-31 | Recheck terms and account entitlement before each connected RC |
| Equity adapter | Protocol and implementation | COMPLETE | Provider-neutral protocol; exact host/path/symbol/MIC allowlists; UTC/session mapping | Corporate actions and fallback remain disabled |
| Equity adapter | Offline/schema-drift tests | COMPLETE | 10 adapter contracts; status/error/redaction/calendar/quality tests | Preserve sanitized-only fixture policy |
| Equity adapter | Connected smoke | BLOCKED | `SKIP_NOT_OPTED_IN`, `provider_contacted=false` | Exact plan/account/license/display rights, reviewed sessions, credential, and one RC observation |
| Crypto adapter | Provider decision | COMPLETE | ADR 0003; Coinbase public API approved with conditions | Recheck terms and jurisdiction before each connected RC |
| Crypto adapter | REST/WebSocket implementation | COMPLETE | Public-only BTC-USD adapter; exact REST/WS allowlists; Decimal/UTC manifests | Expansion requires review |
| Crypto adapter | Reconnect/sequence/connected tests | COMPLETE | Offline contract/replay tests; redacted connected `SKIP_NOT_OPTED_IN` | Connected PASS and human promotion review remain blocked |
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
| Build | Package/container/dashboard/checksums | COMPLETE | Python wheel/sdist, dashboard production build, Docker images, and evidence checksums pass | Release artifact signing remains TG-015/TG-018 |
| Qualification | Two clean environments | MISSING | None | TG-016 |
| Qualification | Offline full matrix | MISSING | None | TG-016 |
| Qualification | Connected equity E2E | BLOCKED | Adapter exists; connected result is `SKIP_NOT_OPTED_IN` | TG-017 |
| Qualification | Connected crypto E2E | BLOCKED | Adapter exists; connected result is `SKIP_NOT_OPTED_IN` | TG-017 |
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

1. External non-live adapter, backtesting, strategies, validation,
   risk, monitoring, and complete API/dashboard functionality remain future
   sequential prompts.
2. Prompt 1 through Prompt 4 are published on the draft implementation pull
   request, where all configured GitHub checks passed. Prompt 5 remains a
   stacked implementation change until its own verification and publication.
3. No connected qualification can be claimed; both Twelve Data and Coinbase
   results are `SKIP_NOT_OPTED_IN`, no provider/account/broker connection was
   attempted, and ADR 0002/0003 promotion blockers remain unresolved.
4. The repository remains non-tradable and has no order-submission, withdrawal,
   transfer, canary, or live path.

## Prompt 0 promotion result

`PASS`

The documentation deliverables exist, the required decisions are recorded, and
no connected/trading claim is made. Prompt 1 implementation is authorized.

## Prompt 1 promotion result

`PASS`

Verified locally:

- Ruff format and lint pass.
- mypy passes.
- 40 offline Python tests pass and one connected test is safely deselected.
- Coverage is 95.86%, above the 90% gate.
- Dashboard typecheck, two safety tests, and production build pass.
- Python and production npm dependency audits report no known vulnerabilities.
- Workflow permission/SHA validation and the redacted secret scan pass.
- Python wheel and source distribution build successfully.
- An independent local clone at commit `ae8c0d5` completed locked Python/npm
  installation, Ruff, mypy, 39 offline Python tests, dashboard checks/tests,
  dashboard production build, and Python package build; the temporary clone was
  removed after verification.
- `scripts/verify_clean_bootstrap.sh` was invoked with Git Bash and returned its
  final `PASS: clean bootstrap verified` result.
- Docker Compose built and started PostgreSQL, API, worker, mock market data,
  deterministic paper broker skeleton, and dashboard. All probes passed.
- Application containers were verified read-only, non-root, capability-dropped,
  and configured with `no-new-privileges`.
- Paper broker capabilities remained non-external and non-live; its order route
  returned HTTP 404.
- Verification removed its containers, network, and volume. The pre-existing
  `freqtrade` container remained running and unchanged.
- Actual localhost `/health/live` and `/health/ready` probes return healthy
  `research` status.
- Bootstrap evidence and its checksum index are generated.

Prompt 2 was authorized by the maintainer on 2026-07-29.

## Prompt 2 promotion result

`PASS`

Verified locally:

- Ruff format and lint pass.
- mypy strict mode passes for 26 source files.
- 74 offline Python tests pass and one connected test is safely deselected.
- Coverage is 96.30%, above the 90% gate.
- All 23 required event types share a strict immutable envelope and generated
  discriminated JSON Schema.
- Canonical JSON and SHA-256 checksums are deterministic; binary floats,
  naive datetimes, tampered events, and unregistered schema versions fail
  closed.
- All five allowed environments load successfully; unallowlisted environments
  fail property-based validation.
- Effective configuration inspection is redacted, configuration hashes are
  credential-independent, and no secret value appears in schema snapshots or
  generated evidence.
- Clean run manifests qualify deterministically; dirty worktrees and validation
  failures are recorded and rejected for release qualification.
- Domain event, configuration, and run-manifest schemas reproduce exactly from
  `scripts/export_schemas.py`; the synthetic sample manifest validates.
- Workflow permission/SHA validation, the redacted secret scan, and repository
  diff checks pass.
- The Python dependency audit reports no known vulnerabilities, and the wheel
  and source distribution build successfully.
- No external provider, account, credential, strategy, adapter, order route,
  canary environment, or live-trading capability was added or exercised.

Prompt 3 was authorized by the maintainer on 2026-07-29.

## Prompt 3 promotion result

`PASS`

Verified locally:

- Ruff format and lint pass.
- mypy strict mode passes for 35 source files.
- 128 offline Python tests pass and one connected test is safely deselected.
- Coverage is 94.26%, above the 90% gate.
- All required canonical records and point-in-time metadata use immutable,
  strict UTC/Decimal contracts.
- Dataset manifests bind sorted symbols, date ranges, row counts, partitions,
  licensing, gaps, corrections, parent identity, checksums, and an acyclic
  transformation graph.
- Content-addressed raw storage is write-once through its API, idempotent for
  identical bytes, and detects altered blobs.
- Every required shared, equity, and crypto quality code is implemented.
- Quality evaluation validates record count and checksum against the manifest;
  unknown or future-known reference data fails closed.
- `FAIL` and `QUARANTINED` reports cannot support validation evidence.
- Eleven committed synthetic fixtures reproduce exact manifests and reports,
  including stale-content-with-fresh-ingest and quarantined examples.
- `tradeguard data validate`, `manifest`, and `inspect` operate offline and
  return non-zero status for unsafe inputs.
- JSON Schema snapshots, fixture manifests, quality reports, transformed data
  checksums, lineage graphs, and evidence checksums regenerate deterministically.
- No external provider, account, credential, strategy, adapter, order route,
  canary environment, or live-trading capability was added or exercised.

Prompt 4 was authorized by the maintainer through the 2026-07-31 provider review.

## Prompt 4 implementation result

`IMPLEMENTED / PROMOTION BLOCKED`

Verified locally:

- The provider-neutral equity protocol covers reviewed metadata, historical
  bars, latest completed bar, calendar, timezone, symbol normalization, and
  explicit unsupported corporate actions.
- The Twelve Data client permits only HTTPS GET to
  `api.twelvedata.com/time_series`, sends credentials only by authorization
  header, limits responses to 1 MiB, times out after 10 seconds, and retries
  exactly once only after HTTP 429.
- Only AAPL, NASDAQ, XNAS/XNGS, `1day`, `outputsize <= 10`, and `adjust=none`
  pass the adapter scope boundary.
- Strict provider schema, Decimal parsing, exchange-local session-date mapping,
  reviewed UTC sessions, manifest/checksum creation, and the Prompt 3 quality
  gate pass the sanitized contract.
- Corporate actions remain unsupported; unadjusted data carries a warning and
  suspected unmodeled discontinuities are quarantined without an inferred split.
- Eleven focused adapter contract tests pass. The complete offline suite has
  159 passing tests, one connected test deselected, and 93.02% branch-aware
  coverage.
- Ruff, strict mypy, schema snapshot reproduction, workflow validation, secret
  scan, dashboard checks/tests/build, and package build pass.
- Prompt 4 changes no dependency or lock entry. System-CA-enabled Python and
  production npm audits report no known dependency vulnerabilities; the local
  unpublished `tradeguard` package is correctly skipped by the PyPI audit.
- Public Prompt 4 evidence contains only sanitized synthetic fixtures, schemas,
  counts, dates, checksums, manifests, quality status, and licensing metadata.
  It records `raw_market_values_persisted=false` and
  `raw_market_values_published=false`.
- Connected evidence is `SKIP_NOT_OPTED_IN`, `passed=false`, and
  `provider_contacted=false`.

The Basic plan, individual account, approved internal non-display use,
internal-use-only classification, 8/800 credit metadata, no redistribution,
no public display, and transient-only raw-response policy are now recorded.
Promotion remains `BLOCKED` until the exact connected-session window is human
approved, a locally opted-in release-candidate connected smoke obtains `PASS`,
the redacted evidence is human reviewed, and promotion is explicitly approved.

Prompt 5 was authorized by the maintainer after Prompt 4 publication.

## Prompt 5 implementation result

`IMPLEMENTED / PROMOTION BLOCKED`

Verified locally:

- The provider-neutral crypto protocol covers trading-pair metadata, supported
  pairs, one-minute bars, public trades, best bid/ask, REST health, public
  WebSocket, venue maintenance status, and rate-limit metadata.
- REST allows only unauthenticated HTTPS GET to four exact
  `api.coinbase.com/api/v3/brokerage` public paths. Authorization, cookies,
  private paths, duplicate queries, responses over 1 MiB, and more than one
  429 retry fail closed.
- WebSocket allows only `advanced-trade-ws.coinbase.com` with public
  `heartbeats`, `market_trades`, `status`, and `ticker` subscriptions. No
  subscription contains a JWT.
- Only BTC-USD spot is enabled. Decimal precision, minimum quantity/notional,
  UTC timestamps, REST/WebSocket metadata agreement, and provider status are
  validated before a stream can become research-admissible.
- Missing, duplicate, skipped, and decreasing sequences; heartbeat gaps; stale
  messages; future timestamps; schema drift; metadata conflict; and reconnect
  exhaustion emit quarantined `DataQualityAlert` events and remain
  `NOT_TRADABLE`. Missing events are never inferred.
- Disconnect replay proves a one-second bounded backoff, full
  resubscription, and controlled closure. The complete schedule is one, two,
  then four seconds with at most three reconnects.
- Five focused Coinbase REST contracts and nine WebSocket replay tests pass.
  The complete offline suite has 189 passing tests, two connected tests
  deselected, and 90.18% branch-aware coverage.
- Ruff format/lint, strict mypy, schema reproduction, workflow validation,
  secret scan, dashboard typecheck/tests/build, and Python package build pass.
- Python and production npm audits report no known vulnerabilities; the local
  unpublished `tradeguard` package is correctly skipped by the PyPI audit.
- Public Prompt 5 artifacts contain deterministic synthetic fixtures,
  checksums, counts, manifests, status, and test output only. They record no
  raw connected values, account data, credential, order, transfer, withdrawal,
  fallback, derivatives, leverage, canary, or live capability.
- Connected evidence is `SKIP_NOT_OPTED_IN`, `passed=false`, and
  `provider_contacted=false`.

Promotion remains `BLOCKED` until the Coinbase terms and jurisdiction are
rechecked for the intended release-candidate use, an explicitly opted-in
public REST/WebSocket smoke obtains `PASS`, the redacted evidence is human
reviewed, and promotion is explicitly approved.
