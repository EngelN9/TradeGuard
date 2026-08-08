# Progressive scope ladder

Status: `NORMATIVE ROADMAP`

This document caps how far each TradeGuard domain may expand. It is not a claim
that every listed stage will be built. Each completed stage is a minimum usable,
testable, stoppable, maintainable product boundary.

## 1. Rules that apply to every stage cell

The domain matrix below supplies the exact capability cap for each stage. Every
cell also inherits the following entry, exit, evidence, failure, rollback,
stopping, complexity, maintenance, and promotion rules.

| Stage | Entry gate | Exit criteria and evidence | Failure and rollback | Valid stop and maintenance | Default budget | Promotion authority |
| --- | --- | --- | --- | --- | --- | --- |
| Stage 0 — interface only | A named Stage 1 consumer exists in the active release stop; otherwise do not scaffold | Versioned typed contract, negative boundary tests, schema snapshot if serialized, zero implicit I/O | Delete unused interface or restore prior schema; no data migration or runtime side effect | May remain indefinitely as a reviewed contract but must not be advertised as working capability | `B0` | Code owner; security/data/risk reviewer if boundary-sensitive |
| Stage 1 — minimum viable capability | Stage 0 passes when useful; one named user/vertical slice; no unresolved blocker | One working implementation, focused unit/property/contract tests, deterministic sample/evidence, documented limitations and rollback | Fail closed; disable the single implementation and retain evidence | First preferred long-term stop; owner maintains dependency, fixtures, docs, and regression tests | `B1` | Maintainer plus named domain reviewer |
| Stage 2 — limited research quality | Stage 1 is used and stable; second capability has a concrete acceptance need | Stable contract, a second implementation/use case only where needed, integration/replay evidence, backward compatibility, runbook for external state | Disable new slice, preserve Stage 1 contract/data, invalidate affected evidence | Second preferred long-term stop; no obligation to advance | `B2` | Maintainer; human security/license/risk review where applicable |
| Stage 3 — extended conditional | Stage 2 limitation is demonstrated; accepted ADR; maintenance and rollback owners named | ADR acceptance, migration/recovery evidence, stress/security tests, operational metrics, documented total complexity | Feature flag/adapter disable plus tested data/config rollback; incident review for safety failure | Conditional stop only while owner, monitoring, and upstream terms remain current | `B3` | Maintainer and specialist reviewer; two-person approval for accounts, writes, auth, or promotion |
| Stage 4 — advanced optional | Separate RFC proves value exceeds lifetime cost; Stage 3 is healthy | RFC-specific tests, capacity/security model, benchmark against simpler stage, decommission plan | Remove optional subsystem without breaking Stage 2/3; preserve audit evidence | Optional; never a prerequisite for the first connected research release | `B4` | Explicit maintainer RFC approval; independent review for high-risk surfaces |
| Stage 5 — explicitly out of scope | No entry gate exists | Rejection tests/policy checks keep the capability absent | Treat discovery as a defect/incident; disable and revert immediately | Permanent stop: capability remains absent | `B5` (zero implementation) | Only a future superseding governance decision can reconsider; agents cannot |

For every domain-stage cell:

- **Non-goals** are every capability in cells to its right plus that row's
  Stage 5 prohibitions. They cannot be pulled into the current task.
- **Evidence** must demonstrate the exact cell and no stronger claim. A fixture
  replay is not connected evidence; an interface is not an implementation.
- **Stop point** is reached as soon as the cell's acceptance evidence passes.
  The next cell is a new task, not automatic continuation.
- **Rollback** returns to the nearest passing cell on the left without deleting
  adverse data, audit, or evidence.
- **Maintenance** includes upstream/schema/license review, regression fixtures,
  dependency/security updates, documentation, and deprecation for the exact
  cell. An unowned cell cannot promote.

## 2. Complexity budgets

Budgets are incremental maxima for one domain promotion. Exceeding one metric
requires splitting the task; Stage 3+ also requires an ADR/RFC.

