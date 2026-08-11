# Historical Prompt 0–17 migration

Status: `HISTORICAL / NON-NORMATIVE`

The root `PROMPTS.md` was retired because it mixed reusable safety rules,
historical one-time construction instructions, connected qualification, and
release publication into one linear program. Git history preserves the exact
original. This file records where its durable requirements moved and how its
oversized stages are treated now.

Normative scope is now defined by:

- `AGENTS.md`;
- `docs/governance/`;
- `docs/roadmap/scope-ladder.md`;
- `docs/roadmap/release-ladder.md`;
- accepted ADRs and the implementation matrix.

## Migration map

| Old prompt | Historical purpose | New treatment |
| --- | --- | --- |
| 0 | Repository assessment and aggregate connected-release contract | Completed history; durable contract in ADR 0001 and `docs/release/connected-release-v1.md`; status now in the matrix |
| 1 | Bootstrap, CI, containers, skeleton services | Completed; governed as Release Stop R1 and domain stages for tooling/deployment/API/dashboard |
| 2 | Events, configuration, run manifest | Completed; contracts in `docs/architecture/domain-contracts.md`; separate domain ladders |
| 3 | Canonical data, manifests, quality | Completed; durable contract in `docs/data/data-foundation.md` |
| 4 | Twelve Data equity adapter | Offline implementation completed; connected promotion remains `BLOCKED`; ADR 0002 is authority |
| 5 | Coinbase REST/WebSocket adapter | Offline implementation completed; connected promotion remains `BLOCKED`; ADR 0003 is authority |
| 6 | Backtester, ledger, fills, costs | Implemented, human-reviewed `PASS`, and promoted to stable R3 on `main`; durable decision in `docs/release/r3-promotion.md` |
| 7 | Protocol plus six baselines and registry | R4 `NEXT` is only 7A protocol + one baseline; 7B second-market baseline and 7C registry refinement remain `LATER`; extra baselines remain `OPTIONAL` |
| 8 | Splits, walk-forward, sensitivities, bootstrap, overfitting | Split: fixed split/OOS; benchmark; cost sensitivity; walk-forward; then optional advanced statistics |
| 9 | Full independent risk engine | Split: fail-closed single-symbol/stale/session gates; portfolio limits; stresses; advanced models optional |
| 10 | Experiment store, reports, evidence | Split into three domains; local content-addressed implementation precedes persistence or release evidence |
| 11 | Full paper broker plus external adapter | Split: internal market-order state machine; fills/replay; external sandbox/read-only only after internal stability |
| 12 | Monitoring, reconciliation, all drift types | Split into monitoring, reconciliation, and drift stages; read-only account dependency is explicit |
| 13 | Broad FastAPI and complete dashboard | Split by backing vertical slice; read-only data/backtest views precede auth writes or monitoring pages |
| 14 | Security, observability, database, release engineering | Split into four domains; each grows only when an implemented surface needs it |
| 15 | Two-environment offline plus connected E2E qualification | Split into offline qualification and separately authorized connected qualification; blocked results remain blocked |
| 16 | Release-candidate assembly | Later release-engineering stop after all named gates; no tag or publication authority |
| 17 | Tag and GitHub Release | Human-only publication procedure; never an automatic successor task |

## Removed assumptions

- Prompt numbers no longer imply authorization to continue automatically.
- A single v0.1.0 batch is no longer the only meaningful completion state.
- Six baseline strategies are not required before one vertical slice is useful.
- Advanced bootstrap/overfitting methods are not minimum implementation.
- Full monitoring, full dashboard, account integration, and release machinery
  are not prerequisites for maintaining the deterministic offline core.
- Connected qualification, tag creation, and GitHub publication always require
  explicit human gates.

## Retained hard requirements

No-live boundaries, least privilege, provider allowlists, offline/default CI,
truthful connected status, UTC/Decimal authority, deterministic manifests,
point-in-time data, conservative execution, independent risk, immutable
evidence, human promotion, and non-waivable security/data/reproducibility gates
were moved into the durable governance documents rather than discarded.
