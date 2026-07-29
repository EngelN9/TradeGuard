# Domain Events, Configuration, and Run Manifest

Status: implemented by Prompt 2
Schema version: `1.0.0`

## Event contract

Every TradeGuard domain event is an immutable Pydantic model. The common
envelope contains the required identity, source, asset, venue, symbol, UTC
timestamps, sequence, correlation, causation, run, schema-version, and checksum
fields.

`payload_checksum` is the SHA-256 digest of canonical JSON for the complete
event except the checksum field itself. Canonical JSON:

- sorts mapping keys;
- serializes timezone-aware datetimes in UTC with a `Z` suffix;
- serializes UUID and enum values as strings;
- normalizes finite `Decimal` values as non-exponent strings;
- rejects binary floats at authoritative boundaries; and
- never serializes `SecretStr` values.

Events must be created with `EventType.build(...)`. The builder validates the
model and derives the checksum. Parsing untrusted serialized events validates
the supplied checksum again.

## Schema compatibility policy

The current event schema is exactly `1.0.0`. `EventParser` accepts current
events directly and fails closed for any other version unless the caller
provides an explicit, immutable migration registry keyed by
`(event_type, old_schema_version)`.

A migration must be separately reviewed and must return a complete current
event whose current checksum validates. No implicit field dropping, best-effort
parsing, or silent future-version acceptance is permitted.

## Configuration contract

Configuration is assembled from ordered YAML layers using `yaml.safe_load` and
then validated as one immutable `TradeGuardConfig`. The required layers are:

- base;
- environment;
- market;
- venue;
- data;
- strategy metadata;
- portfolio;
- risk;
- cost;
- monitoring; and
- alerting.

Only `research`, `backtest`, `replay`, `paper`, and `shadow` environments are
valid. Venue configuration is read-only and structurally prohibits order
submission. Monetary and rate values reject binary floats.

Effective inspection replaces every secret value with `<redacted>`. The config
hash is calculated from that complete redacted representation, so credential
rotation does not change research identity and no credential can enter the
hash input or inspection output.

## Run manifest

`RunManifest` records run identity, strategy identity, Git state, effective
config hash, dataset references, UTC range, universe, seed, platform, Python
and lock identity, cost/execution model versions, completion, result checksum,
warnings, and validation failures.

Release qualification fails closed when:

- the Git worktree was dirty;
- the run is incomplete;
- the result checksum is absent; or
- any validation failure is recorded.

## Schema artifacts

Run the following after changing a contract:

```bash
make schemas
```

or:

```bash
uv run python scripts/export_schemas.py
```

Committed artifacts are under `schemas/`. Contract tests compare those files to
fresh model-generated schemas and validate the synthetic sample run manifest.

These contracts do not implement a strategy, external adapter, broker
connection, or order-submission capability.