| Budget | Modules (`M`) | Runtime deps (`D`) | Services (`S`) | Providers/implementations (`P`) | Persistent stores (`T`) | Network integrations (`N`) | Config/schema families (`C`) | CI jobs (`J`) | Credential classes (`K`) | Runtime processes (`X`) | Runbooks (`R`) | Operator roles (`O`) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `B0` | 2 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 |
| `B1` | 4 | 1 | 0 | 1 | 0 | 1 | 2 | 1 | 0 | 1 | 1 | 1 |
| `B2` | 8 | 2 | 1 | 2 | 1 | 2 | 4 | 2 | 1 | 2 | 2 | 2 |
| `B3` | 12 | 3 | 2 | 3 | 2 | 3 | 6 | 3 | 1 | 3 | 3 | 3 |
| `B4` | RFC-defined, with an explicit lifetime-cost and decommission budget |
| `B5` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

Existing code does not consume a new-stage budget again. The budget controls
the incremental change. Documentation/tests do count when they create a new
schema family, CI job, runbook, or operator burden.

## 3. Domain stage caps

`None` means Stage 0 is not useful and must not be scaffolded.

| # | Domain | Stage 0 — interface only (`B0`) | Stage 1 — MVC (`B1`) | Stage 2 — limited research quality (`B2`) | Stage 3 — extended conditional (`B3`) | Stage 4 — advanced optional (`B4`) | Stage 5 — out of scope (`B5`) |
| ---: | --- | --- | --- | --- | --- | --- | --- |
| 1 | Repository/tooling | None | Locked Python/web project; offline lint/type/test/build; one Compose stack | Clean-clone verification, deterministic package/container evidence | Signed/provenance-aware release workflow after release need | Reproducible multi-platform builds after measured demand | Bespoke build platform, multi-repo split, or secret-dependent default CI |
| 2 | Domain/events | Versioned immutable envelope and parser contract | Events required by current data/backtest slice only | Explicit migrations plus persistence for used events | Compatibility catalog and deprecation tooling | Cross-language generated SDK/event transport | Event-sourced microservice platform without demonstrated need; mutable events |
| 3 | Configuration | Typed schema, five environments, redaction/hash | Ordered local layers with fail-closed startup | Audited persisted versions and tested rollback | Authenticated admin review workflow | General policy engine | `canary`/`live` config, hidden aliases, fail-open unknown config |
| 4 | Run manifest/reproducibility | Immutable manifest schema and qualification predicate | Data/backtest runs bound to Git/config/data/model/result | Strategy/validation/report binding and clean-environment replay | Two-environment qualification and provenance | Signed attestations/reproducible-build linkage | Dirty, incomplete, unbound, or fabricated evidence accepted |
| 5 | Market-data foundation | Canonical Decimal/UTC/PIT record contracts | Synthetic package, manifest, lineage, content store, shared quality gate | Local version catalog and deterministic transforms used by two markets | Audited retention/correction workflow | Distributed catalog/object store | Mutable raw overwrite, hidden corrections, unmanifested mixed providers |
| 6 | Equity market data | Provider-neutral read-only protocol only because one adapter exists | One AAPL daily Twelve Data offline contract; unadjusted/non-display | One human-approved bounded connected AAPL daily qualification | Small reviewed US equity/ETF allowlist or one PIT corporate-action source, not both per task | Second provider or PIT universe after separate license/quality evidence | Live broker/order surface; redistribution/public display without rights; NBBO/execution claims without entitlement |
| 7 | Crypto market data | Public spot protocol only because one adapter exists | One BTC-USD Coinbase REST/WebSocket offline contract | One bounded public connected qualification | Small reviewed spot-pair allowlist on same venue | Second public venue with explicit no-fallback comparison | Private/user/order channels, leverage/derivatives, inferred sequences, automatic fallback |
| 8 | Data quality | Versioned status/code/report schema | Deterministic shared/equity/crypto fixture gates and quarantine | Provider-calibrated thresholds for qualified datasets | Explicit two-source disagreement analysis | Human-reviewed statistical anomaly model with deterministic fallback | Using `FAIL`/`QUARANTINED`, suppressing defects, or silently filling unknown data |
| 9 | Dataset/version/lineage | Manifest, partition, correction, parent, DAG contracts | Local content-addressed immutable datasets | Searchable local catalog with compatibility checks | Retention/garbage-collection policy that preserves referenced evidence | Remote immutable artifact/catalog backend | Rewriting historical datasets, orphaning manifests, or deleting adverse versions |
| 10 | Backtester | Plan/result/order/fill artifact contracts | One offline fixed-order bar engine with deterministic replay | One strategy-driven vertical slice using the same engine | Additional order type or intraday fidelity only after calibrated evidence | Independent engine comparison or order-book research | HFT/live execution, ideal fills, same-close look-ahead, or result-driven data edits |
| 11 | Execution/fill models | Explicit disposition and cost/fill interfaces | Conservative bar market/limit, latency, partial/non-fill, rejection | One calibrated market-specific scenario with sensitivity bounds | Recorded order-book replay for one venue/instrument | Queue-position/impact research model | Guaranteed fills, unexplained price improvement, omitted costs, live routing |
| 12 | Portfolio ledger | Immutable ledger-entry contracts | Single base currency, cash-only, long-only Decimal ledger | Multiple instruments in one base currency with full conservation | Explicit multi-currency/FX ledger with PIT rates | Tax-lot/corporate-action extensions | Margin, leverage, borrowing, short positions, custody, mutable history |
| 13 | Strategy interface | Trusted-local `StrategyProtocol` only when the first baseline task starts | One versioned strategy and one declared-data path | Second market baseline proving/refining the stable contract | Reviewed fixed registry and parameter/version migration | Process/container-isolated external strategy protocol | Arbitrary in-process uploads, secret/network access, direct orders, hidden LLM/data |
| 14 | Baseline strategies | None | One transparent buy-and-hold baseline for one market | One transparent baseline per market plus cash benchmark | At most two additional simple baselines per market, one per task | Complex research baselines with explicit owner | Profit claims, auto-optimization, six-strategy batch, silent cross-market reuse |
| 15 | Strategy validation | Result/status/schema contract when first baseline exists | Cash/buy-and-hold comparison and one immutable fixed OOS split | Cost/parameter sensitivity for the same baseline | Regime and walk-forward aggregation | Advanced statistically justified validation | Automatic promotion, single-metric pass, hiding failed splits |
| 16 | Walk-forward/OOS | Immutable split manifest | One fixed train/validation/test/OOS schedule | One rolling or expanding schedule with one refit rule | Multiple documented regimes/schedules | Nested or combinatorial purged CV | Retuning untouched OOS and still labeling it untouched |
| 17 | Overfitting/leakage controls | Search budget, experiment count, contamination flags | Look-ahead, same-close, feature/label/test contamination rejection | Multiple-testing warning and block bootstrap where applicable | Purging/embargo and one justified adjusted statistic | PBO, CPCV, Deflated Sharpe, or Reality Check individually justified | Disabling leakage gates, unlimited hidden search, statistical certainty claims |
| 18 | Risk engine | `RiskDecision` contract only | Stale/session/precision/notional plus single-symbol/gross exposure gates | Drawdown, concentration, venue/quote and liquidity limits | Fixed equity/crypto stress scenarios | Factor/covariance optimization with estimation controls | Strategy bypass, risk increase on unknown state, automated live limits/promotion |
| 19 | Experiment tracking | Immutable experiment/artifact metadata contract | Local content-addressed run index for one research slice | Parent/child comparison and finalized artifacts | PostgreSQL catalog after real query need | Remote multi-user experiment service | Mutable finalized results or deletion of unfavorable experiments |
| 20 | Reporting | Balanced machine/human report schema | One deterministic JSON/HTML report for one baseline | Validation/risk/benchmark sections backed by evidence | Strategy/version comparison report | Interactive exploratory reports backed by immutable data | Investment advice/profit promise, omitted adverse evidence, frontend recomputation |
| 21 | Evidence pipeline | Checksum index contract | Existing stage-specific synthetic evidence and verification | Generic collect/verify/index plus tamper rejection | Connected/release bundle after gates exist | Signed provenance/transparency publication | Fabricated PASS, secret/raw licensed content, mutable finalized evidence |
| 22 | Paper broker | Read-only capability endpoint/skeleton only | Internal deterministic market-order state machine, no external I/O | Limit/partial/cancel/expire with restart/replay and idempotency | Fault/rate-limit/unknown-state recovery drills | Multi-strategy simulation scale | Any live/external production order path or unknown-state auto-resubmit |
| 23 | External paper/sandbox adapters | Protocol only after internal paper state is stable | One static sandbox schema adapter, explicitly non-behavioral | One behavioral paper/sandbox adapter with offline contracts | Second adapter only after first maintenance evidence | Managed multi-adapter paper qualification | Production endpoint, over-privileged credential, automatic environment switch |
| 24 | Read-only account adapters | Protocol only after reconciliation contract exists | One sanitized recorded account-snapshot fixture | One opt-in real read-only adapter with permission verification | Second read-only provider | Multi-account read aggregation with isolation | Trading/transfer/withdrawal/key-management scope or account data in public evidence |
| 25 | Shadow monitoring | Immutable observation/read-model contract | Offline strategy-versus-paper comparison | One approved read-only account plus public market comparison | Continuous single-strategy monitor with health/alerts | Multi-strategy/venue shadow analytics | Any order submission or presenting shadow as live performance |
| 26 | Reconciliation | Five-state result contract | Internal ledger versus internal paper cash/position | Orders, fills, fees, realized/unrealized PnL | One external read-only source | Multi-venue/settlement reconciliation | `MISMATCHED/UNKNOWN/STALE/UNAVAILABLE` shown healthy or ignored |
| 27 | Drift | Versioned alert/measurement contract | One deterministic cost/slippage or signal drift report | Core data/signal/position/PnL/cost/fill/latency drifts | Feature/regime/parameter/version drift | Multivariate adaptive analysis with fixed action boundary | Black-box automatic risk increase, parameter rewrite, or promotion |
| 28 | API | Health/root endpoints only | Read-only dataset/backtest resources for implemented domains | Read-only validation/risk/evidence resources | Authenticated, authorized, audited bounded paper writes | Trusted multi-user administration | Live/order/withdrawal/transfer/risk-bypass/audit-delete endpoints |
| 29 | Web dashboard | Non-tradable environment-labeled placeholder | Data/backtest status and artifact inspection | Validation/risk/evidence views | Paper/shadow/reconciliation/alert views | Customizable portfolio views | Live controls, secrets, direct provider calls, authoritative frontend risk logic |
| 30 | Alerting | Severity and alert payload contract | Local persisted/in-app alert list | One reviewed outbound notification channel | Routing, deduplication, acknowledgement, escalation | On-call platform integration | Automatic promotion, risk increase, trading, or secret-bearing messages |
| 31 | Security | Security policy, private reporting, secret/workflow scans | Threat model for implemented offline/network surfaces | Auth/RBAC/redaction hardening when account/API state exists | Independent review and incident drills | Penetration test for deployed optional surface | Weakened least privilege, fail-open controls, security-gate waiver for release |
| 32 | Observability | Liveness/readiness only | Structured logs, correlation IDs, data/adapter freshness | Metrics for current workers/adapters and bounded retention | Tracing and explicit SLOs after an operated service exists | Distributed observability for proven scale | Telemetry containing secrets/account data or falsely healthy unknown state |
| 33 | Deployment | Secure local Compose definition | Verified single-host local research stack | Documented self-hosted research deployment with pinned artifacts | Backup/restore and controlled upgrade for persisted state | HA/orchestration after measured demand | Kubernetes/microservices before need; public database; live deployment |
| 34 | Release engineering | Package/container/dashboard build and checksum contracts | Offline candidate from a clean SHA | Connected candidate with reviewed redacted evidence | Signed GitHub release after explicit human approval | Reproducible multi-platform release | Automatic tag/publish, mutable artifacts, release with non-waivable gate failure |
| 35 | Freqtrade integration | None until an actual export fixture is approved | One offline CSV/JSON trade-history importer | Paper-event adapter with recorded contracts | Read-only strategy/position monitoring | Second-version compatibility or isolated paper bridge | Freqtrade live credentials/orders, automatic strategy promotion |
| 36 | Hummingbot integration | None until an actual export fixture is approved | One offline CSV/JSON trade-history importer | Paper-event adapter with recorded contracts | Read-only strategy/position monitoring | Second-version compatibility or isolated paper bridge | Hummingbot live credentials/orders, derivatives/leverage bridge |
| 37 | External strategy integrations | Versioned CSV/Parquet import schema only when a fixture exists | One offline imported signal/trade record path | Trusted local versioned adapter | Isolated process adapter without secrets/network by default | Reviewed container isolation for untrusted code | Arbitrary in-process package execution, host/secret access, direct provider/order calls |

