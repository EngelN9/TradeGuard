# Coinbase public cryptocurrency market data

## Status

`IMPLEMENTED / CONNECTED QUALIFICATION BLOCKED / NOT TRADABLE`

TradeGuard implements a provider-neutral `CryptoMarketDataAdapter` and one
narrow Coinbase Advanced Trade public-data adapter. Default CI is offline.
There is no account, credential, order, transfer, withdrawal, derivatives,
leverage, canary, or live path.

## Enabled capability

| Boundary | Enabled value |
| --- | --- |
| Provider | Coinbase Advanced Trade public data |
| Product | `BTC-USD` spot only |
| REST host | `api.coinbase.com` |
| WebSocket host | `advanced-trade-ws.coinbase.com` |
| Authentication | prohibited |
| REST endpoints | server time, product, one-minute candles, public ticker/trades |
| WebSocket channels | `heartbeats`, `market_trades`, `status`, `ticker` |
| REST rows | at most 10 |
| WebSocket messages per smoke | 4–20 |
| Reconnects | at most 3 |
| Backoff | 1, 2, then 4 seconds |
| Provider fallback | prohibited |
| Raw connected retention/publication | prohibited |

The machine-readable source is:

```text
configs/adapters/coinbase_crypto.json
```

## Public endpoint policy

The Advanced Trade REST overview explicitly says `/market/...` public endpoints
do not require authentication and recommends WebSocket for real-time data.
Generated endpoint reference pages currently include contradictory
`Authorization` examples. TradeGuard never resolves that contradiction by
adding a key. HTTP 401/403 from an approved public endpoint is a scope failure.

REST transport permits only HTTPS GET and rejects:

- every unapproved host or path;
- `Authorization`, cookie, and proxy-authorization headers;
- duplicate or unreviewed query parameters;
- response bodies over 1 MiB;
- more than one retry;
- any order, account, portfolio, payment, transfer, withdrawal, private product,
  or authenticated path.

Public REST data is cached by Coinbase unless bypassed. The adapter sends
`Cache-Control: no-cache` for bounded qualification observations, while
WebSocket remains the real-time path.

## Trading-pair metadata

Provider fields map as follows:

| Coinbase field | TradeGuard field |
| --- | --- |
| `base_currency_id` | base asset |
| `quote_currency_id` | quote asset |
| `price_increment` | tick size |
| `base_increment` | step size and lot size |
| `base_min_size` | minimum quantity |
| `quote_min_size` | minimum notional |
| `status` plus disable/cancel/view flags | trading status |
| adapter observation time | metadata timestamp and `known_at` |

Only `SPOT`, `BTC`, `USD`, and `BTC-USD` are accepted. A conflict is not
normalized away.

## WebSocket state machine

The lifecycle is:

```text
CONNECTING -> SUBSCRIBING -> TRADABLE -> STOPPED
                       \-> NOT_TRADABLE
```

A stream reaches `TRADABLE` only after:

- REST metadata is `ONLINE`;
- a valid status snapshot matches REST metadata;
- at least one heartbeat is observed;
- at least one valid ticker or public trade is observed;
- timestamps are current and timezone-aware;
- per-channel provider sequence checks pass.

Each connection sends four separate public subscription messages within the
provider's documented limit. None contains `jwt`. A disconnect triggers a
controlled close, bounded backoff, reconnection, and full resubscription.

The following conditions emit a quarantined `DataQualityAlert`, keep the
affected run `NOT_TRADABLE`, and never synthesize missing events:

- missing, duplicate, decreasing, or skipped sequence;
- heartbeat counter gap;
- stale envelope or receive timeout;
- future timestamp;
- unknown channel or schema drift;
- REST/WebSocket metadata conflict;
- reconnect schedule exhaustion.

Raw arrival checksums are retained only in the in-memory result. Canonical
records are sorted deterministically for the dataset manifest after arrival
ordering and provider sequences have passed their independent checks.

## Offline contracts

All committed fixtures are deterministic, synthetic, sanitized, and explicitly
not captured market data:

```powershell
$env:PYTHONPATH = "src;."
.venv\Scripts\pytest.exe -m "contract or replay" `
  tests/contract/test_coinbase_adapter.py `
  tests/replay/test_coinbase_websocket_replay.py
```

Coverage includes:

- metadata, bars, trades, bid/ask, REST health, and maintenance status;
- exact host/path/header/query policy;
- 429 bounded retry;
- missing required REST fields;
- duplicate, gap, and out-of-order WebSocket sequence;
- heartbeat gap, stale stream, schema drift, and metadata conflict;
- disconnect, one/two/four-second bounded backoff, resubscription, and clean
  shutdown;
- reconnect exhaustion.

Fixture replay is offline evidence only and is never a connected PASS.

## Opt-in connected smoke

No credential is required or accepted. The test remains off unless the operator
sets the exact opt-in variable:

```powershell
$env:TRADEGUARD_RUN_COINBASE_CONNECTED_TESTS = "1"
$env:PYTHONPATH = "src;."
.venv\Scripts\python.exe scripts/run_coinbase_connected_smoke.py
```

The smoke is bounded to BTC-USD and verifies:

- public server-time health;
- instrument metadata;
- recent public trades and best bid/ask;
- at least four WebSocket messages;
- timestamps and per-channel sequences;
- REST and WebSocket manifests;
- quality results;
- controlled close.

The evidence file contains no market values:

```text
artifacts/evidence/prompt5/connected-smoke-result.json
```

The committed result is `SKIP_NOT_OPTED_IN`, `provider_contacted=false`, and
promotion remains `BLOCKED`. A later local PASS still requires human evidence
review and explicit promotion approval.

## Terms and retention

The 2026-07-31 review found Coinbase terms that restrict sharing, storage,
redistribution, benchmarking, and excessive requests. TradeGuard therefore
uses internal non-display research as the narrow intended use, keeps connected
raw payloads transient, publishes only synthetic fixtures and redacted
checksums/status, and requires a terms/jurisdiction recheck before each release
candidate connected run.

## Rollback

Disable the adapter and retain adverse evidence. Do not add authentication,
switch to a private/user endpoint, fall back to another provider, or replace a
failed connected observation with fixture evidence.
