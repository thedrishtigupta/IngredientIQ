# IngredientIQ

IngredientIQ is an ingredient-aware beauty product recommendation system.

## Architecture

Data
→ Ingredient Parser
→ Ingredient Knowledge Layer
→ PostgreSQL
→ Recommendation Engine
→ Review Intelligence
→ LLM Interface
→ Frontend

## Current Status

- Data profiling: complete
- Ingredient parser: complete
- Review pipeline: complete
- Ingredient knowledge layer: complete
- PostgreSQL integration: complete
- Recommendation engine: in progress

## Local Setup

### 1. Clone

git clone <repository-url>
cd IngredientIQ

### 2. Create virtual environment

python -m venv .venv

### 3. Activate

.venv\Scripts\activate

### 4. Install dependencies

pip install -r requirements.txt

### 5. Create PostgreSQL database

CREATE DATABASE ingredientiq;

### 6. Create schema

psql -U postgres -d ingredientiq
\i sql/001_create_schema.sql
\i sql/002_expand_catalog_review_schema.sql

### 7. Configure password

set PGPASSWORD=your_password

### 8. Load data

python scripts/load_database.py --reset