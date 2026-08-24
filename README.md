# IngredientIQ

IngredientIQ is an ingredient-aware beauty product recommendation system.

The project combines product metadata, structured ingredient data, ingredient-level
knowledge, and review intelligence to build explainable product recommendations.

---

## Project Pipeline

The planned system is:

```text
DATA
  ↓
Data Profiling
  ↓
Ingredient Parser
  ↓
Ingredient Knowledge Layer
  ↓
Product + Ingredient Database
  ↓
Basic Recommendation Engine
  ↓
Explainable Ranking
  ↓
Review Intelligence
  ↓
Hybrid Recommendation Engine
  ↓
Natural Language / LLM Interface
  ↓
Frontend
  ↓
Evaluation
```

The current work is focused on building a reliable data and database foundation
before implementing the recommendation engine.

---

# Current Status

## Completed

### Phase 0 — Project Foundation

- Repository structure established
- Python environment configured
- PostgreSQL database configured
- Database schema created
- Database loading pipeline created

### Phase 1 — Data Understanding & Profiling

Completed for the product catalog and review data:

- Dataset profiling
- Missing-value analysis
- Duplicate analysis
- Ingredient structure analysis
- Review data analysis
- Parser edge cases
- Data pipeline documentation

### Phase 2 — Ingredient Parser

The ingredient parser processes raw product ingredient lists and handles
structures including:

- Parentheses
- Sections
- `May Contain`
- Shades
- Steps
- Percentages
- CI codes
- Ingredient markers
- Ingredient normalization

The parser produces product → ingredient records.

Main code:

```text
src/ingredients/
```

Pipeline:

```text
scripts/run_ingredient_parser.py
```

### Phase 3 — Review Pipeline

The review dataset has been cleaned and deduplicated.

Current cleaned review count:

```text
1,093,895 reviews
```

The pipeline also generates product-level review summaries.

Pipeline:

```text
scripts/run_review_pipeline.py
```

### Phase 4 — Ingredient Intelligence

The ingredient knowledge layer maps canonical ingredients to:

- Functional groups
- User goals
- Ingredient roles
- Fragrance-related properties
- Colorant-related properties
- Knowledge metadata

Current knowledge records:

```text
705 ingredients
```

Product-level functional profiles have also been generated.

### PostgreSQL Data Layer

The processed data has been loaded into PostgreSQL.

Current database:

```text
Products                         8,494
Ingredients                     12,512
Product-ingredient records     260,197
Ingredient knowledge               705
Product functional profiles      7,544
Reviews                      1,093,895
Review summaries                 2,351
```

Validation:

```text
Orphan product-ingredient records    0
Orphan ingredients                   0
Orphan reviews                       0
```

The database has been validated using product/ingredient, ingredient/knowledge,
product/review, and review-summary relationships.

---

# Project Structure

```text
IngredientIQ/
│
├── README.md
├── requirements.txt
├── .gitignore
│
├── data/
│   ├── Ingredient-Data-Profiling.md
│   ├── Ingredient-Parser-Test_Contract.md
│   ├── Review-Data-Pipeline.md
│   ├── README.md
│   └── ingredient_parser_fixtures.json
│
├── scripts/
│   ├── load_database.py
│   ├── run_ingredient_parser.py
│   ├── run_review_pipeline.py
│   └── update_review_quality_report.py
│
├── sql/
│   ├── 001_create_schema.sql
│   ├── 002_expand_catalog_review_schema.sql
│   └── README.md
│
├── src/
│   ├── __init__.py
│   └── ingredients/
│       ├── __init__.py
│       ├── models.py
│       ├── normalizer.py
│       ├── parser.py
│       ├── pipeline.py
│       └── quality.py
│
└── tests/
    ├── test_ingredient_parser.py
    ├── test_parser_real_edge_cases.py
    ├── test_review_pipeline_contract.py
    └── fixtures/
        └── ingredient_parser_fixtures.json
```

