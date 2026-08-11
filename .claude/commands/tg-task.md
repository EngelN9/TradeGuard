---
description: Start one scope-capped TradeGuard increment bound to the scope and release ladders
argument-hint: <one-sentence objective>
---

Start one independently reviewable TradeGuard increment for this objective:

**$ARGUMENTS**

Do not edit any file until the maintainer confirms the scope contract you
produce in step 3.

## Step 1 — Read current reality

Read these before anything else. Do not rely on memory or on a previous session.

1. `CLAUDE.md` and `AGENTS.md`.
2. `docs/status/implementation-matrix.md` — the current stable stop, what is
   `IMPLEMENTED`, and the blocker register.
3. `docs/roadmap/scope-ladder.md` — locate the domain row this objective belongs
   to, and read that row's stage cells, complexity budget, and section 4
   acceptance evidence.
4. `docs/roadmap/release-ladder.md` — the entry gate and stopping rules for the
   relevant stop.
5. The relevant source, tests, schemas, configuration, ADRs, and evidence.

## Step 2 — Repository Reality Check

Report branch, base, and uncommitted changes. If `git` fails with
`detected dubious ownership`, say plainly that git is unavailable and repository
state is unverified, and do not infer state from file timestamps.

## Step 3 — Produce the scope contract and stop

Fill every field of the contract in `docs/ai/claude-code-task-template.md`
section 2, in particular:

- target domain row number and name;
- stage cap, and what that makes a non-goal;
- complexity budget `B0`–`B5` with the concrete maxima;
- current stable stop and target stop, taken from the implementation matrix;
- entry gate, and whether it is actually satisfied;
- the four mandatory acceptance fields — **Runnable, Testable, Maintainable,
  Stoppable** — each with concrete commands, test paths, an owner, and rollback
  steps.

If the objective exceeds the stage cap or the budget, say so here: propose the
smallest independently useful authorized slice, mark the remainder `LATER`,
`OPTIONAL`, `BLOCKED`, or `OUT OF SCOPE`, and do not plan placeholders that
imply the deferred capability.

If the entry gate is unmet, report `BLOCKED` with the exact unblock condition
and its named authority, and stop.

Then **stop and wait for confirmation.**

## Step 4 — After confirmation

Implement only the confirmed slice. Validate with the commands in `CLAUDE.md`
section 3. Report the `AGENTS.md` §8 fields and end with an explicit promotion
gate result: `PASS`, `FAIL`, or `BLOCKED`.

Do not commit, push, merge, tag, open a pull request, connect to a provider, or
set a connected-test opt-in variable. Those are the maintainer's actions.
