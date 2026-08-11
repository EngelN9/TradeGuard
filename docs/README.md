# TradeGuard documentation map

This page is the entry point for durable repository documentation. Historical
prompt numbers are delivery references only; they do not define current scope.

## Start here

| Question | Authority |
| --- | --- |
| What does the public project do now? | [`README.md`](../README.md) |
| What may an AI coding agent do? | [`AGENTS.md`](../AGENTS.md) |
| What product and safety boundaries never move implicitly? | [`governance/product-safety.md`](governance/product-safety.md) |
| What engineering and evidence rules apply? | [`governance/engineering-standards.md`](governance/engineering-standards.md) |
| What validates research, risk, paper, and promotion? | [`governance/research-risk-and-promotion.md`](governance/research-risk-and-promotion.md) |
| What is implemented, blocked, or deferred? | [`status/implementation-matrix.md`](status/implementation-matrix.md) |
| How far may each domain expand? | [`roadmap/scope-ladder.md`](roadmap/scope-ladder.md) |
| What are the stable release stopping points? | [`roadmap/release-ladder.md`](roadmap/release-ladder.md) |
| How should a new Codex task be written? | [`ai/codex-task-template.md`](ai/codex-task-template.md) |
| How should a new Claude Code task be written? | [`ai/claude-code-task-template.md`](ai/claude-code-task-template.md) |
| How is Claude Code operated in this working copy? | [`CLAUDE.md`](../CLAUDE.md) |

## Architecture and current contracts

- [`architecture/system-context.md`](architecture/system-context.md): logical
  planes, trust boundaries, and current/candidate reality.
- [`architecture/domain-contracts.md`](architecture/domain-contracts.md):
  immutable events, configuration, and run manifests.
- [`data/data-foundation.md`](data/data-foundation.md): canonical data,
  point-in-time metadata, manifests, lineage, and quality.
- [`backtest/deterministic-engine.md`](backtest/deterministic-engine.md):
  promoted R3 fixed-order deterministic backtest/replay contract.
- [`adapters/equity-market-data.md`](adapters/equity-market-data.md): restricted
  Twelve Data equity adapter.
- [`adapters/crypto-market-data.md`](adapters/crypto-market-data.md): restricted
  Coinbase public REST/WebSocket adapter.

## Decisions and releases

- [`adr/0001-connected-release-scope.md`](adr/0001-connected-release-scope.md)
- [`adr/0002-twelve-data-equity-adapter.md`](adr/0002-twelve-data-equity-adapter.md)
- [`adr/0003-coinbase-public-crypto-adapter.md`](adr/0003-coinbase-public-crypto-adapter.md)
- [`release/connected-release-v1.md`](release/connected-release-v1.md): approved
  aggregate connected-release contract, now governed as a later ladder stop and
  not as the next all-or-nothing implementation batch.
- [`release/r3-promotion.md`](release/r3-promotion.md): recorded human R3
  promotion decision, exact reviewed head, evidence, conditions, and rollback.
- [`history/prompt-migration.md`](history/prompt-migration.md): historical
  Prompt 0–17 mapping and why the root prompt program was retired.

## Status vocabulary

Roadmap status uses exactly:

- `CURRENT`: implemented on the identified stable branch and maintained now;
- `NEXT`: the single smallest promotion or implementation slice;
- `LATER`: a defined stage that is not an active commitment;
- `OPTIONAL`: useful only if an explicit need and owner appear;
- `BLOCKED`: implementation/qualification exists or is desired, but a named
  external or human gate is unmet;
- `OUT OF SCOPE`: prohibited or deliberately excluded.

Implementation evidence uses `IMPLEMENTED`, `PARTIAL`, `MISSING`, or
`NOT APPLICABLE` as a separate axis. For example, an adapter can be
`IMPLEMENTED + BLOCKED` when offline contracts exist but connected
qualification is not approved.

## Maintenance rule

Update the implementation matrix when behavior changes. Update the scope or
release ladder only when a stage boundary, gate, maintenance owner, or stopping
point changes. Update an ADR when a previously accepted decision changes.
Do not put a one-time task transcript back into a normative root file.