## 4. Domain-specific acceptance evidence

At every promotion, rerun the row's evidence for the capabilities present in
the new cell. Later stages add evidence; they never replace an earlier gate.

| # | Domain | Mandatory acceptance evidence for each promoted cell |
| ---: | --- | --- |
| 1 | Repository/tooling | Locked install, format/lint/type/tests, policy/secret checks, applicable package/web/container build, clean-clone result at Stage 2+ |
| 2 | Domain/events | Canonical serialization/checksum, immutability, schema snapshot, unknown-version rejection, migration replay when added |
| 3 | Configuration | All five environments, unknown/live rejection, redaction, hash stability, audit and rollback replay when persisted |
| 4 | Run manifest/reproducibility | Complete/dirty/tamper rejection and two identical result checksums; two clean environments at Stage 3+ |
| 5 | Market-data foundation | Decimal/UTC/PIT property tests, manifest/checksum/lineage/tamper fixtures, correction preservation |
| 6 | Equity market data | Allowlist/schema/calendar/action/quality/license tests; connected redacted `PASS` only at Stage 2+ |
| 7 | Crypto market data | Public host/channel/schema/sequence/reconnect/stale/quality tests; connected redacted `PASS` only at Stage 2+ |
| 8 | Data quality | One passing and one deliberate failure/quarantine per new rule; unsafe evidence admission rejection |
| 9 | Dataset/version/lineage | Idempotent writes, traversal/cycle/tamper rejection, parent compatibility, referenced-data retention |
| 10 | Backtester | Repeated checksum, ordering, look-ahead rejection, plan/data binding, replay of each new behavior |
| 11 | Execution/fill | Market/limit/latency/partial/non-fill/rejection boundaries, no price improvement, cost sensitivity |
| 12 | Portfolio ledger | Cash/asset conservation, duplicate idempotency, PnL/cost basis, action and rollback replay |
| 13 | Strategy interface | Declared-data enforcement, determinism/version hash, unsupported-market rejection, no I/O/credential/order access |
| 14 | Baseline strategies | Frozen specification, hand-checkable expected signals/orders, benchmark label, deterministic result, adverse example |
| 15 | Strategy validation | Immutable evidence IDs, benchmark/OOS status, failed split visibility, contamination rejection |
| 16 | Walk-forward/OOS | Split manifest, non-overlap/PIT checks, fixed refit rule, untouched OOS checksum |
| 17 | Overfitting/leakage | Deliberately contaminated/overfit fixture rejection, experiment/search count, method assumptions/limits |
| 18 | Risk engine | Strategy non-bypass, stale/unknown rejection, exposure consistency, limit boundary and monotonicity properties |
| 19 | Experiment tracking | Immutable finalization, parent identity, checksum/path traversal/tamper rejection, adverse-run retention |
| 20 | Reporting | Golden machine/human report, manifest binding, missing/adverse evidence visibility, no performance claim leakage |
| 21 | Evidence pipeline | Index completeness, checksum reproduction, tamper/path/secret rejection, producer/run/Git identity |
| 22 | Paper broker | State-transition table, idempotency, unknown no-resubmit, restart/replay, conservation |
| 23 | External paper/sandbox adapters | Capability/environment/permission/allowlist/schema/retry/idempotency tests and separately opted-in evidence |
| 24 | Read-only account adapters | Read-only permission proof, schema/redaction/reconnect tests, no write endpoint, public-evidence privacy check |
| 25 | Shadow monitoring | Theory/paper/observed identity, freshness, read-only proof, no-order route, restart result |
| 26 | Reconciliation | Matched and each non-healthy state, duplicate/missing fill, fee/PnL difference, promotion block |
| 27 | Drift | Baseline/current/threshold/window/severity/reason/action fields, deterministic threshold boundary, no automatic risk increase |
| 28 | API | OpenAPI snapshot, authorization/audit/idempotency for writes, unknown-state and prohibited-route contracts |
| 29 | Web dashboard | Environment labels, stale/unknown/failure visibility, accessibility/responsive/E2E, no secret/direct-provider/frontend-risk logic |
| 30 | Alerting | Severity mapping, dedup/ack/retry when added, redaction, critical promotion block |
| 31 | Security | Threat/control mapping for reachable surface, negative regressions, secret/dependency/workflow/container scans as applicable |
| 32 | Observability | Health truthfulness, correlation continuity, freshness/metric bounds, redaction and failure-state tests |
| 33 | Deployment | Pinned build/start/health, non-root/read-only/capability checks, migration/backup/restore evidence when added |
| 34 | Release engineering | Clean SHA, artifact/checksum/SBOM/evidence verification, install/start/rollback smoke, explicit human authorization records |
| 35 | Freqtrade integration | Versioned sanitized fixture, parser/schema/error/idempotency tests, explicit paper/read-only capability, no credentials/orders |
| 36 | Hummingbot integration | Versioned sanitized fixture, parser/schema/error/idempotency tests, explicit paper/read-only capability, no credentials/orders |
| 37 | External strategy integrations | Import/version/schema determinism, resource/isolation checks at Stage 3+, no host secret/network/order access |

