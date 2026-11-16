# Deployment modernization summary

Implemented the approved Render Free + Neon production contract without
committing secrets or reading tagged `.env` contents. Added `render.yaml`,
`runtime.txt`, a version-aware `scripts/migrate.py`, and the
`docs/DEPLOYMENT_RENDER_NEON.md` release/rollback runbook. Production
configuration now requires explicit CORS and database settings, uses bounded
PostgreSQL timeouts/TLS, and avoids request-time DDL. The API has explicit
liveness/readiness probes, security headers, request-size limits, a generic
database error, and bounded login attempts. Frontend API URL normalization and
the Vercel environment example were updated.

Verification:
- `python -m pytest -q`: 162 passed, 1 deprecation warning.
- Focused API/users/deployment tests: 38 passed, 1 deprecation warning.
- Python compile check passed.
- `/live` returned 200 and local CORS preflight returned 200 with the expected
  allowlist headers.
- `npm ci`, lint, and build were attempted from `client/`; Windows denied
  removal of locked native files in the pre-existing `node_modules`, so those
  frontend checks remain unverified.

Limitations: no live Render or Neon credentials were available, so remote
deployment, Neon migration execution, and production HTTPS probes were not
run. Vercel remains frontend-only because the synchronous psycopg and
process-local vector index were not converted to a serverless backend.