---

# Data

The actual datasets are intentionally excluded from GitHub because of their
size.

They are shared separately through the team's Google Drive.

## Raw Data

```text
product_info.csv

reviews_0-250.csv
reviews_250-500.csv
reviews_500-750.csv
reviews_750-1250.csv
reviews_1250-end.csv
```

## Processed Data

```text
product_ingredients.csv
ingredient_knowledge_v2.csv
product_functional_profile_v2.csv
product_review_summary.csv
reviews_clean.csv
```

The PostgreSQL database dump is also shared separately:

```text
ingredientiq.dump
```

---

# Local Setup

## 1. Clone the Repository

```bash
git clone https://github.com/thedrishtigupta/IngredientIQ
cd IngredientIQ
```

---

## 2. Create a Python Virtual Environment

On Windows:

```powershell
python -m venv .venv
```

Activate it:

```powershell
.venv\Scripts\activate
```

You should see:

```text
(.venv)
```

in your terminal prompt.

---

## 3. Install Python Dependencies

```powershell
pip install -r requirements.txt
```

---

# PostgreSQL Setup

IngredientIQ uses PostgreSQL as its database.

## 1. Install PostgreSQL

Install PostgreSQL for Windows from the official PostgreSQL website.

During installation, make sure the PostgreSQL server and command-line tools
are installed.

The default PostgreSQL port is:

```text
5432
```

Remember the password created for the `postgres` user.

---

## 2. Verify PostgreSQL

Open a new terminal and run:

```powershell
psql --version
```

You should get a PostgreSQL version.

Also verify:

```powershell
pg_restore --version
```

Both commands should be available from the terminal.

If Windows cannot find them, add the PostgreSQL `bin` directory to PATH.

A typical installation path is:

```text
C:\Program Files\PostgreSQL\<version>\bin
```

---

# Create the IngredientIQ Database

Connect to PostgreSQL:

```powershell
psql -U postgres
```

Create the database:

```sql
CREATE DATABASE ingredientiq;
```

Exit:

```sql
\q
```

Connect to the new database:

```powershell
psql -U postgres -d ingredientiq
```

---

# Recommended Team Setup: Restore the Shared Database

For normal development, teammates should use the shared PostgreSQL dump
instead of rebuilding the entire database from CSV files.

Download:

```text
ingredientiq.dump
```

from the team's Google Drive.

Create the database first if it does not already exist:

```sql
CREATE DATABASE ingredientiq;
```

Then exit PostgreSQL:

```sql
\q
```

Restore the dump:

```powershell
pg_restore -U postgres -d ingredientiq path\to\ingredientiq.dump
```

Example:

```powershell
pg_restore -U postgres -d ingredientiq D:\Downloads\ingredientiq.dump
```

The restore may take some time because the database contains more than one
million reviews.

---

# Verify the Restored Database

Connect:

```powershell
psql -U postgres -d ingredientiq
```

List tables:

```sql
\dt
```

You should see:

```text
ingredient_knowledge
ingredients
product_functional_profiles
product_ingredients
product_review_summary
products
reviews
```

Check products:

```sql
SELECT COUNT(*) FROM products;
```

Expected:

```text
8494
```

Check reviews:

```sql
SELECT COUNT(*) FROM reviews;
```

Expected:

```text
1093895
```

---

# Rebuilding the Database From CSVs

The shared dump is the preferred setup method.

However, the database can be rebuilt from the processed datasets if necessary.

## 1. Download the required processed data

From Google Drive, download the processed datasets.

Place them in:

```text
data/
└── processed/
    ├── product_ingredients.csv
    ├── ingredient_knowledge_v2.csv
    ├── product_functional_profile_v2.csv
    ├── product_review_summary.csv
    └── reviews_clean.csv
```

The product catalog should be placed in:

```text
data/raw/product_info.csv
```

---

