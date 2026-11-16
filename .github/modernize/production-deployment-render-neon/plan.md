# Modernization Plan: Production Deployment Modernization

**Project**: IngredientIQ

## Technical Framework

- **Language**: Python 3 (FastAPI) and TypeScript/React
- **Framework**: FastAPI backend; TanStack Start/Vite frontend
- **Build Tool**: pip/pytest; npm scripts in `client/package.json`
- **Database**: PostgreSQL, targeting Neon PostgreSQL in production
- **Key Dependencies**: psycopg 3, uvicorn, FastAPI, React 19, Vite 8

## Overview

IngredientIQ currently runs as a local FastAPI service and independently built
frontend. This plan establishes a production deployment contract while
preserving API and user-facing behavior. Render Free is the default backend
target because it matches the long-lived FastAPI process model; Vercel is
permitted only for the frontend, or for the backend after a bounded
compatibility spike proves that serverless execution does not require broad
risky changes. Neon PostgreSQL remains the production data store.

The work will:

- define reproducible Render/Vercel build, start, health, and runtime settings;
- validate production configuration without reading or exposing tagged `.env`
  contents;
- make CORS, frontend API routing, Neon connections, and migrations safe for
  production process/serverless lifecycles;
- harden authentication and API edges without changing supported user flows;
- verify behavior with focused backend, frontend, deployment-probe, and
  database-lifecycle tests.

## Migration Impact Summary

| Application | Original Service | New Service | Authentication | Comments |
|-------------|------------------|-------------|---------------|----------|
| FastAPI API | Local uvicorn | Render Free | Existing sessions, hardened | Default backend target |
| React frontend | Local Vite | Vercel if compatible | Existing sessions, hardened | Configure API origin |
| PostgreSQL | Local Docker DB | Neon PostgreSQL | Secret env vars only | No committed production data |

## Scope and Design Constraints

- Preserve existing endpoint contracts and recommendation/authentication
  behavior unless a security fix requires an explicitly tested change.
- Do not read, print, serialize, or expose contents of any tagged `.env` file.
  Use only variable names and non-secret presence/format checks.
- Add a bounded Vercel compatibility decision. If the FastAPI adapter,
  synchronous psycopg lifecycle, or vector-index behavior is not safe without
  broad changes, deploy the API to Render Free and keep Vercel frontend-only.
- Do not treat `ingredientiq.dump` or `ingredientiq-neon.dump` as deployment
  automation; document a controlled schema/data import and rollback procedure.
- Keep secrets in Render/Vercel/Neon secret configuration, never in the repo or
  generated logs.

## Verification Commands

Run from `D:\IngredientIQ` unless noted:

```powershell
python -m pytest -q
python -m pytest -q tests/test_api.py tests/test_users.py
python -m uvicorn src.api.main:app --host 127.0.0.1 --port 8000
curl.exe -fsS http://127.0.0.1:8000/health
curl.exe -i -X OPTIONS http://127.0.0.1:8000/health `
  -H "Origin: https://<frontend-domain>" `
  -H "Access-Control-Request-Method: GET"
Set-Location client
npm ci
npm run lint
npm run build
```

For a configured staging deployment, additionally run:

```powershell
curl.exe -fsS https://<render-api-domain>/health
curl.exe -fsS https://<frontend-domain>/
```

## Open Questions & Questionnaire

- [x] Backend hosting decision → Render Free is the default; Vercel backend is
  allowed only after a bounded compatibility check succeeds.
- [x] Frontend hosting decision → Vercel is preferred when the existing
  TanStack/Vite output can be deployed without broad risky changes.
- [x] Secrets handling → validate environment-variable names/presence only;
  never read or expose tagged `.env` contents.
- [x] Integration validation → include focused backend, frontend, deployment
  probe, CORS, auth, and Neon lifecycle tests.
