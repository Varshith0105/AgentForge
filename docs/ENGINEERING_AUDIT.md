# Engineering audit

## Scope

This audit compares the checked-in source with the prior repository claims and
checks the backend, frontend, configuration, and security-sensitive routes.

## Confirmed findings and changes

- The README described a static multi-page frontend that is not present; it
  now documents the React/Vite application.
- Wildcard credentialed CORS and predictable secret defaults were replaced
  with validated settings.
- Terminal and tool command execution no longer accept arbitrary shell input.
- Git paths are confined to `WORKSPACE_ROOT`, and clone URLs are restricted to
  GitHub.
- Analysis status and upload project updates now enforce ownership.
- ZIP extraction rejects traversal entries.
- Compose secrets are supplied by environment variables instead of committed
  values.

## Baseline verification

The system Python did not have `pytest`, and PowerShell execution policy
blocked the `npm.ps1` shim. Use the repository virtual environment's Python
and `npm.cmd` on Windows. Docker Compose syntax was parsed successfully before
the required-secret placeholders were introduced.

## Remaining work

Validate the full test suite with installed dependencies, run the frontend
build with `npm.cmd`, verify Alembic migrations against a disposable
database, and perform manual provider/browser checks with synthetic data.
There is no verified hosted deployment or screenshot set in this checkout.
