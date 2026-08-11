# TradeGuard evidence

`make evidence` writes redacted, generated evidence to
`artifacts/evidence/bootstrap/`.

The bootstrap bundle contains:

- JUnit test results when the corresponding test targets are run
- coverage XML from `make test`
- Python, platform, and available tool versions
- SHA-256 hashes for `uv.lock` and `web/package-lock.json`
- Git SHA, branch, and dirty-worktree state
- a placeholder for container build metadata populated by CI or later release
  qualification
- an `index.json` containing SHA-256 checksums for the generated files

Stage-specific Prompt 3 through Prompt 5 directories also contain committed,
redacted review evidence. Prompt 5 includes only deterministic synthetic
Coinbase-shaped fixture checksums, capability/status records, reconnect and
sequence-gap evidence, test output, and an explicitly non-connected smoke
result.

Prompt 6 contains deterministic synthetic checksum comparisons, ordinary and
recomputed bound-manifest identity tamper rejection, aggregate bar-participation
enforcement, cash/asset conservation, post-bar corporate-action finalization,
engine-owned completion-time ordering and prefilled-time rejection, same-close
rejection, partial-fill, stock-split, and
crypto-maintenance rejection evidence. These artifacts are simulation results,
not performance claims, connected observations, or promotion approval.

R4 contains one synthetic-only BTC-USD buy-and-hold candidate contract, the
strategy-to-R3 result artifact, deterministic checksum comparison, unsupported
market and undeclared-data rejection, and direct plus recomputed-checksum
tamper rejection. Its `NOT_EVALUATED` status is not strategy validation,
promotion approval, investment advice, or a profitability claim.

Evidence must not contain environment values, credentials, account details, raw
connected market values, or other secrets. A fixture replay must never be
represented as a connected PASS.
