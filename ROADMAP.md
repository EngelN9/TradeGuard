# TradeGuard roadmap

**This file is not normative.** It is a reading guide to where the project
stands and what happens next. When it disagrees with
[`docs/roadmap/release-ladder.md`](docs/roadmap/release-ladder.md),
[`docs/roadmap/scope-ladder.md`](docs/roadmap/scope-ladder.md), or
[`docs/status/implementation-matrix.md`](docs/status/implementation-matrix.md),
those documents win and this file is the defect.

---

## Who this is for

The first named user is **the maintainer, working as a solo quantitative
researcher**, offline, against synthetic fixtures or data personally licensed
for internal use. The acceptance criterion is:

> The maintainer can take one strategy idea and produce a defensible
> keep-or-stop decision without leaving the tool.

External usability work — onboarding flows, install polish, tutorials, hosted
examples — is deliberately **out of scope** until a later ADR names an external
user. See [`docs/adr/0004-first-named-user-and-mvp-designation.md`](docs/adr/0004-first-named-user-and-mvp-designation.md).

---

## Where the project is

```
R4 STRATEGY CANDIDATE / R3 CURRENT / NOT TRADABLE
```

Public `main` is at **R3 — fixed-order deterministic simulation**: an offline
deterministic backtest and replay engine, a Decimal cash-only long-only ledger,
conservative fills, and separate equity/crypto cost models. Human promotion was
recorded on 2026-08-11 as
[`TG-R3-PROMOTION-2026-08-11`](docs/release/r3-promotion.md).

An **R4 candidate** exists on a branch: a trusted-local `StrategyProtocol` and
one transparent synthetic BTC-USD buy-and-hold baseline wired to the R3 result
path. Its status is `NOT_EVALUATED`. It is not promoted, not merged, and not a
capability claim.

There is no strategy validation, no independent risk engine, no account
integration, no order path, and no live capability.

## What is next

Exactly one thing: **exact-head human review of the R4 candidate.**

The review must confirm the candidate:

1. uses one exact market and immutable synthetic fixture approved in a separate
   task;
2. exposes a trusted-local `StrategyProtocol` with one immediate consumer and no
   provider, credential, risk-config, mutable-evidence, or order access;
3. adds one transparent buy-and-hold baseline with a frozen specification and a
   version hash;
4. enforces declared-data and unsupported-market rejection;
5. proves a deterministic strategy-to-order-to-R3-result path with all evidence
   clearly labelled synthetic and non-promotional.

Authority: maintainer and research reviewer. Passing automated checks does not
authorize R4 promotion, merge, R5 work, connected qualification, a tag, or a
release. A failed or blocked review produces a bounded defect list and the
project stays at R3.

## Stops

Every stop is a legitimate permanent product boundary — usable, testable,
maintainable, and safe to stop at. An arrow is a separate decision, not an
obligation. Nothing below is a commitment to build.

| Stop | Outcome | State |
| --- | --- | --- |
| R0 | Governance and safety baseline | `done` |
| R1 | Reproducible offline foundation | `done` |
| R2 | Restricted market-data contracts | `done` |
| R3 | Fixed-order deterministic simulation | **`current`** |
| R4 | One-strategy research slice | `candidate` |
| R5 | Basic comparative and out-of-sample validation | `planned` |
| R6 | Minimal independent risk engine | `planned` |
| R7 | Reproducible research report and evidence | `planned` |
| R8 | Internal deterministic paper broker | `planned` |
| R9 | Read-only monitoring and reconciliation slice | `planned` |
| R10 | Connected research release | `planned` |

Entry gates, exit evidence, rollback paths, complexity budgets, and promotion
authorities for each stop are in
[`docs/roadmap/release-ladder.md`](docs/roadmap/release-ladder.md).

## MVP

There is no single all-or-nothing MVP — every stop is a valid permanent product
boundary. Two stops carry a minimum-viable designation, both of which the
release ladder already implies:

