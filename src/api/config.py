"""Environment-backed deployment configuration.

Only variable names and safe, non-secret settings are inspected here. Secret
values are passed directly to the database driver and are never logged.
"""
import os
from dataclasses import dataclass
from urllib.parse import urlparse


def _csv(name: str) -> list[str]:
    return [item.strip().rstrip("/") for item in os.getenv(name, "").split(",") if item.strip()]


def is_production() -> bool:
    return os.getenv("APP_ENV", "").lower() in {"production", "prod"}


def allowed_origins() -> list[str]:
    origins = _csv("CORS_ORIGINS")
    if is_production() and not origins:
        raise RuntimeError("CORS_ORIGINS must be configured in production")
    return origins or ["http://localhost:3000", "http://localhost:5173"]


@dataclass(frozen=True)
class DatabaseSettings:
    conninfo: str | None
    kwargs: dict


def database_settings() -> DatabaseSettings:
    url = os.getenv("DATABASE_URL")
    if url:
        parsed = urlparse(url)
        if parsed.scheme not in {"postgres", "postgresql"} or not parsed.hostname:
            raise RuntimeError("DATABASE_URL must be a PostgreSQL connection URL")
        # Keep the URL opaque; psycopg handles the password and TLS options.
        return DatabaseSettings(url, {"connect_timeout": int(os.getenv("PGCONNECT_TIMEOUT", "5"))})
    if is_production() and not os.getenv("PGHOST"):
        raise RuntimeError("DATABASE_URL or PGHOST must be configured in production")
    kwargs = {
        "host": os.getenv("PGHOST", "localhost"),
        "port": os.getenv("PGPORT", "5432"),
        "dbname": os.getenv("PGDATABASE", "ingredientiq"),
        "user": os.getenv("PGUSER", "postgres"),
        "password": os.getenv("PGPASSWORD"),
        "connect_timeout": int(os.getenv("PGCONNECT_TIMEOUT", "5")),
        "options": "-c statement_timeout=10000",
    }
    if os.getenv("PGSSLMODE"):
        kwargs["sslmode"] = os.environ["PGSSLMODE"]
    elif is_production():
        kwargs["sslmode"] = "require"
    return DatabaseSettings(None, kwargs)