## 2. Create the database schema

Connect to PostgreSQL:

```powershell
psql -U postgres -d ingredientiq
```

Run:

```sql
\i 'path/to/sql/001_create_schema.sql'
\i 'path/to/sql/002_expand_catalog_review_schema.sql'
```

---

## 3. Configure the PostgreSQL Password

PowerShell:

```powershell
$env:PGPASSWORD="YOUR_POSTGRES_PASSWORD"
```

CMD:

```cmd
set PGPASSWORD=YOUR_POSTGRES_PASSWORD
```

---

## 4. Run the Database Loader

```powershell
python scripts/load_database.py --reset
```

The loader performs:

```text
Products
   ↓
Ingredients
   ↓
Product Ingredients
   ↓
Ingredient Knowledge
   ↓
Product Functional Profiles
   ↓
Reviews
   ↓
Review Summaries
   ↓
Validation
```

The final validation should show zero orphan relationships.

---

# Database Schema

The current database contains seven main tables.

```text
products
   │
   ├── reviews
   │      └── product_review_summary
   │
   ├── product_functional_profiles
   │
   └── product_ingredients
          │
          └── ingredients
                 │
                 └── ingredient_knowledge
```

## `products`

Stores product catalog information and product metadata.

## `ingredients`

Stores the canonical ingredient vocabulary.

## `product_ingredients`

Connects products to their ingredients.

It also stores parser-derived information such as:

- Ingredient position
- Presence type
- Section
- Concentration
- CI codes
- Markers
- Original ingredient text

## `ingredient_knowledge`

Stores ingredient-level intelligence:

- Functional groups
- User goals
- Roles
- Fragrance-related properties
- Colorant-related properties
- Knowledge metadata

## `product_functional_profiles`

Stores product-level functional features derived from ingredient knowledge.

## `reviews`

Stores the cleaned review dataset.

## `product_review_summary`

Stores aggregated review information at the product level.

---

# Running the Pipelines

## Ingredient Parser

```powershell
python scripts/run_ingredient_parser.py
```

## Review Pipeline

```powershell
python scripts/run_review_pipeline.py
```

## Tests

```powershell
pytest
```

The parser tests and review pipeline contract tests are located under:

```text
tests/
```

---

# Development Workflow

The repository contains the code and database definitions.

Large datasets and the populated PostgreSQL database are stored separately
in Google Drive.

The normal workflow is:

```text
Clone GitHub repository
        ↓
Create Python environment
        ↓
Install dependencies
        ↓
Install PostgreSQL
        ↓
Download ingredientiq.dump
        ↓
Restore PostgreSQL database
        ↓
Run tests
        ↓
Start development
```

Do not commit the following to GitHub:

```text
Raw datasets
Processed datasets
PostgreSQL dumps
.venv
.env
Passwords
Database credentials
```

---

# Team Data Location

The shared Google Drive contains:

```text
IngredientIQ Data/
│
├── database/
│   └── ingredientiq.dump
│
└── processed_data/
    ├── product_info.csv
    ├── product_ingredients.csv
    ├── ingredient_knowledge_v2.csv
    ├── product_functional_profile_v2.csv
    ├── product_review_summary.csv
    └── reviews_clean.csv
```

Use the PostgreSQL dump for normal development.

The processed CSVs are mainly required when working on or rebuilding the
data pipelines.

---

# Next Development Phase

The data foundation is complete.

The next major phase is:

```text
Basic Recommendation Engine
```

The recommendation engine will eventually use:

- User requirements
- Product category
- Budget
- Ingredient matching
- Ingredient functional properties
- Product similarity
- Ratings
- Popularity
- Review-derived signals

The planned architecture keeps product selection deterministic.

Later, an LLM can be used for:

1. Converting natural-language user requirements into structured requirements.
2. Turning computed recommendation evidence into natural-language explanations.

The LLM should not independently decide which products are recommended.
