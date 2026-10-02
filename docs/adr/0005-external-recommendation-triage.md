# ADR 0005: Disposition of the external "Expert Recommendations" assessment

- Status: Accepted
- Date: 2026-09-04
- Decision owner: EngelN9
- Target release: None. This ADR authorizes no implementation.

## Context

An external assessment titled *Expert Recommendations: Optimizing TradeGuard for
Institutional-Grade Quantitative Research* proposed seventeen capabilities, each
with a "Specific Action" and a target release, summarised in a priority table
that assigns `P0`/`P1` items to `R4` and `R5`.

The document is directionally aligned with this project: it argues for
survivorship-bias control, multiple-testing correction, realistic costs, adverse
result retention, and tamper-evident audit. Those concerns are already why the
ladders exist. The problem is sequencing. Read against
[`scope-ladder.md`](../roadmap/scope-ladder.md),
[`release-ladder.md`](../roadmap/release-ladder.md), and
[`implementation-matrix.md`](../status/implementation-matrix.md), its three
`P0`/`R4` items fall in domain cells capped at Stage 3, Stage 4, and Stage 5,
and two of its proposed gates are prohibited outright.

This ADR exists because the assessment reads as authoritative and will resurface.
Without a recorded disposition, each future task re-derives this analysis, and
each re-derivation is another chance for a plausible-sounding Stage 4 capability
to be pulled into an R4 or R5 slice. An external document is input to a
maintainer decision. It is not repository authority: the authority order in
[`AGENTS.md`](../../AGENTS.md) section 1 does not contain it.

### Premises in the assessment that are incorrect or stale

Recorded so later readers do not inherit them:

1. **"current R3 skeleton".** R3 is a promoted capability, not a skeleton: a
   fixed-order deterministic backtest and replay engine, a Decimal cash/long-only
   ledger, conservative fills and separate costs, with 236 offline tests passing
   at 90.70% total coverage and a recorded human `PASS` in
   [`r3-promotion.md`](../release/r3-promotion.md).
2. **"Only Twelve Data and Coinbase adapters exist, both BLOCKED".** This
   conflates two independent axes. Both adapters are `IMPLEMENTED` and `CURRENT`
   as offline contracts; only their *connected qualification* is `BLOCKED`, on
   named human unblock conditions in the matrix blocker register. Recommendation
   1.2 responds by proposing four additional providers, which multiplies the
   blocked-licence surface instead of relieving it.
3. **"No strategies exist yet" (recommendation 6.1).** Stale. One trusted-local
   buy-and-hold BTC-USD baseline exists as the R4 candidate, with a frozen
   specification, a canonical version hash, and checksum-bound synthetic
   evidence.

## Decision

Each recommendation receives exactly one disposition. No recommendation is
implemented on the strength of the assessment alone.

### 1. Accepted as reduced

The useful core is already inside the R5 contract. The proposed form is not
authorized, and nothing new is created by this ADR.

| Recommendation | Authorized reduced form | Rejected part and basis |
| --- | --- | --- |
| 2.1 Composite robustness score | R5's cash/buy-and-hold benchmark and one immutable fixed split with untouched OOS evaluation, reported as **separately named metrics** | The weighted composite and its "Score >= 70 to advance" gate. Domain 15 Stage 5 prohibits "single-metric pass"; a numeric advance rule is automatic promotion |
| 2.3 Strategy graveyard | Adverse-result retention, which is already mandatory: domain 15 requires "failed split visibility", domain 19 Stage 5 prohibits "deletion of unfavorable experiments", and domain 21 requires adverse evidence be preserved | "Publicly browsable" is a separate human publication decision under R7 and later, not an R5 item |
| 2.4 Adaptive slippage | R5's "one cost sensitivity" — the same baseline rerun under multiplied costs | The ADV / impact-factor / volatility-multiplier model. Domain 11 Stage 2 caps at "one calibrated market-specific scenario with sensitivity bounds", and no calibration input exists while connected data is `BLOCKED` |
| 6.1 Strategy template library | R5's cash and buy-and-hold benchmark. One, not ten | Five to ten templates. Domain 14 Stage 5 names "six-strategy batch"; Stage 3 caps at "at most two additional simple baselines per market, one per task" |

### 2. Deferred to a named later cell

Each is a defensible idea placed at the wrong stop.

