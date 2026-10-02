# Project handoff snapshot — 2026-09-07

Status: `NON-NORMATIVE / LOCAL HANDOFF / REVERIFY BEFORE ACTING`

This is a dated transition record for the next maintainer session. It is not
promotion evidence, a release record, or an authority that overrides
`AGENTS.md`, the implementation matrix, the scope ladder, or the release
ladder. GitHub, branch, review, and check state can change after this snapshot;
recheck every exact SHA before approving, merging, or editing it.

## Snapshot scope and sources

This record was assembled from the local working tree and GitHub on
2026-09-07. It includes a fresh local offline validation pass of the current
`codex/r4-strategy-slice` checkout and read-only GitHub PR/check inspection.
No connected test, promotion, merge, tag, release, credential, or external
market-data operation was performed.

## Authoritative project status at the snapshot

- Public `main` is `3c6751e59d67a63749ad020dba1cd7e4c59293ed` and remains the
  promoted **R3 fixed-order deterministic simulation** stop.
- R4 is a **candidate**, not `CURRENT`: `R4 STRATEGY CANDIDATE / R3 CURRENT /
  NOT TRADABLE`.
- Connected Twelve Data and Coinbase qualification remain `BLOCKED`; neither
  was opted in or run in this handoff.
- TradeGuard has no live/canary trading, external order, withdrawal, transfer,
  custody, leverage, or provider-credential capability. The R4 baseline is
  synthetic-only and is not investment, profitability, validation, risk, or
  promotion evidence.

## Branch and pull-request state

| Item | Exact state observed | Required follow-up |
| --- | --- | --- |
| Local checkout | `codex/r4-strategy-slice` at `04c720bd9bb8c1248fe83c3f3fa22e94719ad4d8`, tracking `origin/codex/r4-strategy-slice`; four commits ahead of `main` | Do not treat this closed-PR branch as merge authority. |
| PR #7 | [Closed, unmerged](https://github.com/EngelN9/TradeGuard/pull/7), exact head `04c720bd9bb8c1248fe83c3f3fa22e94719ad4d8` | Keep as historical review evidence; do not reopen or merge it as a shortcut. |
| PR #10 | [Draft, open code slice](https://github.com/EngelN9/TradeGuard/pull/10), `claude/r4-strategy-slice` at `9b59c7d158e9e7a044c84d20c35d8898d3893a6d`, based on `main@3c6751e` | Resolve the R4 evidence finding below, then obtain exact-head human review before any Ready/merge decision. |
| PR #11 | [Draft, open documentation/governance slice](https://github.com/EngelN9/TradeGuard/pull/11), `claude/r4-docs-governance` at `e82488a11a00a549c05c3be8203b888ef0281577`, stacked on PR #10 | Review only after PR #10's base and the public-positioning/ADR decisions are settled. |

The Git tree for `e82488a` and the original combined R4 head `04c720b` is
identical (`b8091b7e0accc360087fddc6a446a526ab63df8b`). The split changed
commit topology, not the combined file content. PR #10 and PR #11 are still
separate human decisions; tree equality does not approve either one.

At the snapshot, both draft PRs had no recorded human review and each had these
five successful CI checks for its own exact head: Backend quality and tests,
Dashboard check and build, Repository policy, Dependency scans, and Container
scan. These automated checks are supporting evidence only, not promotion or
merge approval.

## Local worktree preservation

The following local changes pre-existed this handoff and must be treated as
user-owned until explicitly reviewed:

- `docs/README.md`: adds the documentation-map entry for ADR 0005.
- `docs/adr/0005-external-recommendation-triage.md`: an accepted, documentation-
  only disposition of an external recommendation set. It authorizes no
  implementation and says the sole `NEXT` gate remains R4 exact-head review.

Do not discard, stage, amend, fold into an unrelated PR, or publish these files
without the maintainer's explicit decision. This handoff file is an additional
local documentation change and likewise has not been committed or pushed.

## Fresh local validation

The following was executed on the local combined-R4 checkout. A unique
per-session `TEMP` directory was used because the historic fixed pytest temp
path can return `WinError 5`; no test, threshold, or project setting was
weakened.

