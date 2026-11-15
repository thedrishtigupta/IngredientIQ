"""Per-request database access shared by every API module."""
from pathlib import Path

from psycopg.rows import dict_row

from src.recommender.repository import ProductRepository

SQL_DIR = Path(__file__).resolve().parents[2] / "sql"


_user_tables_ready = False


def get_repo():
    """One repository (= one DB connection) per request, always closed afterwards.
    FastAPI reuses it within a request, so every dependency that asks for it shares one connection."""
    repo = ProductRepository()
    try:
        ensure_user_tables(repo.connection)  # normally done at startup; covers "database was down then"
        yield repo
    finally:
        repo.close()


def query(repo, sql, params=()):
    """Run a statement and return the rows as a list of dicts."""
    with repo.connection.cursor(row_factory=dict_row) as cur:
        cur.execute(sql, params)
        return cur.fetchall() if cur.description else []


def query_one(repo, sql, params=()):
    rows = query(repo, sql, params)
    return rows[0] if rows else None


def ensure_user_tables(connection):
    """Create the account tables if they are missing (sql/004_users.sql is idempotent). Once per process."""
    global _user_tables_ready
    if _user_tables_ready:
        return
    connection.execute((SQL_DIR / "004_users.sql").read_text(encoding="utf-8"))
    connection.commit()
    _user_tables_ready = True
