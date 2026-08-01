# ADR 0002: Twelve Data equity adapter with blocked promotion

- Status: Provider and licensing decision approved; promotion blocked
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

The maintainer has approved the Basic plan, an individual account,
`internal_non_display` use, and the `internal_use_only` classification. The
reviewed account metadata records 8 API credits per minute, 800 credits per day,
and entitlement to `AAPL` daily historical bars through `/time_series`.
Provider responses remain authoritative at runtime, and no successful connected
observation has yet been made.

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
- reviewed Basic metadata of 8 API credits per minute and 800 per day;
- approved individual internal non-display research use;
- sanitized non-reconstructable or deterministic synthetic provider-shaped
  public fixtures only.

Disabled scope:

- query-string credentials;
- configurable base URLs or unallowlisted endpoints;
- batch and WebSocket access;
- `/exchange_schedule`, `/dividends`, and `/splits`;
- quotes, corporate actions, adjusted or total-return claims;
- broker/account/order/position/balance/OAuth capabilities;
- provider fallback, stale-cache substitution, and synthetic connected PASS;
- public display and redistribution of provider market values.
- any display of actual Twelve Data market values on the public dashboard.

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
| Exact Twelve Data plan name | `Basic` |
| Account owner type | `individual` |
| Intended use | `internal_non_display`; `APPROVED` |
| License/use classification | `individual internal-use-only` |
| Reviewed API entitlement | 8 credits/minute; 800/day; `/time_series`; `AAPL`; `1day`; historical daily bars |
| Runtime connected observation | `NOT_RUN` |
| Public display permission | `FALSE`; prohibited |
| Redistribution permission | `FALSE` |
| Raw connected response publication | `PROHIBITED` |
| Raw connected response retention | `transient_only` |
| Sanitized non-reconstructable fixtures | `ALLOWED` |
| Synthetic fixtures | `ALLOWED` |
| Checksums/manifests without raw market values | `ALLOWED` |
| Terms version reviewed | 2026-01-01 |
| License review date | 2026-07-31 |

The account/use, API-entitlement metadata, licensing, retention,
redistribution, public-display, and fixture decisions are human-approved. They
permit offline implementation and public-safe evidence under the restrictions
above. They do not substitute for a successful connected qualification.

## Connected-session review

The release-candidate `XNAS`/`XNGS` dates and exact open/close instants remain
pending human review. The machine-readable registry is deliberately:

```json
{
  "status": "PENDING_REVIEW",
  "reviewed_by": null,
  "reviewed_at": null,
  "sessions": []
}
```

Only explicit human-reviewed content with top-level `status: APPROVED` is
eligible for connected qualification. Provider responses, online calendars, or
package calendars must never change that state automatically.

## Connected state machine

- no opt-in: `SKIP_NOT_OPTED_IN`;
- opt-in without credential: `BLOCKED_MISSING_CREDENTIAL`;
- HTTP 401: `BLOCKED_INVALID_CREDENTIAL`;
- HTTP 403: `BLOCKED_ENTITLEMENT`;
- HTTP 429 after one retry: `BLOCKED_RATE_LIMIT`;
- timeout or 5xx: `BLOCKED_PROVIDER_UNAVAILABLE`;
- missing reviewed session: `BLOCKED_MARKET_CALENDAR`;
- provider schema drift: `FAIL_SCHEMA_DRIFT`;
- invalid canonical data or fewer than five completed sessions:
  `FAIL_DATA_QUALITY`;
- at least five completed reviewed sessions with valid manifest and admissible
  quality report: `PASS`.

General CI may safely skip and record `passed=false` and
`provider_contacted=false`. Release promotion requires `PASS`; a `SKIP`,
`BLOCKED`, or `FAIL` result never promotes.

## Public fixture and evidence policy

A connected response may be retained transiently in memory only long enough to
validate and hash it, after which the raw response must be discarded. Raw
connected responses must never be published. Public evidence may contain only:

- a sanitized non-reconstructable provider-shaped fixture;
- a deterministic synthetic provider-shaped fixture;
- schemas and field types;
- counts, session dates, request template without a key, and checksums;
- manifest and quality status;
- terms/license review metadata;
- `raw_market_values_persisted=false`;
- `raw_market_values_published=false`.

Actual provider prices, volumes, credentials, request headers, private account
data, and private quota-consumption telemetry must not be committed. The
human-reviewed 8-per-minute and 800-per-day release metadata may be recorded.

## Consequences

Offline contract and schema-drift qualification can proceed reproducibly. A
connected observation remains separately opted in, bounded, and truthfully
blocked if credentials, entitlement, calendar review, schema, or data quality
are not acceptable.

The adapter cannot support total-return research until a separately approved
point-in-time corporate-action source is implemented. It cannot support
execution-quality claims or automatically switch to another provider.

If the plan, account type, intended use, license classification, retention
policy, redistribution rights, display mode, or dashboard behavior changes,
licensing review and this ADR must be repeated before use.

## Promotion blockers

Prompt 4 implementation may complete while the promotion gate remains
`BLOCKED`. Before promotion, a maintainer must:

1. human-review exact release-candidate XNAS/XNGS sessions and mark the registry
   `APPROVED`;
2. locally set the data-only credential without persisting or disclosing it;
3. explicitly opt in;
4. run one minimal release-candidate connected smoke and obtain `PASS` with at
   least five completed sessions;
5. review the redacted connected evidence;
6. explicitly approve promotion.

Until every condition is satisfied, Prompt 4 promotion remains `BLOCKED`.

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
