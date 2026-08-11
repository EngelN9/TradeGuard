# CLAUDE.md — operating Claude Code in this repository

This file is loaded automatically at the start of every Claude Code session. It
describes **how to operate in this working copy**. It deliberately does not
restate product, safety, or engineering rules.

## 1. Authority

[`AGENTS.md`](AGENTS.md) is the highest-priority instruction for every AI coding
agent in this repository, including Claude Code. This file is the lowest rung:

1. [`AGENTS.md`](AGENTS.md) and any narrower `AGENTS.md`;
2. accepted ADRs in [`docs/adr/`](docs/adr/);
3. the governance documents in [`docs/governance/`](docs/governance/);
4. [`docs/roadmap/scope-ladder.md`](docs/roadmap/scope-ladder.md),
   [`docs/roadmap/release-ladder.md`](docs/roadmap/release-ladder.md), and
   [`docs/status/implementation-matrix.md`](docs/status/implementation-matrix.md);
5. task-specific instructions;
6. this file.

If this file ever conflicts with `AGENTS.md`, `AGENTS.md` wins and this file is
the defect. Never resolve a conflict by picking the more permissive rule.

## 2. Start every task by reading current reality

Do not assume repository state from memory, from a previous session, or from
this file. Before proposing or changing anything:

1. read [`docs/status/implementation-matrix.md`](docs/status/implementation-matrix.md)
   for the current stable release stop and what is actually implemented;
2. read the target domain's row in
   [`docs/roadmap/scope-ladder.md`](docs/roadmap/scope-ladder.md) for its stage
   cap, complexity budget, evidence requirements, and Stage 5 prohibitions;
3. read [`docs/roadmap/release-ladder.md`](docs/roadmap/release-ladder.md) for
   the entry gate and stopping rules of the relevant stop;
4. read the relevant source, tests, schemas, configuration, and ADRs.

Use [`docs/ai/claude-code-task-template.md`](docs/ai/claude-code-task-template.md)
to state the resulting scope contract, or run `/tg-task`.

## 3. Local commands that actually work on this machine

`make` and `uv` are **not on PATH in this working copy**, so the `make ...` and
`uv run ...` forms in [`CONTRIBUTING.md`](CONTRIBUTING.md) and `AGENTS.md` §7
cannot be executed here. Use the project virtualenv directly.

Two per-session prerequisites are required until the defects in §3.1 are fixed:

```powershell
$env:PYTHONPATH = 'src'
$env:TG_PYTEST_TMP = "$env:TEMP\tg-pytest-tmp"
```

Verified commands, last confirmed green on 2026-08-11
(236 passed, 2 deselected, 90.70% coverage):

| Purpose | Command |
| --- | --- |
| Format check | `.venv\Scripts\ruff.exe format --check .` |
| Format (write) | `.venv\Scripts\ruff.exe format .` |
| Lint | `.venv\Scripts\ruff.exe check .` |
| Type check | `.venv\Scripts\mypy.exe` |
| Fast test loop | `.venv\Scripts\pytest.exe -m "not connected" -p no:cacheprovider --basetemp=$env:TG_PYTEST_TMP` |
| Full test gate (90% coverage floor) | same as above plus `--cov=tradeguard --cov-report=term-missing` |
| Single marker | append `-m unit` (also `property`, `integration`, `contract`, `replay`) |
| Workflow policy scan | `.venv\Scripts\python.exe scripts/validate_workflows.py` |
| Secret scan | `.venv\Scripts\python.exe scripts/scan_secrets.py` |
| Web type/lint check | `npm run check --prefix web` |
| Web tests | `npm test --prefix web` |
| Schema export | `.venv\Scripts\python.exe scripts/export_schemas.py` |
| R3 evidence | `.venv\Scripts\python.exe scripts/collect_prompt6_evidence.py` |

Notes:

