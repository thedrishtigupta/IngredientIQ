# The database: what runs, and how to recreate it

## What is running

| Thing | Value |
|---|---|
| Database software | **PostgreSQL 18** (official `postgres:18` Docker image) |
| Where it runs | a Docker container named `ingredientiq-db` (defined in `docker-compose.yml`) |
| Address | `localhost:5432` |
| Database / user / password | `ingredientiq` / `postgres` / `ingredientiq` (local development defaults, set in `.env`) |
| Where the data is stored | a Docker volume `ingredientiq_pgdata` (survives restarts; deleted only by `docker compose down -v`) |
| How Python talks to it | the **psycopg 3** library (`src/recommender/repository.py`, `src/api/main.py`) |

It does **not** use a Postgres installed on Windows. If you also have a normal Postgres service
installed it is not used (keep it stopped, or it will fight for port 5432).

### "Which Postgres client?"
A *client* is the program that talks to the database server. Here there are two:
1. **Our app** uses the Python library `psycopg` (a client library, not a program with a window).
2. For admin work, use the `psql` command-line client that is **inside the container**:
   ```powershell
   docker exec -it ingredientiq-db psql -U postgres -d ingredientiq
   ```
   Useful: `\dt` (list tables), `SELECT count(*) FROM products;`, `\q` (quit).
   No local `psql` install is needed. Want a GUI? Connect pgAdmin or DBeaver to
   `localhost:5432` with the values above.

## Tables

| Table | Rows | What it holds |
|---|---|---|
| `products` | 8,494 | product catalog |
| `ingredients` | 12,512 | every distinct ingredient name |
| `product_ingredients` | 260,197 | which product has which ingredient (position, section...) |
| `ingredient_knowledge` | 705 | what each curated ingredient does (functional groups, goals) |
| `product_functional_profiles` | 7,544 | per-product counts of ingredient jobs (feeds the vectors) |
| `reviews` | 1,093,895 | cleaned customer reviews |
| `product_review_summary` | 2,351 | per-product review counts, avg rating, recommend rate |
| `product_review_signals` | 2,351 | **new:** sentiment results (see `sql/003_review_signals.sql`) |

The database is about 0.9 GB once restored.

## How the dump works (backup and restore)

A **dump** is one file that contains everything needed to rebuild a database:
the table definitions (the "CREATE TABLE ..." instructions), all the rows, the indexes and the
constraints (e.g. "every review must belong to a real product").
It is made with the tool `pg_dump` and replayed with `pg_restore`:

```
 your database ──pg_dump──►  ingredientiq_full.dump (one compressed file, ~196 MB)
                                      │  (send via Google Drive)
                                      ▼
 empty database on your friend's PC ◄──pg_restore── same file
```

- Format: *custom* (`-Fc`), compressed. It is not readable text, only `pg_restore` understands it.
- **Version rule:** a dump made by Postgres 18 can only be restored into Postgres 18 or newer.
  That is why `docker-compose.yml` pins `postgres:18`.
- Two dump files exist: the team's original `ingredientiq.dump` (no sentiment results) and our
  `ingredientiq_full.dump` (everything, including `product_review_signals`). Use the full one.
- Dumps are huge, so they are **not in GitHub** (`*.dump` is git-ignored). Share through Drive.

## Recreating it on another machine (Windows)

Needs: Docker Desktop running, and the dump file.

```powershell
git clone https://github.com/thedrishtigupta/IngredientIQ
cd IngredientIQ
.\scripts\setup_db.ps1 -Dump D:\Downloads\ingredientiq_full.dump
```

What `setup_db.ps1` does, step by step:
1. Creates `.env` from `.env.example` if missing.
2. `docker compose up -d --wait`: starts Postgres 18 and waits until it is ready (empty database).
3. If `products` already has rows it stops there (safe to re-run; `-Force` wipes and redoes).
4. Copies the dump into the container and runs `pg_restore` (a few minutes).
5. Applies `sql/003_review_signals.sql` (harmless if the table already exists).
6. Prints the row count of every table so you can compare with the table above.

To send **your** current database to someone else: `.\scripts\export_db.ps1` creates
`ingredientiq_full.dump`.

### Without Docker (alternative)
Install Postgres 18, create an empty database named `ingredientiq`, then
`pg_restore -U postgres -d ingredientiq --no-owner ingredientiq_full.dump`, and put your
connection details in `.env`.

### Rebuilding from the raw CSV files (slowest, only if you must)
`python scripts/load_database.py --reset`, then `python -m scripts.run_review_nlp`
(about 12 minutes). Details are in the main README.

## Handy commands
```powershell
docker compose up -d --wait         # start the database
docker compose stop                 # stop it (data is kept)
docker compose down -v              # DELETE it and its data (restore from the dump afterwards)
docker exec ingredientiq-db psql -U postgres -d ingredientiq -c "SELECT count(*) FROM reviews"
```
