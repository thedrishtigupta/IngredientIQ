# Deployment execution plan

Source of truth: `.github/modernize/production-deployment-render-neon/plan.md`
and its task metadata. Execute the approved Render Free + Neon plan without
changing application behavior or reading tagged `.env` values.

Scope:
- Render Free FastAPI contract and Vercel frontend configuration.
- Environment validation, explicit CORS, frontend API URL handling.
- Neon-safe PostgreSQL connection settings and explicit migrations.
- Security headers, bounded auth sessions, redacted errors, and health/readiness.
- Focused tests plus backend/frontend/build validation.

Validation:
`python -m pytest -q`; focused API/user tests; `npm ci`, `npm run lint`,
`npm run build`; local liveness/readiness and CORS probes where the database
is available. Tagged `.env` files must not be read or exposed.
