# Research, risk, monitoring, and promotion policy

Status: `NORMATIVE`

This document is the durable minimum contract for research claims and any move
toward paper or shadow operation. The scope ladder decides when each capability
may be implemented; this document does not claim that it exists today.

## Deterministic backtesting

Same data, strategy version, configuration, seed, costs, and execution model
must produce the same result. Events are processed only when their content was
knowable. The engine rejects look-ahead, label/feature/corporate-action/future-
universe leakage, same-close signal/fill, ideal high/low fills, and use before
arrival.

Execution becomes more detailed only by stage. When supported, it explicitly
models market/limit orders, partial and non-fill, rejection, latency, spread,
commission/tax/fees, slippage, impact, minimum notional, tick/step/lot rules,
halt/maintenance, and queue uncertainty. Defaults are conservative; a limit
order does not fill without a crossing and orders do not receive unexplained
price improvement.

Equity and crypto cost/fill models are separate. Every report lists modeled and
unmodeled costs. Incomplete costs produce a conspicuous limitation and cannot
support a stronger promotion claim.

## Strategy specification and baselines

Each strategy declares ID/version, supported asset class and instruments,
required fields/frequency, warm-up, holding horizon, expected turnover,
parameter schema, random seed where applicable, costs, risks, failure
conditions, unsuitable markets, and known limitations.

Baselines exist to test the research pipeline, not to claim an edge. Add one
transparent baseline for one vertical slice before adding a second market or a
family of strategies. Trusted local code is the only initial execution model.
Arbitrary uploaded Python is not safely sandboxed and remains prohibited until
separate process/container isolation is implemented and reviewed.

## Validation progression

No strategy advances because of one favorable backtest or win rate. Validation
is added progressively but, before a strategy-level research claim, includes
the applicable:

- cash and buy-and-hold benchmark plus a documented market baseline;
- prior strategy version where one exists;
- immutable training, validation, test, untouched out-of-sample, and live-like
  intervals;
- fixed or walk-forward splits with train/validation/test dates, refit rule,
  selected parameters, failed splits, aggregation, and regime;
- parameter, start/end date, universe, fee/slippage, delay, missing-data,
  partial-fill, liquidity, provider, and extreme-market sensitivity;
- experiment count, search budget, multiple-testing warning, bootstrap or block
  bootstrap where statistically appropriate;
- purging, embargo, deflated Sharpe, probability of backtest overfitting,
  combinatorial purged cross-validation, White's Reality Check, or complexity
  penalty only at a stage whose assumptions and maintenance are justified.

Every statistical method documents assumptions, applicability, parameters,
limits, and failure conditions. Repeated tuning on a test/OOS set permanently
contaminates that evidence; renaming the interval does not restore it.

Validation statuses are `PASS`, `CONDITIONAL`, `FAIL`, and
`INSUFFICIENT_EVIDENCE`. `FAIL` and `INSUFFICIENT_EVIDENCE` cannot promote.

## Metrics and interpretation

A mature strategy report includes, when meaningful: cumulative and annualized
return/volatility, Sharpe, Sortino, Calmar, maximum drawdown and duration, VaR,
Expected Shortfall, win rate, profit factor, average gain/loss, payoff, turnover,
trades, holding period, exposure/concentration, gross/net-of-cost results,
benchmark-relative return, beta/alpha, tail behavior, worst day/week/month,
loss streaks, regimes, symbols, and time contributions.

Metrics may be staged; absence is explicit. Win rate, standard deviation,
normal VaR, a single Sharpe, interval, or covariance estimate is never
sufficient on its own.

## Independent risk engine

The risk engine is independent of strategies. Applicable research/paper checks
cover single-symbol/sector/theme/venue/quote exposure, gross/net exposure,
leverage (which must remain zero in the supported envelope), liquidity,
participation, impact, maximum order/capital/turnover/trade risk, concentration,
drawdown, stale data, market session, precision, and notional.

Portfolio analysis grows by stage to volatility/covariance/shrinkage,
correlation, factor/cluster/sector exposure, stress/scenario analysis,
liquidity-adjusted risk, venue/stablecoin/currency risk, and estimation/model/
parameter uncertainty. It must consider fat tails, volatility clustering,
correlation breakdown, gap risk, liquidity collapse, and venue failure.