| Check | Result |
| --- | --- |
| Ruff format | PASS — `163 files already formatted` |
| Ruff lint | PASS — `All checks passed!` |
| Mypy | PASS — `Success: no issues found in 69 source files` |
| Offline pytest | PASS — `253 passed, 2 deselected`, coverage `90.10%` |
| Workflow validation | PASS — `Validated 2 workflow(s)` |
| Secret scan | PASS — `Secret baseline scan passed` |
| Dashboard typecheck | PASS |
| Dashboard tests | PASS — `2 passed, 0 failed` |
| Installed-environment `pip-audit --skip-editable` | PASS — no known vulnerabilities; this is not lockfile-equivalent CI evidence |
| `npm audit --omit=dev --audit-level=high` | PASS — `0 vulnerabilities` |
| Local container scan | SKIP — CI-only (Trivy); successful CI scans are recorded on PRs #10 and #11 |
| Connected tests | BLOCKED — intentionally not opted in and never represented as PASS |

## R4 review findings and gate

1. **Promotion-blocking acceptance gap — high confidence.** Scope-ladder
   domain 14 requires an adverse example for a baseline. The current R4
   evidence covers valid synthetic execution and fail-closed *input* rejection,
   but PR #10 identifies no example of an unfavourable baseline *result*.
   Resolve the requirement or add narrowly scoped, non-promotional evidence and
   a regression test before a human R4 verdict.
2. **Regression-guard gap — medium confidence.** The static safety test for
   forbidden dynamic/client imports scans `buy_and_hold.py`, `protocol.py`, and
   `cli.py`, but not `models.py` or `runner.py`. Direct import inspection at
   this snapshot found no provider, credential, network-client, or dynamic-
   loader import in any strategy module; nevertheless, the automated guard
   should cover all strategy modules before relying on it as a lasting boundary.
3. **Human review remains absent — high confidence.** Both PR #10 and PR #11
   are drafts with no recorded human review. Passing CI does not satisfy the
   exact-head review required for R4, nor the separate maintainer decision on
   the public README/ROADMAP/ADR changes in PR #11.

**Promotion gate: `BLOCKED` — R4 awaits a resolved acceptance-evidence gap and
exact-head human review.** R5, connected qualification, tags, releases,
paper/shadow advancement, and any live capability remain out of scope.

## Addendum — findings 1 and 2 closed, same date

After this snapshot was written, findings 1 and 2 above were closed on
`claude/r4-strategy-slice` by commit `88b348a`, which adds the adverse baseline
example and its evidence artifact and widens the strategy import guard to every
`strategies/*.py` with an explicit module-set assertion. Local validation of
that commit: ruff and mypy clean, `254 passed, 2 deselected`, coverage `90.10%`.

Finding 3 is unchanged. **The promotion gate remains `BLOCKED`**: PR #10 and
PR #11 are still drafts with no recorded human review, and exact-head review is
still required before any R4 verdict, merge, or R5 work. Closing an acceptance
gap is not a verdict.

The findings list above is preserved as written so the review history stays
readable; this addendum is the correction, not an edit to it.

## Safe next-session sequence

1. Read `AGENTS.md`, the governance documents, the ladders, implementation
   matrix, `SECURITY.md`, `CONTRIBUTING.md`, and this snapshot.
2. Recheck `git status`, branch/HEAD, `origin/main`, PR #10/#11 exact heads,
   draft state, reviews, check results, and whether the user-owned ADR 0005
   changes remain uncommitted.
3. Ask the maintainer to decide whether to address the two R4 review findings,
   proceed with exact-head review, or keep R4 stopped as a candidate. Do not
   change, merge, promote, or retarget a PR merely because CI is green.
4. Keep PR #7 closed. Treat PRs #10 and #11 as the only active R4 review paths
   unless the maintainer explicitly changes that plan.

## Rollback

Remove this handoff file and its documentation-map link if it becomes obsolete.
No code, schema, data, R3 evidence, promotion record, or GitHub state depends
on it.