## 5. Promotion and maintenance ownership

| Domain family | Minimum maintainer | Additional promotion authority |
| --- | --- | --- |
| Repository, domain, config, manifests, API read paths | Repository maintainer | Code owner for schema compatibility |
| Market data, quality, datasets | Data owner | Human license/terms reviewer for connected or redistributed data |
| Backtest, fills, ledger, strategies, validation | Research owner | Independent research reviewer for claims/promotion |
| Risk, paper, shadow, reconciliation, drift, alerts | Risk owner | Human risk reviewer; security reviewer for external/account state |
| Security, observability, deployment, releases | Security/release owner | Independent security review for Stage 3+; explicit maintainer publish approval |
| Freqtrade, Hummingbot, external strategies/accounts | Integration owner | Security + risk review and explicit provider/environment approval |

The current initial owner is `EngelN9` where a narrower accepted ADR does not
name another owner. One person may hold multiple roles in the current trusted
single-user phase, but promotion remains an explicit recorded human act.

## 6. YAGNI and abstraction checks

Before moving right in any row, answer all of these with evidence:

1. What current user cannot complete at the left-hand stage?
2. Why can the gap not be solved inside the existing module?
3. Which exact test or report proves the new capability?
4. What new dependency/service/provider/config/CI/runbook/operator cost is
   introduced?
5. Who maintains it and what upstream change triggers re-review?
6. How is it disabled and rolled back without corrupting prior evidence?

If any answer is missing, remain at the current stage. A second implementation
precedes framework refinement; a speculative interface is not progress.
