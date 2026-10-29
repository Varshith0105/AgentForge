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

## Browser verification

The local backend and Vite development server were started on
`127.0.0.1:8000` and `127.0.0.1:3000`. Landing, login, registration with a
synthetic account, the protected workspace, dashboard, settings, Swagger UI,
and the mobile landing layout were exercised. Registration initially exposed a
frontend crash when FastAPI returned structured validation errors; the
normalizer in `frontend/src/utils/errors.ts` now renders those errors safely.

AI chat was exercised but blocked by an HTTP 500 from the configured provider
in this environment. No provider success screenshot was created. Repository
analysis was not claimed because no synthetic repository was created.

## Remaining work

Validate the full test suite with installed dependencies, run the frontend
build with `npm.cmd`, verify Alembic migrations against a disposable
database, and perform manual provider/browser checks with synthetic data.
There is no verified hosted deployment or screenshot set in this checkout.
