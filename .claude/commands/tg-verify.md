---
description: Run the full local TradeGuard validation gate and report exact results
---

Run the local validation gate in this order. Run every step even if an earlier
one fails, so the report is complete, then summarize.

First set the per-session prerequisites from `CLAUDE.md` §3:

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
9. `.venv\Scripts\pip-audit.exe --skip-editable`
10. `npm audit --prefix web --omit=dev --audit-level=high`

Expected baseline as of 2026-08-30 on `main` (R3): 236 passed, 2 deselected,
90.70% coverage, 2 web tests passing. On the R4 candidate branch the same gate
is 253 passed, 2 deselected, 90.10% coverage. Compare against the baseline for
the branch under test; a drop below it is a regression, not a new baseline.

Steps 9 and 10 mirror the `Dependency scans` CI job. Both reach the network:
`pip-audit` queries PyPI and `npm audit` queries the npm registry. A network
failure is `BLOCKED`, never `FAIL` and never `PASS` — it is not a vulnerability
finding. The `Container scan` CI job (Trivy) has no local equivalent here;
report it as `SKIP: CI-only`, never `PASS`.

Step 9 is weaker than the CI check and must not be reported as equivalent. CI
runs `uv sync --locked` first, so it audits exactly what `uv.lock` pins. Calling
`.venv\Scripts\pip-audit.exe` directly audits whatever is currently installed in
`.venv`, which can drift from `uv.lock` because `uv` is not on PATH in this
working copy (§3.1). A green step 9 therefore means "the installed environment
has no known vulnerability", not "the lockfile is clean". Only the CI job, or
`make audit` where `uv` is available, proves the latter. When step 9 is green
but `uv.lock` was changed in the same task, say so explicitly.

If step 4 fails with `ModuleNotFoundError: No module named 'tradeguard'` or a
`PermissionError` on `.pytest-tmp`, that is a known working-copy defect listed
in `CLAUDE.md` §3.1. Report it as an environment defect and do not change
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
