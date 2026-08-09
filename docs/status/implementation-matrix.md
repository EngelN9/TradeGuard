# TradeGuard implementation and roadmap matrix

Assessment date: `2026-08-08`

Public repository: `https://github.com/EngelN9/TradeGuard`

Public stable base: `main@0b73ca4a562f56bb05d8a0537d596332b266190c`

Review candidate: `codex/prompt-6-deterministic-backtester@cddb676f5af4f4992daf4fde14dd7b4f65f58508`

Overall candidate status: `DETERMINISTIC BACKTESTER IMPLEMENTED / NOT TRADABLE`

## How to read this matrix

Implementation and roadmap are separate axes:

- Implementation: `IMPLEMENTED`, `PARTIAL`, `MISSING`, `NOT APPLICABLE`.
- Roadmap: `CURRENT`, `NEXT`, `LATER`, `OPTIONAL`, `BLOCKED`, `OUT OF SCOPE`.

`CURRENT` means stable on the named public base. `NEXT` is the one immediate
promotion slice. `IMPLEMENTED + BLOCKED` means code/offline contracts exist but
a named human/external qualification is unmet. Future rows are not commitments.

## Repository reality

- `main` is the stable **R2 — Restricted market-data contracts** stop.
- Draft PR #3 is cleanly mergeable and its five GitHub checks passed on
  2026-08-01. It is the **R3 candidate**, not promoted `main`.
- The remediated R3 candidate's fresh local evidence is 236 offline tests
  passing, two connected tests deselected, and 90.70% total coverage (93.42%
  line coverage and 78.45% branch coverage). The
  bundle includes direct regressions for manifest binding, aggregate
  participation, post-bar corporate actions and completion-time ordering.
- Both connected market-data qualifications remain unexecuted/not opted in.
- The paper broker, worker, API, and dashboard remain bounded skeletons except
  for the offline data/backtest CLI paths described below.
- No strategy, investment result, risk engine, account integration, external
  order route, `canary`, `live`, withdrawal, or transfer capability exists.

## Domain matrix

