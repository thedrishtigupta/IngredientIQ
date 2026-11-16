"""Apply versioned SQL migrations using the configured database secret."""
from pathlib import Path

from src.recommender.repository import ProductRepository


def main():
    repo = ProductRepository()
    try:
        repo.connection.execute(
            "CREATE TABLE IF NOT EXISTS schema_migrations "
            "(version text PRIMARY KEY, applied_at timestamptz NOT NULL DEFAULT now())"
        )
        repo.connection.commit()
        for path in sorted(Path("sql").glob("[0-9][0-9][0-9]_*.sql")):
            version = path.name.split("_", 1)[0]
            applied = repo.connection.execute(
                "SELECT 1 FROM schema_migrations WHERE version = %s", (version,)
            ).fetchone()
            if applied:
                print(f"skipped {path.name}")
                continue
            repo.connection.execute(path.read_text(encoding="utf-8"))
            repo.connection.execute("INSERT INTO schema_migrations (version) VALUES (%s)", (version,))
            repo.connection.commit()
            print(f"applied {path.name}")
    finally:
        repo.close()


if __name__ == "__main__":
    main()