Limits are versioned, schema-validated, hashed, audited, and fail closed. Risk
configuration failure or unknown market/account state cannot increase risk.

## Paper, shadow, reconciliation, and drift

Paper results are always labeled simulated. As their stages become current,
paper monitoring covers data freshness, signals, targets, simulated orders and
fills, positions, cash, realized/unrealized PnL, drawdown, exposure, rejections,
partial/non-fill, health, and alerts.

Shadow may compare theoretical strategy decisions, paper decisions, observable
market prices/spread/liquidity/slippage, and explicitly approved read-only
account state. It cannot place orders.

When account or external paper data exists, reconciliation covers cash,
balances, positions, open orders, fills, fees, realized/unrealized PnL, and
session/settlement status. States are exactly `MATCHED`, `MISMATCHED`,
`UNKNOWN`, `STALE`, and `UNAVAILABLE`. The latter four cannot be presented as
healthy or allow promotion.

Drift may cover data, feature, signal, position, PnL, cost, slippage, latency,
fill rate, regime, parameter, and strategy version. Every alert records baseline,
current value, threshold, window, severity, possible causes, and recommended
action. A drift result never directly raises risk.

## API and dashboard authority

The backend owns authoritative data, validation, risk, reconciliation, and
audit results. The dashboard is a projection and cannot recompute or override
them. It stores no secret and calls no provider/broker directly.

Pages and endpoints are added only as their backing domain becomes current.
Every surface displays environment and unknown/stale/failure states. High-risk
writes are schema-validated, authenticated/authorized when introduced,
audited, and idempotent where applicable. No live order, withdrawal, transfer,
risk-bypass, or evidence-deletion endpoint exists.

## Promotion gates

The research lifecycle is:

```text
IDEA -> RESEARCH -> BACKTEST -> ROBUSTNESS -> OUT_OF_SAMPLE
     -> REPLAY -> PAPER -> SHADOW
```

`SHADOW` is the maximum and is not automatic. The broad gate requirements are:

- Research to backtest: specification, data, benchmark, assumptions, failure
  conditions, initial costs, and look-ahead controls.
- Backtest to robustness: reproducible manifest, complete ledger, benchmark,
  data quality, costs, and no material leakage/survivorship defect.
- Robustness to OOS: parameter/cost/time/universe/regime sensitivity, stress,
  and an applicable overfitting assessment.
- OOS to paper: untouched data, acceptable documented drawdown/tails/turnover/
  liquidity, explicit limits, halt and rollback conditions.
- Paper to shadow: sufficient human-defined observation period, stable data,
  realistic simulation limits, no unresolved reconciliation defect, usable
  alerts/drift, incident procedure, and human approval.

Promotion records include ID, strategy/version, from/to stage, evidence,
approver, UTC time, conditions, expiry, and rollback conditions. An agent or
automated check cannot be the approver.

## Reports, alerts, and incidents

A formal research report states executive conclusion, hypothesis, market and
point-in-time universe, sources and licensing, data quality, logic/parameters,
benchmarks, costs/fills, in/out-of-sample and walk-forward evidence, robustness,
stress/risk/regime/capacity/liquidity, favorable/adverse results, limitations,
failure conditions, promotion recommendation, manifest, Git SHA, and hashes.

Alert levels are `INFO`, `WARNING`, `HIGH`, and `CRITICAL`. Critical conditions
include unknown/unreconciled accounts, suspected bad data, unauthorized trading
capability, secret exposure, immutable data/audit loss, risk bypass, or
environment mislabeling. `CRITICAL` blocks new proposals and promotion.

A material incident stops affected work, preserves data/log/events/config/
versions, builds a timeline and impact assessment, marks contaminated runs,
creates a minimal reproduction and regression test, completes root-cause
analysis, updates controls/runbooks, and resumes only after human review.
Evidence is never deleted to reduce apparent impact.

## Completion is stage-specific

There is no single all-or-nothing MVP. Each stop in
`docs/roadmap/release-ladder.md` is a valid maintained product boundary. A stage
is complete only when its explicit acceptance evidence passes; future stages do
not become required merely because they are documented.