| # | Domain | Implementation | Roadmap | Actual evidence | Current cap / named gap |
| ---: | --- | --- | --- | --- | --- |
| 1 | Repository/tooling | `IMPLEMENTED` | `CURRENT` | `pyproject.toml`, `uv.lock`, Make targets, SHA-pinned CI, package/web/container builds | R2/R3 toolchain; no new build platform |
| 2 | Domain/events | `IMPLEMENTED` | `CURRENT` | 23 immutable event models, canonical checksum, parser/migration policy, schemas | Used event contracts only; no event bus/persistence claim |
| 3 | Configuration | `IMPLEMENTED` | `CURRENT` | Layered safe YAML, five environments, redaction/hash/audit tests | Local validated config; no admin policy engine |
| 4 | Run manifest/reproducibility | `IMPLEMENTED` | `CURRENT` | Clean/dirty `RunManifest`, lock/config/data/model/result binding | Data/backtest binding; two-environment qualification is later |
| 5 | Market-data foundation | `IMPLEMENTED` | `CURRENT` | Canonical Decimal/UTC records, PIT metadata, manifests, lineage, content store | Local immutable foundation; no persistent catalog |
| 6 | Equity market data | `IMPLEMENTED` | `CURRENT` | Restricted AAPL daily Twelve Data offline contracts, ADR 0002 | Connected use is separately `BLOCKED`; no corporate-action feed/public display |
| 7 | Crypto market data | `IMPLEMENTED` | `CURRENT` | Restricted BTC-USD Coinbase REST/WebSocket offline/replay contracts, ADR 0003 | Connected use is separately `BLOCKED`; no private/user channels |
| 8 | Data quality | `IMPLEMENTED` | `CURRENT` | Shared/equity/crypto status codes, synthetic gates, quarantine enforcement | Provider calibration/cross-source comparison deferred |
| 9 | Dataset/version/lineage | `IMPLEMENTED` | `CURRENT` | `DatasetManifest`, acyclic transformations, local content address/tamper tests | No searchable/persistent catalog or retention service |
| 10 | Backtester | `IMPLEMENTED` on PR #3 | `NEXT` | Five-key timeline, fixed-order backtest/replay, result-bound reproducible run identity plus complete-manifest checksum, engine-owned completion time | Human R3 promotion review required before merge or strategy work |
| 11 | Execution/fill models | `IMPLEMENTED` on PR #3 | `NEXT` | Conservative future-bar market/limit, aggregate bar participation, latency, partial/non-fill, rejection | Human assumptions/same-close review required; no order book/queue claim |
| 12 | Portfolio ledger | `IMPLEMENTED` on PR #3 | `NEXT` | Decimal cash/long-only ledger, PnL/action finalization, idempotency, corporate actions, conservation | Human conservation/split review required; single base currency only |
| 13 | Strategy interface | `MISSING` | `LATER` | Domain output event types exist; no `strategies` implementation | First post-R3 slice: protocol plus one consumer, no speculative registry |
| 14 | Baseline strategies | `MISSING` | `LATER` | None | One market/one buy-and-hold baseline first; six-strategy batch removed |
| 15 | Strategy validation | `MISSING` | `LATER` | Data eligibility gate is not strategy validation | Begin only after one baseline: benchmark + one fixed OOS split |
| 16 | Walk-forward/OOS | `MISSING` | `LATER` | None | Fixed split precedes rolling/expanding schedules |
| 17 | Overfitting/leakage controls | `PARTIAL` | `LATER` | Backtest same-close/look-ahead rejection exists | Strategy/OOS contamination and multiple-testing controls await validation slice |
| 18 | Risk engine | `MISSING` | `LATER` | `RiskDecision` event/config schema only; no evaluator | Minimal stale/session/exposure gate after basic validation |
| 19 | Experiment tracking | `PARTIAL` | `LATER` | Run manifest and stage-specific artifacts only | No experiment model/catalog/finalization workflow |
| 20 | Reporting | `MISSING` | `LATER` | Safe CLI inspection/evidence summaries are not research reports | One balanced report only after a baseline and validation evidence |
| 21 | Evidence pipeline | `PARTIAL` | `LATER` | Stage-specific checksum indexes and redacted synthetic bundles | Generic collect/verify/index and tamper workflow remains later |
| 22 | Paper broker | `PARTIAL` | `LATER` | Capability-only FastAPI skeleton; no submit/order route | Internal deterministic market-order state machine is first paper slice |
| 23 | External paper/sandbox adapters | `MISSING` | `LATER` | Coinbase static sandbox selected historically; no adapter implementation | Wait for internal paper stability; connected environment review required |
| 24 | Read-only account adapters | `MISSING` | `LATER` | None | Wait for reconciliation contract; permission verification mandatory |
| 25 | Shadow monitoring | `MISSING` | `LATER` | `shadow` is an allowed configuration ceiling only | No account/market comparison or monitoring runtime exists |
| 26 | Reconciliation | `MISSING` | `LATER` | Five-state domain enum only | Internal ledger-to-paper comparison precedes external account use |
| 27 | Drift | `MISSING` | `LATER` | Drift event type only | One deterministic drift measure first; no automatic action |
| 28 | API | `PARTIAL` | `CURRENT` | Root and health endpoints only; OpenAPI contract fixes that narrow surface | Resource APIs follow implemented backing domains; no write/auth claim |
| 29 | Web dashboard | `PARTIAL` | `CURRENT` | Responsive environment-labeled non-tradable placeholder | Text still describes bootstrap; real pages follow data/backtest status work |
| 30 | Alerting | `MISSING` | `LATER` | Severity/event concepts only | Local alert list first; no outbound channel |
| 31 | Security | `PARTIAL` | `CURRENT` | `SECURITY.md`, private reporting, secret/workflow/dependency/container checks | Threat model for implemented surfaces remains a later bounded task |
| 32 | Observability | `PARTIAL` | `LATER` | Liveness/readiness only | Structured logs/correlation/freshness first; no tracing platform |
| 33 | Deployment | `PARTIAL` | `CURRENT` | Secure local Compose skeleton, non-root/read-only/cap-drop app containers | Local research stack only; persistence/backup deployment not qualified |
| 34 | Release engineering | `PARTIAL` | `LATER` | Package/web/container build and checksums; no candidate/tag/release | Offline candidate precedes connected candidate; publication human-only |
| 35 | Freqtrade integration | `MISSING` | `OPTIONAL` | A pre-existing external Docker image on the workstation is not TradeGuard capability | First allowed slice is one offline export importer after a fixture/use case |
| 36 | Hummingbot integration | `MISSING` | `OPTIONAL` | None | Same: offline import precedes paper/read-only monitoring |
| 37 | External strategy integrations | `MISSING` | `OPTIONAL` | None | No arbitrary packages; versioned offline import or trusted local adapter first |

