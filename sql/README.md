# IngredientIQ — Database Integration (New Files Only)

This package contains only the new files for the PostgreSQL integration step.

## Before loading

1. Your `001_create_schema.sql` should already have been executed.
2. Execute `sql/002_expand_catalog_review_schema.sql`.
3. Install the Python PostgreSQL driver:

```bash
pip install "psycopg[binary]" pandas
```

4. Put the generated data artifacts in:

```text
data/
├── raw/
│   └── product_info.csv
└── processed/
    ├── product_ingredients.csv
    ├── ingredient_knowledge_v2.csv
    ├── product_functional_profile_v2.csv
    ├── reviews_clean.csv
    └── product_review_summary.csv
```

The existing Phase 3 pipeline already generates the review files. The Phase 4D package supplies the knowledge/profile files.

## Configure PostgreSQL credentials

PowerShell:

```powershell
$env:PGPASSWORD="YOUR_POSTGRES_PASSWORD"
```

CMD:

```cmd
set PGPASSWORD=YOUR_POSTGRES_PASSWORD
```

The defaults are:

```text
host=localhost
port=5432
database=ingredientiq
user=postgres
```

You can override them with `PGHOST`, `PGPORT`, `PGDATABASE`, and `PGUSER`.

## Run

From the project root:

```bash
python scripts/load_database.py
```

For a completely fresh reload:

```bash
python scripts/load_database.py --reset
```

Do NOT use `--reset` unless you are intentionally rebuilding the database.

## Important

The loader is intentionally staged in this order:

1. products
2. ingredients
3. product_ingredients
4. ingredient_knowledge
5. product_functional_profiles
6. reviews
7. product_review_summary

The script validates foreign-key integrity at the end.

It does not modify the raw CSV files.
