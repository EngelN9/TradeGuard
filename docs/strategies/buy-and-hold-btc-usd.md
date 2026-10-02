# Synthetic BTC-USD buy-and-hold baseline

Status: `R4 CANDIDATE / NOT_EVALUATED / NOT INVESTMENT ADVICE`

## Frozen identity

- Strategy ID: `buy-and-hold-btc-usd`
- Strategy specification version: `1.0.0`
- Canonical strategy version hash:
  `56fa87c025d421dac8ca15c162aac1d267b2d5aa3db7f29a0fb0381a1c3f5224`
- Market: synthetic crypto, `SYNTH-CRYPTO`, `BTC-USD`
- Dataset: `synthetic-normal` version `1.0.0`
- Dataset manifest checksum:
  `559e0e669ff3ab7d6bf37aaa192c8cba69c253361e2b640209320f5ffb0da750`
- Fixture file SHA-256:
  `babd3917bdafbe86cb840981be2d64a2c51a498f766a0aeb385a596e70aad578`
- Initial cash: synthetic `USD 100000`
- Quantity: synthetic `0.1000 BTC`
- Warmup: one completed OHLCV bar

## Behavior

After the first completed declared bar, the baseline emits one long signal with
strength one, one `0.1000 BTC` target, and one matching BUY MARKET proposal. It
emits nothing else and holds the simulated position through the fixture end.
The proposal is sequenced after the first bar and the R3 simulator fills it only
on the second bar.

The baseline does not size from wealth, optimize parameters, liquidate, compare
benchmarks, calculate performance metrics, validate an edge, evaluate risk, or
promote itself. It assumes the synthetic research account starts with no BTC.

## Applicable and unsupported inputs

Only the exact committed two-bar synthetic fixture above is supported. Equity,
ACME, real Coinbase data, connected data, alternate crypto pairs, alternate
venues, modified fixture bytes, modified manifests, non-`PASS` quality, volume,
future bars, account state, and any private/user channel are rejected.

## Known limitations and failure modes

- Two synthetic bars cannot establish profitability, robustness, liquidity, or
  real-world fillability.
- No benchmark, OOS split, sensitivity analysis, risk engine, or paper behavior
  exists at R4.
- A repository maintainer must review any code change because trusted local
  Python is not sandboxed.
- Any specification, parameter, dataset, plan, event, result, report, or
  checksum mismatch invalidates the artifact.

Rollback removes this one baseline and its compiler/CLI seam; promoted R3
fixed-order simulation remains available.
