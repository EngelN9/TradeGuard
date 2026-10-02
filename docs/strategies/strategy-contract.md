# Trusted-local strategy contract

Status: `R4 CANDIDATE / NOT PROMOTED / NOT TRADABLE`

The R4 candidate adds one deliberately narrow strategy seam. It is an offline
research caller of the promoted R3 simulator, not an order system, risk
approval, provider adapter, plugin framework, or Python security sandbox.

## Public contract

`StrategyProtocol` exposes an immutable specification and three lifecycle
methods: `initialize`, `on_event`, and `finalize`. A strategy receives only an
immutable `StrategyContext` and `StrategyBar`. The bar projection contains:

- asset class, venue, and symbol;
- completed-bar event time and sequence number;
- close price.

It contains no full dataset, volume, future bar, provider client, network
handle, credential, broker, risk configuration, mutable evidence store, or
external order endpoint. The only permitted outputs are `Signal`,
`TargetPosition`, and `TradeProposal`.

The CLI constructs the single repository-owned baseline directly. There is no
dynamic import, package upload, registry framework, or arbitrary strategy
execution path. Trusted local Python remains able to misuse host capabilities
if a maintainer changes it; this contract is scope isolation, not a sandbox.

## Research-only compilation

`ResearchPlanCompiler` maps exactly one `TradeProposal` to exactly one
`PlannedOrder` for the existing R3 offline simulator. The mapping changes no
side, quantity, order type, price, decision time, submission time, or sequence.
It is not a `RiskDecision` and cannot reach paper or external order APIs.

The compiled order is sequenced after the completed bar that caused the
proposal. R3 therefore cannot fill it at that same close. Unknown markets,
unapproved data fields, invalid quality, output-time conflicts, invalid output
types, identity conflicts, and checksum conflicts fail closed before an
artifact is written.

## Commands and artifacts

```text
tradeguard strategy run DATASET.json REQUEST.json ARTIFACT.json
tradeguard strategy inspect ARTIFACT.json
```

The run artifact binds the frozen specification and parameters, strategy hash,
dataset manifest, output events, generated plan, R3 artifact, synthetic report,
and its own checksum. Recomputing only an outer checksum cannot repair a broken
semantic binding.

Evidence is under `artifacts/evidence/r4/`. Every file is synthetic-only and
`NOT_EVALUATED`; none is connected, investment, profitability, validation, or
promotion evidence.

## Rollback

Remove the strategy package, strategy CLI route, strategy schemas, and R4
evidence. The R3 fixed-order `backtest` and `replay` commands and their artifacts
remain unchanged and independently usable.
