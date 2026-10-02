# ADR 0006: Product boundary against the LLM finance ecosystem

- Status: Accepted
- Date: 2026-09-12
- Decision owner: EngelN9
- Target release: None. This ADR authorizes no implementation.

## Context

This repository's product boundary was written when general-purpose assistants
could discuss markets but could not act in them, and when market data, execution
realism, and research reporting were things a research tool would plausibly build
for itself. Both assumptions expired during 2026.

This ADR records a dated scan of what the surrounding ecosystem now supplies, and
draws the resulting boundary. It is written because the absence of such a record
makes every future task re-argue "should TradeGuard add a data layer, a report
generator, an execution model?" from first principles, with no citable reason to
decline.

### Scan: assistant-directed trading became ordinary

Order entry is now exposed to any assistant that speaks the Model Context
Protocol, at both retail and institutional brokers:

| Date | Development |
| --- | --- |
| 2026-01 | TradeStation ships the first MCP server at a US broker |
| 2026-05-27 | Robinhood opens Agentic Trading — an MCP client may read the portfolio, analyze risk, and place real equity orders; reported at roughly 100,000 accounts and over $100M custodied by the end of Q2 |
| 2026-06-22 | Interactive Brokers adds ChatGPT and Grok to an agentic suite that began with Claude, covering equities, ETFs, options, futures and futures options; every assistant-generated instruction requires client review before the order reaches the market |
| 2026-08-25 | Scalable Capital becomes the first ECB-licensed bank in Europe to let retail customers execute trades, set up savings plans, and manage portfolios through ChatGPT and Claude |
| 2026-08-31 | Coinbase for Agents extends its June 2026 MCP launch to stocks alongside crypto and derivatives |

Primary sources: the Interactive Brokers media release (`interactivebrokers.com`,
2026-06-22). The remaining rows rest on secondary trade reporting and are
recorded at that confidence; the boundary below does not depend on any single
row being exact, only on the pattern, which is corroborated across independent
outlets.

### Scan: analysis capability consolidated into the vendors

Claude for Financial Services ships pre-built MCP connectors to FactSet,
S&P Capital IQ, MSCI, PitchBook, Morningstar, LSEG, Moody's, Daloopa, Aiera and
MT Newswires, alongside firms' own warehouses, under governed access controls. It
adds a native Excel plugin, real-time market connectors, and skills for modeling,
comparable-company analysis and earnings reports. Ten finance agents were
released on 2026-05-05, deployable as plugins or as headless managed agents.
Sonnet 4.5 leads the Vals AI Finance Agent benchmark at 55.3%.

Source: `anthropic.com/news/claude-for-financial-services`,
`anthropic.com/news/advancing-claude-for-financial-services`,
`anthropic.com/news/finance-agents`.

### Scan: both vendors gate advice on a licensed human

- **Anthropic.** The Usage Policy's High-Risk Use Case Requirements, effective
  2025-09-15, cover "use cases related to financial decisions, including
  investment advice". They require that "a qualified professional in that field
  must review the content or decision prior to dissemination or finalization",
  and that AI involvement be disclosed to the end user. These bind
  consumer-facing outputs rather than business-to-business interactions.
  Source: `anthropic.com/legal/aup`.
- **OpenAI.** Usage Policies effective 2025-10-29 prohibit "tailored advice that
  requires a license... without appropriate involvement by a licensed
  professional", with the operative distinction drawn between tailored advice and
  general information. Source: `openai.com/policies/usage-policies/`.

Neither vendor prohibits financial work. Both condition it on a qualified human
in the loop and on disclosure.

### Scan: the open-source research stack is mature and specialized

NautilusTrader is the strongest open foundation where execution mechanics decide
the outcome — order types, sequencing, latency, book depth, live parity.
QuantConnect's LEAN is the most complete end-to-end platform, with brokerage
integrations, tick data and portfolio-construction frameworks. PyBroker builds
walk-forward analysis in as a first-class primitive. vectorbt remains the fastest
route to large parameter sweeps, with its ongoing development in a paid closed
tier. Each is better at its specialty than a general research workbench will be.

## Decision

### 1. Build versus defer

