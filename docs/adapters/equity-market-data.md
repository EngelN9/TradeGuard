# Equity market-data adapter

TradeGuard v0.1.0 implements a provider-neutral
`EquityMarketDataAdapter` protocol and one restricted Twelve Data adapter. It
is a read-only market-data boundary. It has no broker, account, order, position,
transfer, withdrawal, `canary`, or `live` capability.

The binding decision and unresolved promotion blockers are in
[`ADR 0002`](../adr/0002-twelve-data-equity-adapter.md).

## Enabled capability

| Capability | v0.1.0 state |
| --- | --- |
| Provider | Twelve Data |
| Approval | `APPROVED_WITH_CONDITIONS` |
| Plan/account | Basic / individual |
| Intended use | Approved `internal_non_display`, `internal_use_only` |
| Authentication | Required, header only |
| Historical bars | AAPL, `1day`, unadjusted, at most 10 |
| Latest data | Latest completed daily bar |
| Quote | Disabled |
| Real-time/delayed | Entitlement-dependent; not claimed as enabled |
| Timezone | Provider metadata validated against `America/New_York` |
| Calendar | Internal human-approved XNAS/XNGS sessions only |
| Corporate actions | Explicitly unsupported |
| Fallback provider | None |
| Consolidated/NBBO/full volume/execution grade | Unsupported |
| Basic entitlement metadata | 8 credits/minute; 800/day |
| Public raw values | Prohibited |

The enabled endpoint is exactly:

```text
GET https://api.twelvedata.com/time_series
```

The adapter always sends `adjust=none`, uses a 10-second timeout, limits a
response to 1 MiB, and allows one retry only for HTTP 429. The retry delay is
bounded to two seconds. It never retries indefinitely or changes provider.

Only `AAPL` and MIC `XNAS`/`XNGS` are accepted. Symbols are trimmed and
uppercased before allowlist validation. The response must identify NASDAQ,
USD, `1day`, `America/New_York`, and `Common Stock`.

## Timestamp and calendar contract

Twelve Data's daily equity `datetime` is treated as the exchange-local session
date, not UTC midnight. TradeGuard resolves that date to exact reviewed session
open and close instants, then stores the canonical bar in UTC.

The connected registry is:

```text
configs/markets/equities_connected_sessions.json
```

It starts as `PENDING_REVIEW`. Unknown, unapproved, or missing
sessions produce `BLOCKED_MARKET_CALENDAR`; weekdays and holidays are never
guessed. A pending document cannot contain reviewer claims or session entries.
Only an explicit human-reviewed top-level `status: APPROVED` can unlock the
registry.

## Data quality and corporate actions

Provider data is parsed through a strict provider-specific schema and then
mapped to the canonical `OHLCVBar`; provider schema does not cross the domain
boundary. Decimal strings stay exact and all canonical timestamps are
timezone-aware UTC.

The Prompt 3 quality gate verifies manifest binding, count/checksum, timestamps,
OHLC, volume, order, duplicates, point-in-time metadata, and reviewed sessions.
Because corporate actions are disabled, an otherwise valid dataset is `WARN`.
A large unadjusted overnight discontinuity is `QUARANTINED` for manual
corporate-action review, and TradeGuard never invents a split ratio.

Consequently, v0.1.0 data cannot support adjusted-price, total-return, NBBO,
consolidated-volume, fill-quality, or execution-grade claims.

## Credentials and redaction

Connected access requires both:

```text
TRADEGUARD_RUN_CONNECTED_TESTS=1
TRADEGUARD_TWELVE_DATA_API_KEY=<data-only API key>
```

The key is sent only as:

```text
Authorization: apikey <redacted>
```

Do not put a key in a URL, file, log, fixture, command history, screenshot,
issue, pull request, or evidence bundle. Twelve Data API keys do not expose a
broker-style scope document, so TradeGuard constrains the key through the
program's host, method, endpoint, and capability allowlists.

## Offline qualification

The committed recorded fixture is provider-shaped but contains deterministic
synthetic financial values. It explicitly states:

```text
sanitized=true
values_are_deterministic_synthetic=true
raw_market_values_persisted=false
raw_market_values_published=false
redistribution_allowed=false
```

Run:

```bash
uv run pytest -m contract tests/contract/test_twelve_data_adapter.py
uv run python scripts/collect_prompt4_evidence.py
```

No command above contacts Twelve Data.

## Connected qualification

Connected tests are not part of default CI. The Basic plan, individual
account, internal non-display use, internal-use-only classification, no
redistribution, and no public display decisions are recorded in
`configs/adapters/twelve_data_equity.json`. Before opting in, the maintainer
must update and approve the exact session registry and provide the credential
through the environment.

Run at most once per release candidate:

```bash
TRADEGUARD_RUN_CONNECTED_TESTS=1 \
TRADEGUARD_TWELVE_DATA_API_KEY=... \
uv run python scripts/run_twelve_data_connected_smoke.py
```

The public result contains status, counts, checksums, manifest binding, and
quality state only—never raw market values or a credential. `SKIP`, `BLOCKED`,
and `FAIL` are not promotion successes.

## Failure map

| Condition | Result |
| --- | --- |
| No opt-in | `SKIP_NOT_OPTED_IN` |
| Opt-in, no key | `BLOCKED_MISSING_CREDENTIAL` |
| HTTP 401 | `BLOCKED_INVALID_CREDENTIAL` |
| HTTP 403 | `BLOCKED_ENTITLEMENT` |
| HTTP 429 after retry | `BLOCKED_RATE_LIMIT` |
| Timeout or 5xx | `BLOCKED_PROVIDER_UNAVAILABLE` |
| Unknown session date | `BLOCKED_MARKET_CALENDAR` |
| Schema mismatch | `FAIL_SCHEMA_DRIFT` |
| Invalid timestamp/OHLC/data or fewer than five completed sessions | `FAIL_DATA_QUALITY` |

Errors use fixed redacted messages. Provider request IDs may be logged; response
bodies, request headers, and keys may not.

## Licensing and retention

The current implementation classification is approved individual,
internal-use-only, non-display use. Public display and redistribution are
prohibited. The reviewed Basic metadata is 8 API credits per minute and 800 per
day; provider responses remain authoritative at runtime.

Raw connected bytes may be validated and hashed in memory but are not retained
or published by this adapter. The public repository contains only sanitized
synthetic fixtures, schemas, metadata, and hashes.

The public dashboard must not show actual Twelve Data market values. Any change
to plan, ownership, intended use, licensing, retention, redistribution, or
display mode requires a new human licensing review before use.
