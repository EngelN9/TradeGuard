# Claude Code task template

Use this template for one independently reviewable TradeGuard increment driven
by Claude Code. It is a reusable scope contract, not a roadmap step and not a
sequence of mandatory prompts.

The Codex equivalent is [`codex-task-template.md`](codex-task-template.md).
Both templates express the same scope discipline; this one adds the Claude Code
workflow, the local command set from [`CLAUDE.md`](../../CLAUDE.md), and the
four completion conditions as hard fields.

`/tg-task <objective>` expands this template automatically.

## 1. How to size one task

One task is one **vertical slice inside one domain row**, capped by that row's
stage cell and complexity budget in
[`scope-ladder.md`](../roadmap/scope-ladder.md).

Split the task if it would need more than one of any of the following:

- new provider, service, persistent store, or network integration;
- new strategy family, market, or base currency;
- promotion decision or release stop;
- domain row moving right by more than one stage.

If no current consumer of an interface exists, do not create the interface. If a
stage is useful and maintainable without its successor, stop there and open a
separate task later.

## 2. The template

```markdown
You are working on TradeGuard.

## Required reading before acting

1. `CLAUDE.md` and `AGENTS.md` (plus any narrower `AGENTS.md`).
2. `docs/status/implementation-matrix.md` — current reality.
3. The target domain's row in `docs/roadmap/scope-ladder.md`.
4. The relevant stop in `docs/roadmap/release-ladder.md`.
5. The relevant source, tests, schemas, configuration, ADRs, and evidence.

Do not assume repository state from memory or from a previous session.

## Scope contract

Objective:
<one observable outcome, one sentence>

Target domain:
<row number and name from scope-ladder.md, e.g. "10 — Backtester">

Stage cap:
<Stage 0-5 for this task. Reaching the cap ends the task.
Anything to the right of this cell is a non-goal, not a stretch goal.>

Complexity budget:
<B0-B5. Maximum NEW modules / runtime deps / services / providers /
persistent stores / network integrations / config families / CI jobs /
credential classes / runtime processes / runbooks / operator roles.
Existing code does not consume the budget again.>

Current stable stop:
<R value taken from docs/status/implementation-matrix.md, not from memory>

Target stop for this task:
<the same R value, or a named R+1 candidate. A candidate is not a promotion.>

In scope:
- <observable behavior 1>
- <observable behavior 2, optional>

Non-goals:
- <the specific next-stage capability being deliberately deferred>
- every capability in cells to the right of the stage cap
- that row's Stage 5 prohibitions
- no live/canary, order submission, withdrawal, transfer, leverage, credential,
  or account authority

Entry gate:
<the evidence or recorded human decision that must already exist for this task
to be authorized. If it does not exist, stop and report BLOCKED.>

## Acceptance — all four are mandatory, one failure means FAIL

Runnable:
<one exact command from the CLAUDE.md table that produces the claimed behavior,
and the observable output that proves it>

Testable:
<test file paths, pytest markers, and the expected result, including at least
one negative/boundary test for any safety or risk behavior; plus the row's
mandatory acceptance evidence from scope-ladder.md section 4>

Maintainable:
<named human owner from scope-ladder.md section 5; the regression test added;
the docs, schema snapshots, manifests, and evidence updated in the same change;
the upstream change that triggers re-review>

Stoppable:
<why this exact state is a legitimate permanent stopping point that needs no
successor; the precise rollback steps back to the nearest passing cell; and a
statement that no placeholder implying future capability was created>

## Scope-breach protocol

If the objective turns out to exceed the stage cap or the complexity budget:

1. implement only the smallest independently useful authorized slice;
2. mark the remainder `LATER`, `OPTIONAL`, `BLOCKED`, or `OUT OF SCOPE`;
3. do not create scaffolding, config keys, or interfaces that imply the deferred
   capability exists or is planned;
4. stop and request explicit human authorization; do not proceed on assumption.

Report a scope breach as a finding, not as a failure to be worked around.

## Authorization

Do not commit, push, merge, rebase, tag, open or update a pull request, connect
to a provider, set a connected-test opt-in variable, or change any GitHub state
unless this task explicitly authorizes that exact action.

## Before editing, report

- Repository Reality Check (branch, base, dirty files, and whether git works)
- Objective and the stage/budget/stop binding above
- Assumptions
- Human decisions required
- Files expected to change
- Validation plan (exact commands)
- Risk impact
- Rollback approach

## After finishing, report

- Summary
- Files changed
- Behavior changes
- Architecture decisions
- Risk impact
- Security impact
- Tests executed and exact results (unrun tests are SKIP, never PASS)
- Evidence generated
- Known limitations
- Rollback plan
- Remaining/deferred work
- Promotion gate result: PASS / FAIL / BLOCKED
```

## 3. Worked example of the scope contract

The following fills the contract for the smallest authorized slice after the R3
promotion review passes. It is an illustration of the field values, not an
instruction to implement it now.

```markdown
Objective:
Add a trusted local StrategyProtocol with exactly one consumer.

Target domain:        13 — Strategy interface
Stage cap:            Stage 1 (one versioned strategy, one declared-data path)
Complexity budget:    B1 (max 4 new modules, 1 runtime dep, 0 services,
                      1 provider/implementation, 0 persistent stores)
Current stable stop:  R3 (only after the human R3 gate is recorded PASS)
Target stop:          R4 candidate

In scope:
- one versioned StrategyProtocol whose output is limited to Signal /
  TargetPosition / TradeProposal
- one consumer wiring it to the existing deterministic backtest path

Non-goals:
- strategy registry, plugin system, or parameter migration (Stage 3)
- a second market or a second baseline (Stage 2)
- strategy access to credentials, providers, network, or order APIs (Stage 5)

Entry gate:
Recorded human R3 promotion PASS and maintainer merge decision.

Runnable:
.venv\Scripts\pytest.exe -m contract tests/... produces a deterministic
strategy-to-order-to-result path on the existing synthetic fixture.

Testable:
Declared-data enforcement, determinism/version-hash stability,
unsupported-market rejection, and a negative test proving no I/O, credential,
or order access. Matches scope-ladder.md section 4 row 13.

Maintainable:
Research owner. Regression test for the version hash. Updates to
implementation-matrix.md row 13 and docs/architecture/domain-contracts.md.
Re-review triggered by any change to the domain event contracts.

Stoppable:
A protocol plus one consumer is a complete, useful, non-advertised contract.
Rollback deletes the protocol module and its consumer, leaving the R3
fixed-order engine fully usable. No baseline registry scaffolding is created.
```

## 4. Relationship to the ladders

This template does not define stages. It binds a task to the stages that already
exist:

| Question | Authority |
| --- | --- |
| How far may this domain go? | [`scope-ladder.md`](../roadmap/scope-ladder.md) section 3 |
| What evidence does this cell require? | [`scope-ladder.md`](../roadmap/scope-ladder.md) section 4 |
| Who may approve promotion? | [`scope-ladder.md`](../roadmap/scope-ladder.md) section 5 |
| Is this a valid place to stop? | [`release-ladder.md`](../roadmap/release-ladder.md) |
| What is actually built right now? | [`implementation-matrix.md`](../status/implementation-matrix.md) |
| Which commands can I actually run? | [`CLAUDE.md`](../../CLAUDE.md) section 3 |

Changing a stage boundary, gate, owner, or stopping point is a separate task
against the ladder documents. It is never a side effect of an implementation
task.
