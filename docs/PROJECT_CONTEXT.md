# IngredientIQ — Project Context (handoff + LLM context file)

> **How to use this file with an LLM:** paste the whole file at the start of a chat and say
> *"You are helping me understand/extend this project. Use only this context and the code I show you;
> say so if something is not covered."* It is written to be self-contained and accurate as of the
> commit that added it. Function names are given instead of line numbers because line numbers drift.
> Beginner-friendly walkthrough: `docs/WHAT_WAS_BUILT.md`. Database details: `docs/DATABASE.md`.

---

## 1. What the project is
IngredientIQ recommends beauty products (Sephora catalog) based on **what is in them** and
**what reviewers say**. The user picks a goal (e.g. hydration), optionally a category, budget and
"fragrance-free". The system returns a ranked list with a plain-English reason per product.

**Core design principle:** the *data and scoring code choose the products*. The LLM only
*describes* products that were already chosen. It cannot add or invent products.
Everything works without the LLM (template text fallback).

## 2. Architecture

```
React website (client/, port 8080/8081)
        │  HTTP/JSON   (client/src/lib/api.ts)
        ▼
FastAPI (src/api/main.py, port 8000)
        │
        ├─► RecommendationEngine (src/recommender/engine.py)
        │      1. SQL candidates (category / subcategory / price)           repository.py
        │      2. Python filters (required / excluded ingredients, fragrance) filters.py
        │      3. For each product, 6 signals -> 1 score                      scorer.py
        │      4. Sort, take top_k, build rule-based strengths/weaknesses     explanations.py
        │
        ├─► LLM (src/llm/openrouter.py): facts + user choices -> 2-3 sentences per product
        │
        └─► Postgres 18 in Docker (localhost:5432, db "ingredientiq")
```

Offline pipelines (run once, results stored in Postgres): ingredient parser, review cleaning,
**review sentiment** (`scripts/run_review_nlp.py`).
Vectors are **not** stored: built in memory at API start (about 0.6 s).

## 3. Repository map

| Path | Purpose |
|---|---|
| `src/ingredients/` | Parses raw ingredient text into structured records (commas inside brackets, sections, `May Contain`, CI codes, percentages) |
| `src/reviews/sentiment.py` | VADER sentiment, topic ("aspect") sentiment, smoothing, per-product signal |
| `src/recommender/config.py` | **All tunable numbers:** `HYBRID_WEIGHTS`, `GOAL_LABELS`, `GOAL_SUBCATEGORY_AFFINITY`, `NEUTRAL_REVIEW_SCORE`, `UNLISTED_SUBCATEGORY_INTENT`, `UNRELIABLE_ASPECTS`, `MIN_ASPECT_MENTIONS` |
| `src/recommender/vectors.py` | `VectorIndex`: product vectors + cosine similarity (numpy only) |
| `src/recommender/scorer.py` | Pure functions turning raw numbers into 0..1 signals and the final score |
| `src/recommender/engine.py` | `RecommendationEngine.recommend(request)` orchestrates everything |
| `src/recommender/repository.py` | All SQL used by the recommender (psycopg 3) |
| `src/recommender/filters.py` | Hard filters incl. "fragrance-free" |
| `src/recommender/explanations.py` | Deterministic strengths/weaknesses text from the scores |
| `src/recommender/models.py` | `RecommendationRequest`, `RecommendationResult`, `RecommendationExplanation` |
| `src/llm/openrouter.py` | OpenRouter call, prompt rules, template fallback, `user_choices()` |
| `src/api/main.py`, `schemas.py` | FastAPI app and request/response models |
| `client/` | React 19 + TanStack Start/Router + Tailwind v4 + shadcn/ui (generated with Lovable) |
| `sql/001..003_*.sql` | Schema; 003 adds `product_review_signals` |
| `scripts/` | `setup_db.ps1`, `export_db.ps1`, `run_review_nlp.py`, `evaluate_recommender.py`, `load_database.py`, `run_ingredient_parser.py`, `run_review_pipeline.py` |
| `tests/` | 126 pytest tests (DB-backed ones skip if Postgres is down) |
| `docs/` | `API.md`, `DATABASE.md`, `EVALUATION.md`, `WHAT_WAS_BUILT.md`, this file |
| `docker-compose.yml`, `.env.example` | Local Postgres 18 and settings template |

## 4. Data (Postgres tables)

