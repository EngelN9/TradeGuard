# PROMPTS.md — Deprecated compatibility notice

`PROMPTS.md` has been replaced by [`DELIVERY_PLAN.md`](DELIVERY_PLAN.md).

The former file combined persistent engineering policy, completed implementation
prompts, future delivery stages, release evidence requirements, and publication
operations in one monolithic document. That structure made it too easy to submit
stale or excessive instructions to Codex.

Use the following sources instead:

- [`DELIVERY_PLAN.md`](DELIVERY_PLAN.md): current delivery sequence, status
  orientation, review gates, and instructions for assigning one stage at a time.
- [`AGENTS.md`](AGENTS.md): repository-wide rules for AI agents and contributors.
- [`CONTRIBUTING.md`](CONTRIBUTING.md): development and pull-request workflow.
- [`SECURITY.md`](SECURITY.md): security policy and vulnerability reporting.
- [`docs/release/connected-release-v1.md`](docs/release/connected-release-v1.md):
  authoritative Connected Release contract and non-live boundary.
- [`docs/status/implementation-matrix.md`](docs/status/implementation-matrix.md):
  authoritative implementation status and outstanding gaps.

Do not submit this compatibility notice or the former monolithic prompt set to
Codex as an implementation task. Submit one current stage from
`DELIVERY_PLAN.md`, or preferably one small, independently reviewable GitHub
Issue.

This compatibility file is retained temporarily so existing links do not break.
It may be removed after all repository references have been migrated to
`DELIVERY_PLAN.md`.
