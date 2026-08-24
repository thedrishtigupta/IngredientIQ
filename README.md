# IngredientIQ

Ingredient-aware beauty product recommendation system.

## Pipeline

```text
Data → Profiling → Ingredient Parser → Ingredient Knowledge
→ PostgreSQL → Recommendation Engine → Review Intelligence
→ Hybrid Recommendations → LLM Interface → Frontend
```

## Current Status

Completed:
- Data profiling
- Ingredient parser + tests
- Review cleaning pipeline
- Ingredient knowledge layer
- Product functional profiles
- PostgreSQL schema and data integration

Current database:
- 8,494 products
- 12,512 ingredients
- 260,197 product-ingredient records
- 705 ingredient knowledge records
- 7,544 product profiles
- 1,093,895 reviews
- 2,351 review summaries

**Next:** Basic Recommendation Engine

## Project Structure

```text
IngredientIQ/
├── data/          # documentation and local datasets
├── scripts/       # data pipelines and DB loader
├── sql/           # PostgreSQL schema
├── src/           # application/data logic
├── tests/         # tests
├── requirements.txt
└── README.md
```

Raw and processed datasets are **not tracked by Git**. They are shared separately through Google Drive.

## Setup

### 1. Clone

```bash
git clone https://github.com/thedrishtigupta/IngredientIQ
cd IngredientIQ
```

### 2. Python

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### 3. PostgreSQL

Install PostgreSQL and make sure `psql` and `pg_restore` are available in PATH.

Create the database:

```sql
CREATE DATABASE ingredientiq;
```

### 4. Restore the shared database

Download `ingredientiq.dump` from the team's Google Drive and run:

```powershell
pg_restore -U postgres -d ingredientiq path\to\ingredientiq.dump
```

Verify:

```powershell
psql -U postgres -d ingredientiq
```

```sql
\dt
SELECT COUNT(*) FROM products;
SELECT COUNT(*) FROM reviews;
```

Expected:

```text
products: 8,494
reviews: 1,093,895
```

### Rebuilding from CSVs

If you need to rebuild the database instead of using the dump:

1. Download the required processed data from Google Drive.
2. Place it under `data/processed/`.
3. Run the SQL files in `sql/`.
4. Run:

```powershell
python scripts/load_database.py --reset
```

## Team Data

Google Drive contains:

```text
IngredientIQ Data/
├── database/
│   └── ingredientiq.dump
└── processed_data/
    ├── product_info.csv
    ├── product_ingredients.csv
    ├── ingredient_knowledge_v2.csv
    ├── product_functional_profile_v2.csv
    ├── product_review_summary.csv
    └── reviews_clean.csv
```

Use the PostgreSQL dump for normal development. The CSVs are mainly needed when working on the data pipelines.

## Git Rules

Do not commit:
- Raw/processed datasets
- PostgreSQL dumps
- `.venv`
- `.env`
- Database credentials

Use:

```bash
git status
git add .
git commit -m "your message"
git push
```