| Table | Rows | Purpose / key columns |
|---|---|---|
| `products` | 8,494 | `product_id` (TEXT like `P473671`), `product_name`, `brand`, `category`, `subcategory`, `price`, `rating`, `review_count`, `loves_count`, `raw_ingredients`, flags |
| `ingredients` | 12,512 | `ingredient_id`, `canonical_name` (lowercased) |
| `product_ingredients` | 260,197 | `product_id`, `ingredient_id`, `position`, `presence_type` (PRIMARY / MAY_CONTAIN), `section`, `concentration`, `ci_codes`, `markers` |
| `ingredient_knowledge` | 705 | curated: `functional_groups`, `user_goals`, `roles`, `fragrance_related`, `confidence` |
| `product_functional_profiles` | 7,544 | `features` JSONB, 126 keys: `fg_<job>` and `goal_<goal>` counts (+ `_primary_` variants, coverage columns) |
| `reviews` | 1,093,895 | cleaned reviews incl. `review_text`, `rating`, `is_recommended`, `skin_type`, ... |
| `product_review_summary` | 2,351 | per-product counts, average rating, recommendation rate |
| `product_review_signals` | 2,351 | **ours:** `avg_sentiment`, `positive_share`, `negative_share`, `review_score` (0..1), `aspects` JSONB |

Facts that matter:
- Only **Skincare** products have reviews (2,351 of 2,420). Other categories have none.
- 945 products have no ingredient list; about 194 more have a profile but no classified ingredient: **no vector** (similarity 0).
- Ingredient knowledge covers 705 of 12,512 ingredients (weak for brightening: 4, barrier_support: 5, exfoliation: 5, hair_conditioning: 10).
- Product ids are **text**, not numbers.

## 5. How a recommendation is computed

**Request:** `goals`, `category`, `subcategory`, `min_price`, `max_price`, `required_ingredients`,
`excluded_ingredients` (`"fragrance"` removes products with an ingredient containing "fragrance" or "parfum"), `top_k`.
Filters are applied first; scoring only ranks what survives.

**Six signals, each 0..1** (`scorer.py`, weights in `config.HYBRID_WEIGHTS`, sum = 1):

| Signal | Weight | Calculation |
|---|---|---|
| goal (ingredient match) | 0.30 | `n` = number of the product's distinct ingredients whose knowledge `user_goals` contains the goal (SQL in `repository.get_goal_matches`); score = `1 - exp(-k*n)` with `k = 3 / min(goal ingredient count, 20)` |
| similarity | 0.20 | cosine(goal vector, product vector), see below |
| intent | 0.15 | lookup `GOAL_SUBCATEGORY_AFFINITY[goal][subcategory]` (e.g. hydration + Moisturizers = 1.0); unlisted type for a known goal = 0.25; unknown goal = 0.5; averaged over goals |
| review | 0.15 | `product_review_signals.review_score`; **no reviews -> 0.84** (`NEUTRAL_REVIEW_SCORE`) in the score only, while the result still shows `review_score = null` |
| rating | 0.12 | `rating / 5` |
| popularity | 0.08 | `min((ln(1+reviews) + ln(1+loves)) / 25, 1)` |

`hybrid_score` = weighted average. Any signal that is `None` is dropped and the remaining weights
are rescaled. With **no goals**, goal/similarity/intent are dropped. Ties break on `product_id`
(deterministic: same request + same DB = same output).

**Vectors** (`vectors.py`): each product = 62 numbers: 37 `fg_*` (ingredient jobs, e.g. humectant)
+ 24 `goal_*` + 1 `unknown_ingredients`, scaled to length 1. A goal vector puts weight on
`goal_<goal>` plus the `fg_*` jobs that at least half of that goal's curated ingredients have
(hydration -> `goal_hydration` + `fg_humectant`). Several goals add. Cosine similarity is one line:
`matrix[rows] @ goal_vector` (dot product of two unit vectors), clipped to 0..1.
`similar_products` compares one product's vector with all others (API restricts to the same category).

**Review sentiment** (`sentiment.py`): VADER `compound` (-1..1) per review (text, else title).
Positive > 0.05, negative < -0.05. Per product: `own = (avg+1)/2`;
`review_score = (n*own + 20*global_mean) / (n + 20)` (smoothing so few reviews cannot look perfect).
Topics (hydration, texture, scent, irritation, absorption, packaging, value, effectiveness): sentences
containing keywords are scored separately; kept if >= 5 mentions; explanations use >= 10 mentions and
**never quote "irritation"** (`UNRELIABLE_ASPECTS`: "no irritation at all" scores negative).

**LLM** (`openrouter.py`): one batched call per request. Sends: shopper's choices (`user_choices(request)`:
goals, category, budget, fragrance-free, excluded/required ingredients) + per-product facts (name, brand, price,
rating, up to 8 matched ingredients, scores, best/worst review topic, strengths/weaknesses).
Rules in the system prompt: use only given facts, no medical claims, mention ingredients only from
`matched_ingredients`, say "no fragrance or parfum listed" (never "allergen-free"), 2-3 sentences, JSON out.
Default model `google/gemini-2.5-flash-lite` (`OPENROUTER_MODEL`). `max_tokens` is capped (otherwise
OpenRouter returns 402 when credits are low). Any failure -> deterministic `template_summary`.
`llm_used` in the API response is true only if the LLM really wrote at least one text.

## 6. API (full examples in `docs/API.md`, live docs at `/docs`)

