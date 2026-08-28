---
name: "source-command-tg-verify"
description: "Run the full local TradeGuard validation gate and report exact results"
---

# source-command-tg-verify

Use this skill when the user asks to run the migrated source command `tg-verify`.

## Command Template

Run the local validation gate in this order. Run every step even if an earlier
one fails, so the report is complete, then summarize.

First set the per-session prerequisites from `AGENTS.md` §3:

```powershell
$env:PYTHONPATH = 'src'
$env:TG_PYTEST_TMP = "$env:TEMP\tg-pytest-tmp"
```

1. `.venv\Scripts\ruff.exe format --check .`
2. `.venv\Scripts\ruff.exe check .`
3. `.venv\Scripts\mypy.exe`
4. `.venv\Scripts\pytest.exe -m "not connected" -p no:cacheprovider --basetemp=$env:TG_PYTEST_TMP --cov=tradeguard --cov-report=term-missing`
5. `.venv\Scripts\python.exe scripts/validate_workflows.py`
6. `.venv\Scripts\python.exe scripts/scan_secrets.py`
7. `npm run check --prefix web`
8. `npm test --prefix web`

Expected baseline as of 2026-08-09: 236 passed, 2 deselected, 90.70% coverage,
2 web tests passing. A drop below that is a regression, not a new baseline.

If step 4 fails with `ModuleNotFoundError: No module named 'tradeguard'` or a
`PermissionError` on `.pytest-tmp`, that is a known working-copy defect listed
in `AGENTS.md` §3.1. Report it as an environment defect and do not change
`pyproject.toml`, tests, or project configuration to work around it.

## Reporting rules

Report a table with one row per step: the command, the exit code, and the
decisive output (test counts, coverage percentage, first error).

- A step that was not executed is `SKIP` with the reason. It is never `PASS`.
- A step that failed is `FAIL` with the actual error text, never a summary that
  softens it.
- Connected tests are out of scope here. They are `BLOCKED` pending the ADR
  prerequisites; do not set `TRADEGUARD_RUN_CONNECTED_TESTS` or
  `TRADEGUARD_RUN_COINBASE_CONNECTED_TESTS`.
- The coverage floor is 90% (`pyproject.toml`, `[tool.coverage.report]`).

Do not fix failures in this command. Report them, and let the maintainer decide
whether a fix is in scope. Never make a gate pass by deleting a test, weakening
an assertion, or adding a tolerance.

End with one line: `GATE: PASS`, `GATE: FAIL`, or `GATE: BLOCKED`.
