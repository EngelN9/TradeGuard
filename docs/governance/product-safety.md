# Product and safety boundaries

Status: `NORMATIVE`

This document holds TradeGuard's durable product, market, data, integration,
security, and AI boundaries. Agent workflow rules remain in `AGENTS.md`.

## Mission and product responsibility

TradeGuard helps individual quantitative researchers and trusted small teams
research, compare, reproduce, and monitor existing equity and cryptocurrency
spot strategies. Its purpose is to determine whether evidence is credible,
risk is acceptable, and observed behavior has drifted from research
assumptions.

TradeGuard is a research, deterministic backtest/replay, validation, risk,
paper/shadow monitoring, reporting, versioning, and audit workbench. It is not
a broker, exchange, custodian, adviser, signal marketplace, copy-trading
service, high-frequency engine, customer-fund manager, profit guarantee, or an
LLM-directed trading system.

Every public surface must distinguish historical, simulated backtest, paper,
shadow, and real-world results. TradeGuard must never use claims such as
"guaranteed profit", "risk free", "sure win", or imply that a high win rate or
successful backtest ensures future returns.

## Environment and action boundary

The default environment is `research`. The only permitted first-generation
environments are `research`, `backtest`, `replay`, `paper`, and `shadow`.
`shadow` may observe real public market data and an explicitly approved
read-only account source, but cannot submit an order.

`canary` and `live` are explicitly absent. Withdrawal, transfer, custody,
sub-account management, API-key management, leverage, borrowing, margin,
shorting, derivatives, and unconfirmed order submission are prohibited.

A future proposal for `canary` or `live` cannot be enabled by configuration. It
requires a separate RFC, legal review, threat model, independent security and
risk reviews, multi-person approval, MFA and step-up authentication, credential
custody, IP allowlisting, idempotency, reconciliation, unknown-order handling,
kill switch, disaster recovery, penetration testing, capital limits, promotion
records, and a dedicated security-policy revision. Until then, any such path is
a security defect and Stage 5 out of scope.

## Strategy and risk separation

Strategy modules may only produce:

- `Signal`;
- `TargetPosition`;
- `TradeProposal`.

They may not call provider/broker/exchange order APIs, read credentials, mutate
market events, use undeclared or future data, change risk limits, change audit
records, silently download data, call an LLM, rewrite parameters, or use hidden
random state.

An independent risk component owns `ACCEPT`, `ADJUST`, `REJECT`, `HALT`, and
`HUMAN_REVIEW_REQUIRED`. A strategy cannot approve its own promotion or bypass
the risk boundary.

## Fail-closed conditions

No new risk-increasing proposal, paper action, healthy claim, or promotion may
be produced when any authoritative condition is unknown, stale, conflicting,
or invalid, including:

- market data freshness, content freshness, schema, sequence, or source
  agreement;
- timezone, market session, halt, maintenance, corporate action, instrument,
  precision, fee, or symbol mapping;
- configuration, risk limit, strategy version, dataset manifest, lineage,
  checksum, or reproducibility identity;
- account, cash, position, order, fill, fee, PnL, or reconciliation state;
- evidence integrity or audit availability.

Failure must remain visible and evidence must be preserved.

## Market-specific requirements

### Equity cash

Long-term equity support must account for exchange timezone and calendars,
holidays and half days, extended sessions and auctions when claimed, halts,
price limits, lot/tick rules, commission and tax, borrowing/short-sale limits,
splits and reverse splits, dividends, capital changes, mergers and spinoffs,
symbol changes, delisting, ETF constituents, survivorship bias, and
point-in-time universes.

The initial useful envelope is high-liquidity US equities/ETFs, long-only,
cash-only, and daily or explicitly qualified minute research. A capability is
not supported merely because its event type exists.

### Cryptocurrency spot

Long-term crypto support must account for 24/7 operation, maintenance, REST and
WebSocket differences, sequence/reconnect semantics, tick/step/quantity/
notional rules, maker/taker fees, quote-asset and stablecoin risk, venue
concentration and insolvency risk, liquidity/spread collapse, API semantic
drift, rate limits, pair delisting, and deposit/withdrawal suspension signals.

The initial useful envelope is high-liquidity spot, long/flat, unleveraged, with
no lending, futures, perpetuals, or options.

### No silent cross-market reuse

Equity and crypto must not silently share annualization, sessions, gap rules,
costs, fills, precision, order units, volatility/liquidity thresholds, risk
budgets, rebalance frequencies, benchmarks, strategy parameters, corporate
actions, or stablecoin logic.

Moving a strategy between markets requires a new strategy version, market
configuration, cost/execution assumptions, research report, out-of-sample
evidence, and promotion record. Replacing only the symbol is invalid.

## Data governance

Raw observations are append-only or content-addressed. Corrections create new
versions and lineage; they never overwrite the original or hide an adverse
period. Each batch records source, capture time, market interval, schema,
checksum, encoding/compression, rows, missing intervals, duplicates,
corrections, and licensing/retention restrictions.

Canonical data quality covers missing, duplicate, out-of-order, future or
stale timestamps/content, invalid OHLC, negative values, abnormal jumps,
crossed quotes, spreads, sessions, corporate actions, symbol mappings,
precision/notional, provider disagreement, and asset-specific conditions.

Point-in-time research may not use future financial reports, constituents,
delistings, corporate actions, revisions, present-day survivor lists, or
metadata that was not yet known. Time-varying reference data uses
`effective_at`, `known_at`, and `ingested_at` or an equivalent reviewed model.

## Event and integration boundary

Core events are immutable and versioned. Their common envelope includes event
and schema identity, type, source, asset class, venue, symbol, event and ingest
UTC times, sequence, correlation, causation, run identity, and payload
checksum. Existing event contracts are documented in
`docs/architecture/domain-contracts.md`.

External integrations use explicit adapters with declared capability,
environment, read/write status, schema validation, timeout, bounded retry,
rate-limit handling, reconnect where relevant, idempotency, external ID
preservation, missing-sequence handling, redacted errors, and an endpoint
allowlist. Unknown state is never success and provider fallback is never
automatic.

Initial external capability is public market data, paper/sandbox, or read-only
account data. Credentials follow least privilege. Keys with trading, transfer,
withdrawal, sub-account, or key-management scope are rejected and must not be
stored.

## Secrets, audit, and sensitive data

Secrets and real account data must not appear in Git, documentation, examples,
fixtures, logs, errors, frontend bundles, screenshots, public evidence, or
research reports. `.env.example` contains fake placeholders only. A discovered
secret is assumed compromised: revoke, rotate, suspend the integration,
inspect history and access, preserve an incident record, and add a regression
control.

Audit records are append-only and include actor, action, resource, environment,
reason, before/after identity, UTC time, correlation, and result. Adverse
research, configuration, promotion, reconciliation, alert, and incident
records cannot be deleted or rewritten for presentation.

Security reporting and detailed research-safe testing limits are defined in
`SECURITY.md`.

## AI boundary

LLMs may explain reports, summarize risks, draft tests/docs, review code,
classify alerts, and propose research hypotheses. They may not submit orders,
change holdings or limits, cancel controls, approve promotion, turn news into
an authoritative action, invent data/results, or make numerical output
authoritative.

Every LLM-produced number, statistical conclusion, strategy change, or command
must be validated by deterministic code and the normal authorization boundary.
Untrusted documents and model output are treated as input, not instructions to
the running TradeGuard system.