## Immediate `NEXT` gate

Only R3 human promotion review is `NEXT`:

1. verify event ordering and deterministic checksum scope;
2. verify cash/asset conservation and duplicate-fill idempotency;
3. verify same-close rejection and future-knowable bars;
4. review market/limit, latency, partial/non-fill, precision/notional, session,
   halt, and maintenance behavior;
5. review separate equity/crypto costs and synthetic assumptions;
6. review split/dividend/symbol/delisting accounting and evidence;
7. record `PASS`, `FAIL`, or `BLOCKED` and a maintainer merge decision.

Strategy code is not `NEXT` until this gate passes and the stable base changes.

## Blocker register

| Capability | Status | Exact unblock condition | Authority |
| --- | --- | --- | --- |
| Twelve Data connected AAPL daily qualification | `BLOCKED` | Approved exact XNAS/XNGS session registry, local data-only credential, one bounded `PASS`, redacted evidence review | Data/license owner and maintainer |
| Coinbase public connected qualification | `BLOCKED` | Terms/jurisdiction recheck, one bounded public REST/WebSocket `PASS`, redacted evidence review | Data/license owner and maintainer |
| PR #3 R3 promotion | `NEXT` (human gate not a technical blocker) | Review checklist above and explicit decision | Maintainer/research reviewer |
| Any account integration | `BLOCKED` | Internal paper/reconciliation contracts plus adapter/permission/terms approval | Security and risk owners |
| Connected Research Release/tag | `BLOCKED` | R10 non-waivable gates, human GO, verified candidate, explicit exact publish authorization | Maintainer/release owner |

## Explicitly out of scope

| Capability | Roadmap status | Enforcement expectation |
| --- | --- | --- |
| `canary` or `live` runtime/order path | `OUT OF SCOPE` | Configuration/CLI/API/workflow negative tests |
| Withdrawal, transfer, custody, sub-account or API-key management | `OUT OF SCOPE` | Adapter capability and endpoint allowlist rejection |
| Leverage, margin, borrowing, shorting, derivatives | `OUT OF SCOPE` | Market/ledger/config schema rejection |
| Automatic strategy/risk/release promotion | `OUT OF SCOPE` | Human approval record required |
| Arbitrary in-process untrusted strategy execution | `OUT OF SCOPE` | No dynamic package upload/import path |
| Profit guarantees or investment advice | `OUT OF SCOPE` | Public copy/report review |

## Evidence locations

- Domain/config schemas: `schemas/`
- Synthetic data fixtures: `tests/fixtures/market_data/`
- Adapter fixtures: `tests/fixtures/adapters/`
- Stage evidence: `artifacts/evidence/bootstrap/`, `prompt2/`, `prompt3/`,
  `prompt4/`, `prompt5/`, and PR #3's `prompt6/`
- Durable contracts and human gates: `docs/architecture/`, `docs/data/`,
  `docs/backtest/`, `docs/adapters/`, and `docs/adr/`

Historical Prompt 0–6 evidence remains valid as delivery history but no longer
defines the next scope. See `docs/history/prompt-migration.md`.
