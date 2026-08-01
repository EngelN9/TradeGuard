# Deterministic backtest and replay engine

Status: `IMPLEMENTED / HUMAN PROMOTION REVIEW REQUIRED`

TradeGuard Prompt 6 provides an offline, fixed-order simulation engine. It is a
research component, not a strategy, broker, account connector, or indication
that any simulated result can be achieved in a real market.

## Scope and trust boundary

The engine accepts only:

- a self-contained `DatasetPackage` that passes the Prompt 3 quality gate with
  `PASS` or `WARN`;
- an immutable `BacktestPlan` containing explicit fixed orders;
- recorded runtime metadata for the `RunManifest`.

The engine has no network client, credential input, account state, external
order endpoint, `canary`, or `live` mode. Strategy generation is deliberately
deferred to Prompt 7. A `FAIL` or `QUARANTINED` dataset is rejected before any
simulation result is produced.

## Deterministic ordering

Bars, explicit orders, and point-in-time corporate actions use a stable total
order:

1. `event_time_utc`;
2. `ingest_time_utc`;
3. `sequence_number`;
4. reviewed event-kind priority;
5. canonical SHA-256 tie-breaker.

The result checksum covers the plan identity, dataset manifest identity, order,
fill, action, position and PnL ledgers, ending balances, conservation report,
and warnings. Workstation and wall-clock fields remain in the run manifest but
are intentionally outside this deterministic result checksum.

## Ledger rules

The portfolio ledger is cash-only and long-only. Money, prices, quantities,
fees, taxes, cost basis, balances and PnL use `decimal.Decimal`; binary floats
are rejected at model boundaries.

- Buys debit notional plus all explicit costs.
- Sells cannot exceed the held quantity and realize PnL net of costs.
- A duplicate `fill_id` is ignored and counted instead of applied twice.
- Splits and reverse splits preserve total cost basis.
- Cash dividends adjust cash and realized PnL in the base currency.
- Symbol changes move the position without duplicating it.
- Every result exposes ending asset and currency balances.
- Cash/equity and asset-quantity conservation must both pass or the run fails.

## Conservative fill model

A bar is eligible only when it is strictly future-knowable relative to the
order and the configured latency has elapsed. An order produced at a bar close
cannot fill on that same bar.

- Market buys use the future bar high; market sells use the future bar low.
- Limit orders fill only when the future bar crosses the limit, exactly at the
  limit, with no assumed price improvement.
- Bar participation is capped and rounded down to the reviewed lot/step size,
  so partial fills and non-fills are explicit.
- Tick size, quantity precision, minimum quantity/notional, equity sessions,
  halts and crypto maintenance are fail-closed gates.
- Unknown point-in-time metadata or session state rejects or blocks execution.

The model does not claim to reproduce queue position. Spread, slippage and
market impact are explicit adverse quote-currency costs for market orders,
instead of an unreviewable ideal-price adjustment.

## Separate market costs

`EquityCostModel` records commission, minimum commission, sell-side tax,
spread, slippage and market impact. `CryptoCostModel` records spot maker/taker
fees plus spread, slippage and market impact. The models have separate version
identifiers and are never selected by merely changing a symbol.

The defaults are intentionally conservative synthetic research assumptions.
They are not a representation of any broker, venue, jurisdiction or account.

## CLI and artifacts

```text
tradeguard backtest run DATASET.json PLAN.json ARTIFACT.json
tradeguard replay run DATASET.json PLAN.json ARTIFACT.json
tradeguard backtest inspect ARTIFACT.json
```

The artifact contains a bound `RunManifest` and `BacktestResult`, including:

- order and fill ledgers;
- corporate-action ledger;
- position ledger and PnL series;
- ending asset and currency balances;
- conservation report;
- deterministic result checksum;
- warnings and data/model version references.

JSON contracts are committed under `schemas/backtest/`. Synthetic review
evidence is committed under `artifacts/evidence/prompt6/`.

## Known limitations and human gate

- Only bar-based market and limit research fills are modeled.
- Queue position, order-book depth, FX conversion and borrowing are absent.
- The ledger is single-base-currency, cash-only and long-only.
- No strategy, benchmark, performance report or promotion decision is included.
- A bar model cannot establish real-world fillability.

Before Prompt 7, a human reviewer must inspect the ordering contract, same-close
rejection, partial-fill behavior, cost assumptions, split accounting,
maintenance rejection and conservation evidence. Prompt 6 remains unpromoted
until that review is explicitly recorded.

Rollback is a normal revert of the Prompt 6 model version. Previously generated
artifacts and checksums must remain available for audit and must not be rewritten.
