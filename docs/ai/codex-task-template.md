# Codex task template

Use this template for one independently reviewable TradeGuard increment. It is
a reusable task contract, not a sequence of mandatory roadmap prompts.

```markdown
You are working on TradeGuard.

Read completely before acting:

1. `AGENTS.md` and any narrower `AGENTS.md`.
2. `docs/README.md` and the linked governance sources relevant to this task.
3. `docs/status/implementation-matrix.md`.
4. `docs/roadmap/scope-ladder.md` and `docs/roadmap/release-ladder.md`.
5. The relevant source, tests, ADRs, schemas, configuration, and evidence.

Objective:
<one observable outcome>

Current stage and release stop:
<domain/stage and stable base>

Scope cap:
<maximum files/modules/providers/services/dependencies and one vertical slice>

In scope:
- <behavior 1>
- <behavior 2>

Non-goals:
- <explicit next/later/optional behavior>
- no live/canary/withdrawal/transfer/secret/account authority

Entry gate:
<evidence or human decision that must already exist>

Acceptance evidence:
- <focused unit/property/contract/replay test>
- <deterministic artifact/schema/report>
- <full applicable regression gates>

Failure and rollback:
<fail-closed state and return to last verified version>

Maintenance owner and promotion authority:
<human owner; never the agent>

Do not commit, push, merge, connect, tag, or publish unless this task explicitly
authorizes the exact action.

Before editing, report:
- Repository Reality Check
- Objective
- Assumptions
- Files expected to change
- Validation plan
- Risk impact
- Rollback approach

After completion, report:
- Summary
- Files Changed
- Behavior Changes
- Risk/Security Impact
- Tests Executed and exact results
- Evidence Generated
- Known Limitations
- Rollback Plan
- Deferred Scope
- Promotion Gate: PASS / FAIL / BLOCKED
```

## Sizing rule

If the task needs more than one new provider, service, persistent store,
strategy family, market, or promotion decision, split it. If no current user of
an interface exists, do not create the interface. If a stage can be useful and
maintained without its successor, stop there and request a separate task later.
