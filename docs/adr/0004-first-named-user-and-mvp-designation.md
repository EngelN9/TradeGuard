# ADR 0004: First named user and MVP designation

- Status: Accepted
- Date: 2026-08-27
- Decision owner: EngelN9
- Target release: R5 (functional) and R7 (first public)

## Context

[`docs/roadmap/scope-ladder.md`](../roadmap/scope-ladder.md) makes "one named
user/vertical slice" an entry gate for every Stage 1 — minimum viable capability
— promotion. No document in this repository has ever named that user. The R1,
R2, and R3 promotions were therefore recorded against a gate whose referent was
never stated. That is a defect in the repository's own terms, not a missing
feature.

Separately, the project already designates a minimum viable product in two
places, but neither is discoverable:

- [`scope-ladder.md`](../roadmap/scope-ladder.md) Stage 1 is literally named
  "minimum viable capability", per domain, with complexity budget `B1`.
- [`release-ladder.md`](../roadmap/release-ladder.md) marks R7 as
  "Candidate first public offline research release" — in the sixth column of a
  wide table, referenced by no other document.

[`docs/governance/research-risk-and-promotion.md`](../governance/research-risk-and-promotion.md)
states that "There is no single all-or-nothing MVP", and that each ladder stop
is a valid maintained product boundary. That clause is deliberate and remains in
force. This ADR does not create an MVP; it names the user the ladder already
requires, and makes the designation the ladder already contains legible.

## Decision

### 1. The first named user

The first named user is **the maintainer, working as a solo quantitative
researcher**, offline, against synthetic fixtures or data personally licensed
for internal use.

The user-level acceptance criterion, which the ladder currently expresses only
in engineering evidence, is:

> The maintainer can take one strategy idea and produce a defensible
> keep-or-stop decision without leaving the tool.

This referent applies to Stage 1 promotions already recorded and to all future
ones. It is the standard against which "is this capability viable?" is judged.

### 2. Two-layer MVP designation

This restates a distinction the release ladder already draws. It changes no
stop's definition, evidence, gate, or order.

**Functional MVP — R5 (basic comparative validation).** The first stop at which
the product's own question, *is this strategy worth trusting?*, can be answered
end to end: one baseline, a cash and buy-and-hold benchmark, one immutable split
declared before results with an untouched out-of-sample evaluation, and one cost
sensitivity run. The ladder already calls R5 a "valid permanent
research-validation release".

**Public MVP — R7 (reproducible research report and evidence).** The first stop
at which that answer becomes shareable and auditable: one finalized local
experiment, a balanced JSON/HTML report, and a generic evidence index with
tamper rejection. The ladder already calls R7 the "candidate first public
offline research release".

### 3. This does not override the no-single-MVP rule

`R5` and `R7` are labels applied to existing ladder stops. They are not a new
all-or-nothing bundle and they do not make earlier stops provisional. R0 through
R4 each remain a legitimate permanent stopping point that may be maintained
indefinitely without ever reaching R5.

Reaching a labelled stop still requires that stop's own evidence and its own
recorded human promotion. This ADR authorizes no implementation and no
promotion.

## Consequences

- Stage 1's "one named user" entry gate now has a stated referent, so future
  promotions can cite it and past ones are no longer ambiguous.
- Scope pressure tightens in a useful direction: a capability that does not help
  the maintainer reach a defensible keep-or-stop decision at R5 is deferred,
  regardless of how reasonable it looks in isolation.
- **Naming the maintainer as the only user explicitly places external usability
  work outside R5 and R7 scope.** Onboarding flows, install polish, tutorials,
  hosted examples, and multi-user concerns are not R5/R7 requirements and must
  not be smuggled in under the MVP label. They become in scope only when a later
  ADR names an external user, which may also raise the affected domain stage
  caps and complexity budgets.
- The gap between the current stop and the functional MVP is now explicit: R4's
  exact-head human review, then the four R5 evidence items. Nothing else.

## Promotion gate

This ADR records a naming and labelling decision. It promotes nothing.

The only current `NEXT` gate remains exact-head human review of the R4
candidate, per
[`docs/status/implementation-matrix.md`](../status/implementation-matrix.md).
R5 work is not authorized until that review is recorded `PASS` and the stable
base changes.

## Review triggers

Reopen this ADR when any of the following occurs:

- an external user is identified, or the project accepts outside contributions
  that depend on external usability;
- the release ladder changes the definition, evidence, or ordering of R5 or R7;
- governance revises the no-single-MVP clause in
  [`research-risk-and-promotion.md`](../governance/research-risk-and-promotion.md);
- maintenance ownership changes, since the named user and the maintainer are
  currently the same person.

## Rollback

Supersede with a later ADR. This decision touches no code, schema, data, or
evidence, so rollback is limited to marking this ADR superseded and removing the
summary sections it added to [`ROADMAP.md`](../../ROADMAP.md). No ladder stop,
test, or recorded promotion depends on it.
