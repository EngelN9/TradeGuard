# Bootstrap Evidence

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

Generated evidence is intentionally ignored by Git. It must not contain
environment values, credentials, account details, or other secrets.