- The [`Makefile`](Makefile) remains the canonical description of each gate. If
  `uv` and GNU Make are installed, the `make` targets are equivalent and
  preferred, because they also write JUnit/coverage evidence under
  `artifacts/evidence/`.
- Run `/tg-verify` to execute the full gate sequence in order.
- Report the exact observed result of every command. A command that was not run
  is `SKIP`, never `PASS`.

### 3.1 Known local environment defects

These are defects of **this working copy**, not of the project. They exist
because parts of the tree were created by a different Windows account
(`CodexSandboxOffline`) than the current user. Do not work around them by
changing project configuration, tests, or `pyproject.toml`.

| Symptom | Cause | Permanent fix (maintainer action) |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'tradeguard'` | `.venv` has `tradeguard` dist-info but no editable path link | `uv sync --locked`, or `.venv\Scripts\pip.exe install -e . --no-deps` |
| `PermissionError` on `.pytest-tmp` during test setup | `.pytest-tmp` is owned by the other account and denies access | delete the gitignored `.pytest-tmp` directory |
| `PytestCacheWarning` / `WinError 183` on `.pytest_cache` | same ownership problem | delete the gitignored `.pytest_cache` directory |
| `fatal: detected dubious ownership` from any git command | `.git` is owned by the other account | `git config --global --add safe.directory C:/Users/User/Documents/GitHub/TradeGuard`, or re-clone in GitHub Desktop |

After all four are fixed, drop the two environment variables and the
`-p no:cacheprovider --basetemp=...` flags, and update this section.

## 4. Connected tests are never part of ordinary validation

Connected tests require an explicit opt-in environment variable
(`TRADEGUARD_RUN_CONNECTED_TESTS=1` or
`TRADEGUARD_RUN_COINBASE_CONNECTED_TESTS=1`) plus the accepted ADR prerequisites
in [`docs/adr/`](docs/adr/). Both connected qualifications are currently
`BLOCKED`.

Do not set these variables, do not request credentials, and do not run connected
tests. Report their status as `SKIP` or `BLOCKED`.

## 5. Git, GitHub, and the human boundary

Claude Code MUST NOT commit, push, merge, rebase, tag, create or update a pull
request, or change any GitHub state, unless the current task explicitly
authorizes that exact action. A request to edit or review code is not
authorization to publish it.

The maintainer performs commits, merges, and publication in **GitHub Desktop**
(`C:\Users\User\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\GitHub, Inc\GitHub Desktop.lnk`).
The `gh` CLI is installed on this machine but is subject to the same
restriction.

Leave the worktree in a state the maintainer can inspect as a clean diff:
preserve unrelated changes, and do not revert or stage anything you did not
create.

### If git does not work

`git` in this working copy may fail with `detected dubious ownership` because
`.git` is owned by a different Windows account than the current user. When that
happens:

- state plainly that **git is unavailable and repository state is unverified**;
- do not infer the branch, base, or dirtiness from file timestamps, from this
  file, or from the implementation matrix;
- ask the maintainer to resolve ownership before doing anything that depends on
  knowing the branch state.

## 6. Non-negotiable completion conditions

Every increment must be simultaneously:

- **Runnable** — one concrete command produces the claimed behavior;
- **Testable** — named tests with a marker and an expected result cover it;
- **Maintainable** — a named human owner, regression tests, and updated docs,
  schemas, and evidence;
- **Stoppable** — the resulting state is a legitimate permanent stopping point,
  with a precise rollback path and no placeholder implying future capability.

If any one of the four cannot be satisfied, the increment is too large. Split it
and implement only the smallest authorized slice.
[`docs/ai/claude-code-task-template.md`](docs/ai/claude-code-task-template.md)
defines the exact fields.

## 7. Reporting

Follow `AGENTS.md` §6 before editing and `AGENTS.md` §8 after finishing. End
every task with an explicit promotion gate result: `PASS`, `FAIL`, or `BLOCKED`.
Never present local success as connected qualification, human approval, merge,
release, or future profitability.