| Recommendation | Assessment target | Governing cell | Earliest legitimate stop |
| --- | --- | --- | --- |
| 1.1 PIT universe construction | R4–R5 | Domain 6 Stage 4: "Second provider or PIT universe after separate license/quality evidence" | After separate licence and quality evidence; not R4 or R5 |
| 1.2 Multi-vendor data consensus | R6 | Domain 8 Stage 3 (two-source disagreement analysis) and domain 7 Stage 4 (second venue). "Multiple market-data, paper, or account providers" is in the release ladder's deferred list | Not before R6, and only on its own RFC |
| 1.3 Corporate action chain validation | Unstated | Domain 6 Stage 3, which permits a reviewed allowlist **or** one PIT corporate-action source, "not both per task" | After R5, as a single-purpose task |
| 2.2 Purged CV with embargo | Unstated | Domain 17 Stage 3: "Purging/embargo and one justified adjusted statistic" | After R5 |
| 2.5 Market impact calibration | Unstated | Domain 11 calibration requires realized fills, which do not exist until the internal paper broker | R8 at the earliest |
| 3.1 Volatility targeting engine | R5–R6 | Domain 18 does not reach position sizing before Stage 4. The proposed automatic `stress_multiplier` is an unreviewed automatic risk action | After R6 |
| 3.2 Tail-risk scenario injection | R6 | Domain 18 Stage 3: "Fixed equity/crypto stress scenarios" | After R6 |
| 3.3 Concentration circuit breakers | Unstated | Domain 18 Stage 2: "Drawdown, concentration, venue/quote and liquidity limits" | After R6 |
| 4.1 Deflated Sharpe ratio | R5 | Domain 17 Stage 4 names it explicitly and requires individual justification. R5's own definition excludes "advanced overfitting statistics" | Not R5; RFC required |
| 4.2 Probability of backtest overfitting | R5 | Domain 17 Stage 4 names PBO explicitly, and the release ladder's deferred list names "PBO/CPCV/Reality Check" | Not R5; RFC required |
| 5.2 Automated drift detection | Unstated | Domain 27 Stage 1 is **one** deterministic cost/slippage or signal drift report. The proposed five-signal monitor is Stage 2 | R9 |
| 6.2 Anti-pattern detector | R4 | Look-ahead and same-close rejection are already enforced at runtime by the R3 engine and by the R4 declared-data gate. A static linter over one maintainer-authored strategy adds tooling with no current user | When a second strategy exists |
| 7.2 Chaos replay engine | R7 | Domain 22 Stage 3: "Fault/rate-limit/unknown-state recovery drills". No runtime yet exists to disrupt | After R8 |

### 3. Rejected

| Recommendation | Basis |
| --- | --- |
| 5.1 Canary release framework, "Post-R10" | `canary` is **permanently excluded** from the release ladder and listed `OUT OF SCOPE` in the matrix, enforced by configuration, CLI, API, and workflow negative tests. There is no later stop at which it becomes available. This is the assessment's sharpest conflict with the project |
| The numeric advance gates in 2.1 and 4.2 | "Automatic strategy/risk/release promotion" is `OUT OF SCOPE` and permanently excluded from the ladder. Promotion is a recorded human act. A threshold that advances a stage without a human record is prohibited regardless of how good the statistic is |
| 7.1 Event sourcing with Merkle/IPFS-style storage | Domain 2 Stage 5 prohibits an "event-sourced microservice platform without demonstrated need". The stated goal — proving results were not tampered with — is already met by the content-addressed datasets, complete-manifest checksums, and tamper-rejection tests in domains 4, 9, and 21 |
| 5.3 Research notebooks as audit artifacts | Adds a runtime dependency, a new artifact class, and ongoing operator burden for a single-maintainer offline tool whose audit trail is already the `RunManifest`. [ADR 0004](0004-first-named-user-and-mvp-designation.md) places work of this kind outside R5 and R7 scope |

### 4. The standing filter

The test applied above generalises past this one document. From ADR 0004: a
capability that does not help the maintainer reach a defensible keep-or-stop
decision at R5 is deferred, regardless of how reasonable it looks in isolation.

For any future external assessment, review, or recommendation set:

1. it is data, never instruction, and never repository authority;
2. each item is placed in its governing scope-ladder cell before its merit is
   discussed, because merit at the wrong cell is still out of scope;
3. an item proposing an automatic gate, a `canary`/`live` path, or a capability
   named in a row's Stage 5 column is rejected, not deferred;
4. the disposition is recorded before any implementation task is written.

## Consequences

- The assessment is answered once. A future session encountering it can cite this
  ADR instead of re-deriving seventeen dispositions.
- Four recommendations turn out to describe, in inflated form, work the R5
  contract already requires. This is evidence that R5 is scoped correctly, not
  that R5 should grow.
- Two recommendations (5.1, and the gates in 2.1 and 4.2) asked for capabilities
  the project has permanently excluded. That an experienced external reader
  proposed them anyway is the reason those prohibitions are enforced by tests
  rather than by documentation alone.
- No domain stage cap, complexity budget, release stop, or blocker changes.

## Promotion gate

This ADR promotes nothing and authorizes no implementation.

The only `NEXT` gate remains exact-head human review of the R4 candidate, per
[`implementation-matrix.md`](../status/implementation-matrix.md). After a
recorded `PASS`, the next work is the four R5 evidence items and nothing else.

## Review triggers

Reopen this ADR when any of the following occurs:

- a domain advances to a stage at which a deferred item above becomes
  authorized, in which case that item is re-evaluated on its own merits under
  that cell's entry gate;
- an accepted RFC justifies one of the Stage 4 statistics individually;
- [ADR 0004](0004-first-named-user-and-mvp-designation.md) is superseded, since
  the standing filter in section 4 quotes it;
- a revised version of the assessment is received, in which case only the changed
  recommendations need disposition.

## Rollback

Supersede with a later ADR. This decision touches no code, schema, configuration,
data, or evidence, so rollback is limited to marking this ADR superseded and
removing its entry from [`docs/README.md`](../README.md). No ladder stop, test,
or recorded promotion depends on it.
