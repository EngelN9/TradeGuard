# R3 promotion record

Decision ID: `TG-R3-PROMOTION-2026-08-11`

Decision: `PASS`

Transition: `R2 — Restricted market-data contracts` to
`R3 — Fixed-order deterministic simulation`

Approver: `EngelN9` (maintainer and initial research owner)

Decision time: `2026-08-11T11:43:19Z`

Reviewed pull request: [#3](https://github.com/EngelN9/TradeGuard/pull/3)

Reviewed head: `aee037fd2c3f8494cd45ac619869a3095afcc7dd`

Promotion merge: `b92c8e9e8f7943c063d7adb9e55c791a6108d9e0`

## Capability and version identity

The promoted capability is the offline fixed-order deterministic backtest and
replay engine, including the Decimal cash-only/long-only ledger, conservative
bar fills, separate equity and crypto costs, corporate actions, conservation
checks, and checksummed artifacts. Backtest artifacts use schema version
`1.1.0`. Strategy identity is not applicable because no strategy is included
in R3.

## Reviewed evidence

- The exact reviewed head passed GitHub Backend, Dashboard, Repository policy,
  Dependency scans, and Container scan checks.
- The fresh local gate passed Ruff format/lint, strict mypy for 63 source
  files, 236 offline tests with two connected tests deselected, 90.70% total
  coverage, two-workflow validation, secret scanning, dashboard typecheck, and
  two dashboard tests.
- The focused Prompt 6 evidence gate passed five tests covering evidence index
  and checksum reproduction, ordinary and recomputed manifest-provenance
  tamper rejection, and prefilled completion-time rejection.
- Synthetic review artifacts and their checksums remain under
  [`artifacts/evidence/prompt6/`](../../artifacts/evidence/prompt6/).

The connected tests were not executed and are not `PASS` evidence.

## Conditions, expiry, and re-review

This approval is bound to the reviewed head and promotion merge above. It has
no scheduled expiry while those immutable sources and artifacts remain intact.
A new human decision is required if the promoted code, schemas, model
assumptions, or evidence changes; an evidence checksum fails; or a material
security, correctness, data-integrity, or reproducibility defect is found.

R3 remains offline deterministic research only. It authorizes no strategy,
investment-performance claim, credential, account, connected qualification,
paper/shadow promotion, order route, `canary`, `live`, tag, or GitHub Release.
Twelve Data and Coinbase connected qualification remain `BLOCKED` and not
opted in. R4 is a separate future task.

## Rollback

Revert the R3 squash merge and return to the last verified R2 capability
boundary. Preserve the Prompt 6 artifacts, checksums, adverse results, and
this decision record for audit; do not rewrite or delete them.
