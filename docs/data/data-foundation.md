# TradeGuard data foundation

Status: implemented by Prompt 3

TradeGuard now has an offline, deterministic data boundary shared by equity and
crypto research. It does not connect to an external provider, account, broker,
or exchange.

## Authority boundary

Canonical records are strict, immutable Pydantic models:

- `Quote`
- `Trade`
- `OHLCVBar`
- `InstrumentMetadata`
- `MarketSession`
- `CorporateAction`

All authoritative prices, quantities, notionals, and precision values use
`Decimal`. Binary floats are rejected. All timestamps must be timezone-aware
and are normalized to UTC.

Raw observations can preserve quality defects such as crossed quotes, invalid
OHLC relationships, and negative volume. Representability does not make a
record admissible: only a manifest-bound `PASS` or `WARN` quality report may
support later validation evidence.

## Point-in-time metadata

Instrument metadata records both effective-time activity and knowledge-time
availability:

- `active_from` and `active_to` define when an instrument was active.
- `known_at` defines when the metadata became available to research.
- `metadata_version` identifies the reviewed definition.

An instrument is available only when it is active at the observation time and
was known by the research knowledge cut-off. Trading sessions, corporate
actions, and crypto maintenance intervals use the same knowledge-time rule.

Equity metadata requires `currency` and a session calendar. Crypto metadata
requires `quote_asset`. Tick size, step size, lot size, minimum quantity, and
minimum notional are market-specific metadata, not shared assumptions.

## Dataset identity and lineage

`DatasetManifest` records:

- dataset and schema versions;
- source, asset class, sorted symbols, and date range;
- row count and partition information;
- SHA-256 checksums;
- creation and ingestion timestamps;
- licensing notes;
- missing intervals and corrections;
- parent dataset identity;
- a versioned transformation DAG.

Partition paths must be relative and traversal-free. Partition row counts must
sum to the dataset row count, partition ranges must remain within the dataset
range, and the final transformation output must match the manifest dataset ID.
Lineage cycles and duplicate outputs fail validation.

Raw bytes can be written through `ContentAddressedStore`. The SHA-256 digest is
the address, identical writes are idempotent, and stored bytes are verified on
read. The store deliberately exposes no update or delete method.

## Quality gate

Shared checks cover missing, duplicate, out-of-order, future or stale content,
invalid OHLC, negative volume, abnormal jumps, schema mismatch, checksum or row
count mismatch, and symbol mapping conflicts.

Equity checks cover sessions, half days, corporate actions, splits, delisting,
and point-in-time universe availability.

Crypto checks cover continuous 24/7 gaps, precision, minimum notional,
maintenance intervals, crossed quotes, spread anomalies, and quote-asset
consistency.

Results use exactly:

- `PASS`
- `WARN`
- `FAIL`
- `QUARANTINED`

`FAIL` and `QUARANTINED` reports are rejected by
`require_validation_evidence_eligible`. A report is also rejected if its
dataset ID or manifest checksum does not match the supplied manifest.

## Offline fixtures and commands

The committed packages under `tests/fixtures/market_data/` contain no external
market data. They cover:

| Scenario | Expected result |
| --- | --- |
| normal | `PASS` |
| gap | `FAIL` |
| duplicate | `FAIL` |
| out of order | `FAIL` |
| bad tick | `QUARANTINED` |
| stock split | `WARN` |
| symbol change | `PASS` |
| delisting | `QUARANTINED` |
| crypto maintenance | `FAIL` |
| stale timestamp | `FAIL` |
| fresh timestamp with stale content | `FAIL` |

The CLI is offline-only:

```text
tradeguard data validate tests/fixtures/market_data/normal.json
tradeguard data manifest tests/fixtures/market_data/normal.json
tradeguard data inspect tests/fixtures/market_data/normal.json
```

Validation exits with status `2` for `FAIL`, `QUARANTINED`, malformed, or
unavailable input. It never falls back to an external source.

Regenerate deterministic artifacts with:

```text
make data-fixtures
make schemas
make prompt3-evidence
```

Prompt 3 evidence is generated under `artifacts/evidence/prompt3/` and includes
fixture manifests, quality reports, a quarantined example, transformed dataset
checksums, a lineage graph, and a SHA-256 index.

## Known limitations

- All examples are synthetic and do not qualify any real provider.
- No connected adapter or external schema-drift handling exists yet.
- The content-addressed store is a local primitive, not a retention or backup
  system.
- Quality thresholds are explicit deterministic defaults; provider- and
  venue-specific calibration belongs to later adapter prompts.
- A `PASS` result establishes data-contract eligibility only. It is not a
  strategy validation result and says nothing about profitability.
