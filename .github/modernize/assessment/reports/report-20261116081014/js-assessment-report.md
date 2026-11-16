# IngredientIQ production deployment assessment

**Assessment timestamp (UTC):** 2026-11-16T08:10:14Z  
**Scope:** `D:\IngredientIQ` (application code, deployment files, tests, and dependency manifests; tagged `.env` contents were not read)  
**Detected stack:** Python/FastAPI backend, React + TanStack Start/Vite frontend, PostgreSQL (Neon-compatible), optional OpenRouter LLM.

## Architecture and deployment fit

- Backend entry point is `src.api.main:app`; it uses synchronous psycopg connections and builds a read-only vector index at startup/first request (`src/api/main.py`, `src/recommender/repository.py`).
- Frontend is an independently deployable TanStack Start/Vite app under `client/`; API calls use `VITE_API_URL` and default to localhost (`client/src/lib/api.ts`).
- Local infrastructure is only PostgreSQL 18 in `docker-compose.yml`; there is no Dockerfile, `vercel.json`, `render.yaml`, Procfile, CI workflow, or production start/health configuration.
- **Vercel frontend:** structurally compatible after configuring the client root/build command and `VITE_API_URL`; the current Vite/TanStack Start config uses Nitro's Cloudflare default and needs an explicit production adapter/runtime decision.
- **Vercel FastAPI:** not deployment-ready as-is. No Vercel Python function wrapper/config is present, and the synchronous per-request database model plus startup vector-index construction needs serverless suitability testing.
- **Render Free:** more natural for the FastAPI process, but the repository lacks a service definition/start command, persistent operational configuration, and a production database migration/bootstrap path. Free-tier cold starts and resource limits are likely to make index construction and large Postgres queries a blocker.
- **Neon PostgreSQL:** application configuration is generic `PGHOST`, `PGPORT`, `PGDATABASE`, `PGUSER`, `PGPASSWORD`; this can target Neon, but SSL, pooled/serverless connection strategy, connection limits, and migration execution are not explicitly configured. The committed local dump is development data, not a deployment mechanism.

## Key findings and blockers

1. **High — no production deployment contract.** No platform manifests, pinned backend start command, build/output settings, runtime version policy, or CI deployment checks exist.
2. **High — CORS is local-only.** `CORSMiddleware` permits only `localhost`/`127.0.0.1`; a Vercel origin will be rejected. Production origin allowlisting is required, with environment-driven configuration.
3. **High — database lifecycle is process/request coupled.** A new psycopg connection is opened per request; `ensure_user_tables()` executes DDL lazily and uses a process-local flag. This is fragile with multiple workers/serverless instances and does not provide migrations.
4. **High — authentication token exposure.** The frontend stores 30-day bearer tokens in `localStorage` (`client/src/lib/session.ts`), increasing impact of any XSS. There is no visible rate limiting, account lockout, refresh/revocation policy, CSRF model, security headers, or audit/observability configuration.
5. **Medium — health semantics are incomplete for deployment.** `/health` checks database queries and reports LLM availability, but there is no readiness/liveness separation, timeout budget, dependency probe policy, or platform health configuration. Startup intentionally continues when the database is unavailable.
6. **Medium — scale/cold-start risk.** Vector index creation can happen on first request and may be duplicated under concurrent startup; recommendation and ingredient queries can be expensive. Render Free sleeping/cold starts and Vercel function limits need measured validation.
7. **Medium — secrets hygiene is partly good but incomplete.** `.gitignore` excludes `.env`/`.env.*` except `.env.example`, and code reads secrets from environment variables. However, there is no documented production secret ownership/rotation process, no explicit fail-closed validation for required database settings, and LLM request data leaves the deployment boundary.
8. **Medium — test/dependency gap.** Backend has a substantial pytest suite including `tests/test_api.py` and `tests/test_users.py`; frontend has lint/build scripts but no browser or deployment smoke-test suite. Root `package-lock.json` is not a meaningful frontend manifest; the authoritative frontend manifest is `client/package.json`.
9. **Low/Medium — dependency drift.** npm-check-updates found many available updates, including major upgrades for TypeScript 7, React ecosystem packages, Vite plugin, ESLint, Zod, Recharts, and react-day-picker. These are opportunities, not automatic production changes; they require a separate compatibility task.

## Assessment workflow output

The Java/.NET AppCAT route was not applicable: no `pom.xml`, Gradle file, `.java`, `.csproj`, `.sln`, or `.cs` indicators were found. The supported JavaScript/TypeScript assessment was run against `client/package.json` with npm-check-updates 19.6.3. It identified:

- 5 patch-level update opportunities;
- approximately 30 minor-level update opportunities;
- 16 major-level update opportunities;
- one major-zero package with potentially breaking changes.

No application code was modified by the assessment.

## Recommended task categories (not a plan)

- **Deployment contract:** choose Vercel frontend + Render/other backend target; add platform manifests, commands, runtime pins, and CI build/test gates.
- **Neon/database operations:** pooled connection strategy, SSL settings, bounded timeouts, versioned migrations, bootstrap/rollback, and production data separation.
- **API edge hardening:** environment-driven CORS, trusted origins, proxy/TLS behavior, rate limiting, request limits, security headers, structured logs, and error redaction.
- **Authentication hardening:** replace or mitigate localStorage bearer tokens, session lifetime/revocation, password abuse controls, cookie/CSRF policy, and secret rotation.
- **Readiness/performance:** separate liveness/readiness endpoints, lazy/prebuilt vector index strategy, query/index review, cold-start measurements, and load tests on the selected platform.
- **Validation and observability:** frontend browser smoke tests, backend integration tests against ephemeral/Neon test databases, deployment probes, metrics/logging/alerting, and backup/restore drills.
- **Dependency maintenance:** staged frontend upgrades with lockfile consistency, npm audit/build/lint validation, and Python dependency vulnerability scanning.

## Evidence paths

`src/api/main.py`, `src/api/db.py`, `src/api/auth.py`, `src/recommender/repository.py`, `client/src/lib/api.ts`, `client/src/lib/session.ts`, `client/vite.config.ts`, `client/package.json`, `docker-compose.yml`, `requirements.txt`, `.gitignore`, `tests/`.