| Layer | Stop | Why |
| --- | --- | --- |
| Functional MVP | **R5** | First stop that can answer the product's own question end to end: one baseline, a cash and buy-and-hold benchmark, one untouched out-of-sample split, one cost sensitivity run |
| Public MVP | **R7** | First stop where that answer is shareable and auditable: a finalized experiment, a balanced report, and a tamper-rejecting evidence index |

Neither designation makes an earlier stop provisional, and neither authorizes
implementation. Recorded in
[`docs/adr/0004-first-named-user-and-mvp-designation.md`](docs/adr/0004-first-named-user-and-mvp-designation.md).

### Path from here to the functional MVP

| # | Step | Stop |
| --- | --- | --- |
| 1 | Exact-head human review of the R4 candidate returns `PASS` | R4 — the only current gate |
| 2 | Cash and buy-and-hold benchmark comparison | R5 |
| 3 | One immutable split declared before results, out-of-sample left untouched | R5 |
| 4 | One cost sensitivity run | R5 |
| 5 | Contamination rejection tests, with failed results kept visible | R5 |

Nothing else stands between the current stop and the functional MVP. Each step
is a separate task with its own evidence and its own human promotion decision.

---

## Why there are no dates

This roadmap is gate-driven, not date-driven. A stop is reached when its
evidence passes human review, and not before. `R0`–`R10` are planning
identifiers, not version numbers and not automatic tags — semantic versions and
publication are separate human decisions.

Committing to dates would create pressure to promote on schedule rather than on
evidence, which is the failure mode this project exists to prevent.

## Blocked

These are not scheduling problems. Each needs a named human or external decision
before any work on it is authorized.

| Capability | Unblock condition | Authority |
| --- | --- | --- |
| Twelve Data connected AAPL daily qualification | Approved exact XNAS/XNGS session registry, local data-only credential, one bounded `PASS`, redacted evidence review | Data/license owner and maintainer |
| Coinbase public connected qualification | Terms and jurisdiction recheck, one bounded public REST/WebSocket `PASS`, redacted evidence review | Data/license owner and maintainer |
| Any account integration | Internal paper and reconciliation contracts, plus adapter/permission/terms approval | Security and risk owners |
| Connected research release or tag | R10 non-waivable gates, human GO, verified candidate, explicit exact publish authorization | Maintainer and release owner |

## Deferred and optional

Not prerequisites for R3–R10. Each must independently prove a need, an owner, a
complexity budget, and a rollback path before it is considered:

- multiple baseline families, automatic parameter search, Monte Carlo suites,
  PBO/CPCV/Reality Check, factor optimization, generalized plugin systems;
- multiple market-data, paper, or account providers;
- Freqtrade and Hummingbot bridges;
- multi-user administration, multi-tenancy, distributed workers, Kubernetes,
  high availability, remote experiment stores, multi-platform releases;
- arbitrary untrusted strategy execution.

## Permanently excluded

Not "later" — these are outside the project's scope and are enforced by
rejection tests:

- `canary` or `live` trading, and any production order path;
- withdrawal, transfer, custody, sub-account, or API-key management;
- leverage, margin, borrowing, shorting, futures, perpetuals, options;
- automatic strategy, risk, or release promotion;
- strategy access to secrets, provider clients, or order APIs;
- mutable or fabricated research and release evidence;
- profit guarantees or investment advice.

## Where to go next

| Question | Document |
| --- | --- |
| What is actually implemented, blocked, or deferred? | [`docs/status/implementation-matrix.md`](docs/status/implementation-matrix.md) |
| What are the exact gates for each stop? | [`docs/roadmap/release-ladder.md`](docs/roadmap/release-ladder.md) |
| How far may each domain expand? | [`docs/roadmap/scope-ladder.md`](docs/roadmap/scope-ladder.md) |
| What does the project do today? | [`README.md`](README.md) |
| How do I scope one increment? | [`docs/ai/claude-code-task-template.md`](docs/ai/claude-code-task-template.md) |
