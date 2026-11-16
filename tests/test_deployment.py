import pytest

from src.api.config import allowed_origins, database_settings


def test_local_configuration_has_safe_defaults(monkeypatch):
    monkeypatch.delenv("APP_ENV", raising=False)
    monkeypatch.delenv("CORS_ORIGINS", raising=False)
    assert "http://localhost:5173" in allowed_origins()
    assert database_settings().kwargs["connect_timeout"] == 5


def test_production_requires_explicit_cors(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.delenv("CORS_ORIGINS", raising=False)
    with pytest.raises(RuntimeError, match="CORS_ORIGINS"):
        allowed_origins()


def test_production_requires_database_configuration(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("PGHOST", raising=False)
    with pytest.raises(RuntimeError, match="DATABASE_URL"):
        database_settings()


def test_database_url_is_not_logged_or_parsed_into_password(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:secret@example.test/db?sslmode=require")
    settings = database_settings()
    assert settings.conninfo.startswith("postgresql://")
    assert settings.kwargs["connect_timeout"] == 5
