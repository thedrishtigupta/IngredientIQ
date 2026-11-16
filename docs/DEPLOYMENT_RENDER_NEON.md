# Production deployment: Render Free + Neon

The API runs as a long-lived Render Free web service. The Vercel deployment is
frontend-only; the current synchronous psycopg connection and in-process vector
index do not meet a serverless backend compatibility gate without a broader
change.

## Render

Create the service from `render.yaml`. Set `DATABASE_URL`, `CORS_ORIGINS`
(comma-separated exact HTTPS frontend origins), `OPENROUTER_API_KEY` (optional),
and `OPENROUTER_MODEL` in Render's secret environment settings. Do not commit
values or copy a tagged `.env` file. `DATABASE_URL` is used with a five-second
connect timeout, a ten-second statement timeout, and TLS required in production.

Run migrations before the first release from a trusted environment:

```powershell
python -m scripts.migrate
```

The command reads the database secret from the environment, applies numbered
SQL files in order, and does not restore `ingredientiq.dump` files. Take a Neon
restore point/backup before migrations. Roll back by redeploying the previous
application revision and restoring a reviewed backward-compatible SQL backup;
never run destructive SQL as an automatic startup action.

Render probes `/live` for cheap liveness and `/ready` for database readiness.
`/health` retains the application health response and includes product counts.

## Vercel frontend

Set the project root to `client/`, install with `npm ci`, build with `npm run
build`, and set `VITE_API_URL` to the Render HTTPS URL (the client normalizes a
trailing slash). Configure the same URL in Render's `CORS_ORIGINS`.

## Release and security checks

```powershell
python -m pytest -q
python -m pytest -q tests/test_api.py tests/test_users.py
Set-Location client; npm ci; npm run lint; npm run build
```

Use `/live`, `/ready`, and a browser smoke test after deployment. Rotate the
Neon password and OpenRouter key through their secret managers. Sessions are
stored as hashes, expire after 30 days, and are revoked on logout. Login
attempts are bounded per process; use Render/edge rate limiting for distributed
abuse protection. Logs must not contain authorization headers, passwords,
connection URLs, environment contents, or LLM keys.