| Capability | Already supplied by | Disposition |
| --- | --- | --- |
| Order submission, routing, brokerage connectivity | Robinhood, Interactive Brokers, Scalable Capital, Coinbase for Agents, TradeStation — all reachable over MCP | **Never build.** Already permanently excluded from the release ladder. Now also redundant |
| Point-in-time universes, corporate-action histories, cross-vendor price consensus | FactSet, S&P Capital IQ, LSEG, MSCI, Morningstar, Daloopa, reachable through governed connectors | **Defer indefinitely.** Reinforces the [ADR 0005](0005-external-recommendation-triage.md) deferral of recommendations 1.1, 1.2 and 1.3 |
| Order-book realism, latency modeling, backtest-to-live parity | NautilusTrader | **Defer.** Domain 11 remains at conservative bar fills |
| Walk-forward machinery, large parameter sweeps | PyBroker, vectorbt | **Defer.** Domains 16 and 17 build only the single fixed split R5 requires |
| End-to-end research-to-deployment platform | QuantConnect LEAN | **Never build.** Outside the mission |
| Narrative research reports, spreadsheet modeling, comparable-company and earnings analysis | Claude for Financial Services, its Excel plugin and finance agents | **Defer.** Reinforces the ADR 0005 rejection of recommendation 5.3 |
| **Pre-deployment evidence that a strategy was actually validated: an immutable split declared before results, a reproducible run manifest, retained adverse results, and a recorded human promotion decision** | **Nothing in the stack above** | **Build. This is the product** |

### 2. The operative rule

A capability that an established vendor or a maintained open-source project
already supplies is **declined by default**. It is adopted only when an accepted
ADR demonstrates that the cost of integrating or depending on the external
supplier exceeds the verification value lost by not holding the capability
in-tree.

"A reasonable system would have this" is not an argument for building it. The
argument must be that TradeGuard's own question — *is this strategy worth
trusting?* — cannot be answered without it.

### 3. Exclusion is now positioning, not caution

The scan inverts the usual reading of this project's scope.

Order submission has become the commodity half of the stack: five brokers give it
away, and an assistant can drive it in a single MCP call. What none of them
supplies is any evidence that the strategy behind the order was ever validated —
that the split was declared before the results were seen, that the adverse runs
were kept, that a human recorded a decision against a reproducible manifest.

So the capability TradeGuard permanently excludes is the one with no scarcity,
and the capability it retains is the one nothing else in the ecosystem provides.
The correct answer to "why not add live trading now that it is easy" is that the
easiness is precisely the argument against it.

This also settles a recurring question in the opposite direction: the project's
scarce asset is the promotion record, not the order path, so work that
strengthens evidence discipline outranks work that broadens market reach.

### 4. Independent confirmation of the human-promotion rule

Both vendor policies now require a qualified or licensed human to review
financial output before it is disseminated, and require disclosure of AI
involvement. TradeGuard satisfies both **by construction** rather than by
compliance effort: promotion is already a recorded human act, automatic promotion
is already out of scope, and the project already makes no investment
recommendation to any end user.

ADR 0005 rejected two proposals for numeric auto-advance gates. That rejection
now has external corroboration: an automatic gate that advanced a strategy
without a human record would move the project away from the posture both vendors
independently converged on.

### 5. What does not change

No domain stage cap, complexity budget, release stop, blocker, ladder arrow, or
evidence requirement moves. `canary` and `live` remain permanently excluded. This
ADR narrows the set of capabilities that may be proposed. It widens nothing, and
it authorizes no integration with any vendor or project named above.

Naming a vendor or project here is a statement about where a capability already
exists. It is not an endorsement, a recommendation to trade through it, a
dependency, or a commitment to integrate.

## Consequences

- "Another maintained system already does this" becomes a citable reason to
  decline scope, which is the reason this ADR exists.
- The deferrals in ADR 0005 gain a second, independent justification. They were
  deferred there because the ladder caps them; they are deferred here because
  building them duplicates a vendor.
- The project's public positioning can state plainly what it is for, now that the
  surrounding ecosystem makes the contrast legible: the verification layer that
  the agentic-trading stack does not contain.
- Accepting this ADR creates no dependency, no connector, no credential class,
  and no new maintenance surface.

## Promotion gate

This ADR promotes nothing and authorizes no implementation.

The only `NEXT` gate remains exact-head human review of the R4 candidate, per
[`implementation-matrix.md`](../status/implementation-matrix.md).

## Review triggers

The scan above is dated and will age. Reopen this ADR when any of the following
occurs:

- a vendor or open-source project named here withdraws, paywalls, or materially
  changes the capability attributed to it, which would move a "defer" row back
  into scope;
- either vendor's usage policy stops requiring a qualified or licensed human
  reviewer for financial output, removing the external corroboration in section 4;
- a regulator or standards body publishes a pre-deployment assurance requirement
  for assistant-directed trading, which would bear directly on the capability
  section 1 retains;
- an accepted ADR names an external user, since the build-versus-defer balance
  assumes the single-maintainer user of
  [ADR 0004](0004-first-named-user-and-mvp-designation.md);
- the scan is more than twelve months old and is being cited in a scope decision.

## Rollback

Supersede with a later ADR. This decision touches no code, schema, configuration,
data, or evidence. Rollback is limited to marking this ADR superseded, reverting
the "Ecosystem boundary" subsection of
[`product-safety.md`](../governance/product-safety.md), and removing its entry
from [`docs/README.md`](../README.md). No ladder stop, test, or recorded
promotion depends on it.
