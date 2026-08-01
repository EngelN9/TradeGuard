# ADR 0003: Coinbase Advanced Trade public crypto adapter

- Status: Accepted with promotion blocked
- Date: 2026-07-31
- Decision owner: EngelN9
- Target release: v0.1.0

## Context

ADR 0001 selected Coinbase Advanced Trade public REST and WebSocket market data
for Prompt 5. TradeGuard needs real-provider contracts without introducing an
account, credential, order, transfer, withdrawal, derivatives, leverage, or
live-trading surface.

Coinbase's Advanced Trade overview says the `/market/...` endpoints do not
require authentication. The generated endpoint reference pages still show an
`Authorization` example. This implementation treats the overview's explicit
public endpoint table and the public WebSocket channel table as the authority.
An authentication challenge from a public endpoint is a scope failure, not a
reason to add a key.

Coinbase's current developer and market-data terms allow limited personal or
entity research use but restrict sharing, storage, redistribution, excessive
requests, and benchmarking. Public repository fixtures therefore contain
deterministic synthetic values only. A connected observation may hash raw bytes
in memory but may not retain or publish them.

## Decision

Implement one provider-neutral `CryptoMarketDataAdapter` and one Coinbase
implementation with these boundaries:

- `BTC-USD` spot only;
- public unauthenticated HTTPS GET only;
- REST host `api.coinbase.com`;
- REST paths limited to server time, the BTC-USD product, one-minute candles,
  and public market trades/ticker;
- WebSocket host `advanced-trade-ws.coinbase.com`;
- channels limited to `heartbeats`, `market_trades`, `status`, and `ticker`;
- no `jwt`, `Authorization`, cookie, user channel, private host, or automatic
  provider fallback;
- at most ten REST records per request;
- exactly one bounded retry for HTTP 429;
- WebSocket reconnect backoff of one, two, then four seconds;
- at most three reconnects and twenty observed messages per smoke;
- raw connected payloads are transient only.

The canonical trading-pair metadata binds:

- base asset `BTC`;
- quote asset `USD`;
- `price_increment` to tick size;
- `base_increment` to step and lot size;
- `base_min_size` to minimum quantity;
- `quote_min_size` to minimum notional;
- REST product status and flags to an explicit `ONLINE` or `NOT_TRADABLE`
  result;
- the observation time to `known_at` and `metadata_timestamp`.

WebSocket envelope sequence numbers are tracked per channel. A missing,
duplicate, decreasing, or skipped sequence is never repaired or inferred.
Schema drift, stale messages, heartbeat gaps, and REST/WebSocket metadata
conflicts emit a quarantined `DataQualityAlert` and set the stream
`NOT_TRADABLE`. Reconnection starts a fresh subscription and sequence boundary,
but an alert in the qualification run remains disqualifying.

## Public evidence policy

Allowed:

- strict schemas;
- deterministic synthetic provider-shaped fixtures;
- fixture checksums;
- normalized manifest and quality checksums;
- event counts, status, reconnect count, and backoff schedule;
- redacted PASS, FAIL, BLOCKED, or SKIP evidence.

Prohibited:

- captured Coinbase prices, sizes, books, trades, candles, or raw messages;
- account or portfolio identifiers;
- credentials or JWTs;
- public display or redistribution claims;
- describing fixture replay as a connected PASS.

## Consequences

Offline tests can reproduce REST normalization, WebSocket lifecycle behavior,
sequence rejection, reconnect, resubscription, stale handling, and controlled
shutdown without network access. The adapter remains useful for research
qualification while having no way to inspect an account or submit an order.

The narrow pair and record bounds are intentional. Expanding products,
channels, retention, display, or redistribution requires a new review. Additive
provider fields are tolerated at REST only when all required semantics still
validate; missing or type-changed required fields fail closed. WebSocket
envelopes and selected channel payloads are strict because sequence and
tradability depend on them.

## Promotion gate

Implementation is complete, but promotion remains `BLOCKED` until:

1. the maintainer rechecks the Coinbase Developer Platform Terms and Market
   Data Terms for the intended deployment and jurisdiction;
2. one explicitly opted-in release-candidate smoke obtains a complete public
   REST and WebSocket `PASS`;
3. the redacted evidence is reviewed;
4. the maintainer explicitly approves promotion.

The current committed connected result is `SKIP_NOT_OPTED_IN`. No provider was
contacted.

## Review triggers

Re-review on any:

- endpoint, host, public-authentication, channel, or sequence semantic change;
- terms, retention, display, redistribution, or geographic availability change;
- new product, quote asset, or venue;
- higher REST/stream bounds or reconnect policy;
- request for accounts, orders, credentials, transfers, withdrawals,
  derivatives, leverage, fallback, canary, or live behavior.

## Sources reviewed

- [Advanced Trade REST endpoint table](https://docs.cdp.coinbase.com/coinbase-app/advanced-trade-apis/rest-api)
- [Advanced Trade WebSocket guide](https://docs.cdp.coinbase.com/coinbase-app/advanced-trade-apis/guides/websocket)
- [Advanced Trade WebSocket channels](https://docs.cdp.coinbase.com/coinbase-app/advanced-trade-apis/websocket/websocket-channels)
- [Advanced Trade WebSocket rate limits](https://docs.cdp.coinbase.com/coinbase-app/advanced-trade-apis/websocket/websocket-rate-limits)
- [Coinbase Developer Platform Terms](https://www.coinbase.com/legal/developer-platform/terms-of-service)
- [Coinbase Market Data Terms](https://www.coinbase.com/legal/market_data)

## Rollback

Disable or remove the Coinbase adapter and connected runner, retain adverse
evidence, invalidate affected qualification results, and continue with offline
synthetic crypto data. Rollback must not add authentication, use a private
endpoint, switch provider, infer missing stream events, or rewrite evidence.