`GET /health` · `GET /goals` · `GET /categories` · `GET /products?q=&category=&limit=` ·
`GET /products/{id}` · `GET /products/{id}/similar?k=` · `GET /ingredients`, `/ingredients/{id}` ·
`POST /recommend` body `{goals, category, subcategory, min_price, max_price, required_ingredients,
excluded_ingredients, top_k (1..20), explain}` -> `{count, llm_used, request, weights, results[]}`.
Each result: product facts + `score`, `goal_match_score`, `similarity_score`, `intent_score`,
`review_score`, `rating_score`, `popularity_score`, `matched_goals`, `matched_ingredients`, `aspects`,
`explanation {strengths, weaknesses, summary}`. Unknown goal -> 422; unknown product -> 404; DB down -> 503.

Supported user goals (`GOAL_LABELS`): hydration, moisturization, brightening, exfoliation, antioxidant,
soothing, oil_control, uv_protection, cleansing, barrier_support, hair_conditioning.

## 7. Setup and commands (Windows)

```powershell
# needs Docker Desktop, Python 3.11+, Node 22
.\scripts\setup_db.ps1 -Dump <path>\ingredientiq_full.dump     # DB (restores once, safe to re-run)
python -m venv .venv ; .venv\Scripts\activate ; pip install -r requirements.txt
copy .env.example .env                                         # add OPENROUTER_API_KEY to enable the LLM
python -m uvicorn src.api.main:app --port 8000                 # API
cd client ; npm install ; npm run dev                          # website (8080, or 8081 if taken)
python -m pytest -q                                            # 126 tests
python -m scripts.evaluate_recommender --quick                 # quality checks (full run ~6 min)
python -m scripts.run_review_nlp                               # recompute sentiment (~12 min)
```

`.env` keys: `PGHOST PGPORT PGDATABASE PGUSER PGPASSWORD` (defaults match docker-compose),
`OPENROUTER_API_KEY`, `OPENROUTER_MODEL`. **`.env` is git-ignored; never commit keys or dump files.**

## 8. Results so far (details in `docs/EVALUATION.md`)
- 279 requests, 0 rule violations (filters, ordering, determinism, formula).
- Right product type in top 10 (no category filter): hybrid 94% vs 11-15% for random / popularity-only / rating-only.
- Sentiment vs star rating correlation 0.73; `review_score` vs catalog rating 0.65.

## 9. Known limitations (be honest about these)
- Reviews only for Skincare; other categories rank on ingredients, rating, popularity.
- `oil_control` with no category can return makeup powders (they contain oil-absorbing ingredients).
- "Fragrance-free" cannot check products with no ingredient list; required ingredients match exact names.
- Mini and full-size of one product can both appear.
- VADER is word-based: misses sarcasm; topic scores are rough. Vector similarity is small for narrow goals.
- Evaluation has no human labels; "ingredient evidence" uses the same knowledge table as the goal score (partly circular).
- Product images are placeholders (dataset has none). Research page is a placeholder (no results).

## 10. Gotchas
- Windows: set `PYTHONUTF8=1` if a script prints symbols and crashes on cp1252.
- Port 8080 may be taken (Vite then uses 8081); API allows any `http://localhost:*` origin.
- Do not run `docker compose down -v` unless you want to delete the database (restore from the dump).
- The dump was made with Postgres 18; it only restores into 18+. `docker-compose.yml` pins `postgres:18`.
- Heavy on RAM: Docker + Postgres + Vite + API together can exhaust a small machine.
- `client/` was generated by Lovable (see `client/AGENTS.md`): do not rewrite pushed git history.

## 11. How to extend
- **New goal:** tag ingredients with it in `ingredient_knowledge.user_goals`, add it to `GOAL_LABELS` and
  `GOAL_SUBCATEGORY_AFFINITY` in `config.py`, make sure a `goal_<name>` feature exists in the profiles.
- **Change ranking:** edit `HYBRID_WEIGHTS` (keep the sum at 1), rerun `evaluate_recommender`.
- **Better sentiment:** replace `sentiment()` in `src/reviews/sentiment.py` (e.g. transformer model or
  the Jev classifier), rerun `run_review_nlp`. Nothing else changes.
- **Per-skin-type reviews:** `reviews.skin_type` exists; aggregate sentiment per (product, skin_type).
- **More ingredient knowledge:** grow `ingredient_knowledge` (705 of 12,512 mapped), then regenerate profiles.

## 12. Glossary
Vector: list of numbers describing something. Cosine similarity: how alike two vectors are, 0..1.
Hybrid: several signals combined into one score. Sentiment: positive/negative mood of text. VADER: word-list
sentiment tool. Smoothing: pulling small samples toward the average. Endpoint: a URL the website calls.
Prompt: instructions + facts sent to an LLM. Fallback: backup behaviour when something fails.
Dump: one file that can rebuild the whole database (`pg_dump` / `pg_restore`).
