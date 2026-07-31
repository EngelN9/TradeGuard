# ADR 0002: Twelve Data equity adapter with blocked promotion

- Status: Accepted with conditions
- Decision date: 2026-07-31
- Decision owner: EngelN9
- Implementation target: Prompt 4 / TG-004 / v0.1.0
- Promotion gate: `BLOCKED`

## Context

Prompt 4 requires one provider-neutral equity market-data protocol and one
human-approved connected implementation. The maintainer approved Twelve Data
for implementation subject to narrow technical, licensing, evidence-retention,
and connected-test conditions.

The provider's current documentation recommends the
`Authorization: apikey ...` header, documents standardized 401, 403, 429, and
5xx errors, and states that rate limits depend on the account plan. The account
dashboard and response headers remain authoritative; public pricing text is not
treated as proof of this account's entitlement.

The provider's terms dated 2026-01-01 limit use by subscription tier and require
separate authorization for redistribution or external display. Individual plan
guidance describes personal/internal use and prohibits redistribution and
commercial display to third parties. Therefore a public source repository may
contain adapter code, schemas, hashes, and deterministic synthetic provider-shaped
fixtures, but no captured Twelve Data market values.

## Decision

Implement Twelve Data as v0.1.0's only equity provider with
`APPROVED_WITH_CONDITIONS`.

Enabled scope:

- United States listed common stock;
- initial and only connected symbol: `AAPL`;
- accepted MIC values: `XNAS` and `XNGS`;
- `GET https://api.twelvedata.com/time_series`;
- `1day`, `outputsize <= 10`, `adjust=none`;
- authenticated only by `TRADEGUARD_TWELVE_DATA_API_KEY` in the
  `Authorization` header;
- one request with at most one retry, only after HTTP 429;
- internal/personal non-display research use;
- sanitized, deterministic, provider-shaped public fixtures only.

Disabled scope:

- query-string credentials;
- configurable base URLs or unallowlisted endpoints;
- batch and WebSocket access;
- `/exchange_schedule`, `/dividends`, and `/splits`;
- quotes, corporate actions, adjusted or total-return claims;
- broker/account/order/position/balance/OAuth capabilities;
- provider fallback, stale-cache substitution, and synthetic connected PASS;
- public display and redistribution of provider market values.

Daily timestamps are interpreted as exchange-local session dates and are mapped
to UTC only through TradeGuard's reviewed deterministic MIC registry. An unknown
date is `BLOCKED_MARKET_CALENDAR`; it is never inferred to be open.

The adapter declares the feed as unsuitable for NBBO, consolidated-volume,
execution, fill, or best-execution claims. Corporate actions are explicitly
unsupported. Unadjusted data carries a warning, and a large unexplained overnight
discontinuity is quarantined without inferring a split ratio.

## Account and licensing record

The following fields are deliberately explicit rather than inferred:

| Field | Current record |
| --- | --- |
| Execution jurisdiction | Taiwan |
| Exact Twelve Data plan name | `UNCONFIRMED` |
| Account owner type | `UNCONFIRMED` (`individual` or `business`) |
| Intended use | `internal_non_display` |
| License/use classification | `UNCONFIRMED_PENDING_ACCOUNT_REVIEW` |
| Public display permission | `NOT_CONFIRMED`; prohibited by default |
| Redistribution permission | `FALSE` |
| Raw market values in public repository | `FALSE` |
| Terms version reviewed | 2026-01-01 |
| License review date | 2026-07-31 |

These unresolved fields do not block offline implementation. They do block
release promotion and any claim that the connected qualification has passed.

## Connected state machine

- no opt-in: `SKIP_NOT_OPTED_IN`;
- opt-in without credential: `BLOCKED_MISSING_CREDENTIAL`;
- HTTP 401: `BLOCKED_INVALID_CREDENTIAL`;
- HTTP 403: `BLOCKED_ENTITLEMENT`;
- HTTP 429 after one retry: `BLOCKED_RATE_LIMIT`;
- timeout or 5xx: `BLOCKED_PROVIDER_UNAVAILABLE`;
- missing reviewed session: `BLOCKED_MARKET_CALENDAR`;
- provider schema drift or invalid canonical data: `FAIL`;
- at least five completed reviewed sessions with valid manifest and admissible
  quality report: `PASS`.

General CI may safely skip and record `passed=false` and
`provider_contacted=false`. Release promotion requires `PASS`; a `SKIP`,
`BLOCKED`, or `FAIL` result never promotes.

## Public fixture and evidence policy

A connected capture may be validated and hashed in memory, but public evidence
must contain only:

- a deterministic sanitized provider-shaped response;
- schemas and field types;
- counts, session dates, request template without a key, and checksums;
- manifest and quality status;
- terms/license review metadata;
- `raw_payload_retained=false`;
- `raw_payload_published=false`.

Actual provider prices, volumes, credentials, request headers, account quota
details, and private account data must not be committed.

## Consequences

Offline contract and schema-drift qualification can proceed reproducibly. A
connected observation remains separately opted in, bounded, and truthfully
blocked if credentials, entitlement, calendar review, schema, or data quality
are not acceptable.

The adapter cannot support total-return research until a separately approved
point-in-time corporate-action source is implemented. It cannot support
execution-quality claims or automatically switch to another provider.

## Promotion blockers

Prompt 4 implementation may complete while the promotion gate remains
`BLOCKED`. Before promotion, a maintainer must:

1. record the exact account plan;
2. record whether the account is individual or business and confirm its use;
3. confirm the applicable license/use classification;
4. confirm whether any display is allowed (default remains no);
5. approve the connected MIC session window;
6. run the connected smoke once for the release candidate and obtain `PASS`.

## Official sources reviewed

- [Twelve Data API quickstart and error model](https://twelvedata.com/docs/introduction/quickstart)
- [Twelve Data terms of use](https://twelvedata.com/terms)
- [Twelve Data individual pricing](https://twelvedata.com/pricing)
- [Twelve Data commercial and personal usage](https://support.twelvedata.com/en/articles/5332349-commercial-and-personal-usage)
- [Twelve Data US equities coverage](https://support.twelvedata.com/en/articles/9935903-us-equities-market-data)
- [Twelve Data timezone behavior](https://support.twelvedata.com/en/articles/5745849-timezones)

## Rollback

Disable or remove the Twelve Data adapter and its connected runner, retain all
adverse evidence, and invalidate affected qualification results. Do not
activate a fallback provider and do not delete audit or BLOCKED/FAIL records.
