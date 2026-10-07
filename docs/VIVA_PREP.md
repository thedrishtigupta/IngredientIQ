# IngredientIQ — Viva Preparation Guide

**Complete Q&A for defending your project**

---

## TABLE OF CONTENTS

1. [Project Overview & Motivation](#1-project-overview--motivation)
2. [Architecture & Design Decisions](#2-architecture--design-decisions)
3. [Technology Stack & Why](#3-technology-stack--why)
4. [Database & Data Management](#4-database--data-management)
5. [Machine Learning & NLP](#5-machine-learning--nlp)
6. [Recommendation Algorithm](#6-recommendation-algorithm)
7. [Backend API](#7-backend-api)
8. [Frontend Implementation](#8-frontend-implementation)
9. [Testing & Evaluation](#9-testing--evaluation)
10. [Deployment & DevOps](#10-deployment--devops)
11. [Challenges & Solutions](#11-challenges--solutions)
12. [Future Enhancements](#12-future-enhancements)
13. [Ethical & Practical Considerations](#13-ethical--practical-considerations)

---

## 1. PROJECT OVERVIEW & MOTIVATION

### Q1.1: What is IngredientIQ and what problem does it solve?

**Answer:**
IngredientIQ is an **explainable, ingredient-aware beauty product recommendation system** that helps users find skincare and cosmetics based on their actual ingredient composition rather than marketing claims or brand popularity alone.

**Problem it solves:**
- Consumers struggle to understand ingredient lists (complex chemical names, order matters)
- Traditional product search relies on brand names or subjective reviews
- Lack of transparency: why is this product recommended?
- No easy way to filter by specific functional needs (hydration, exfoliation, etc.)

**Our solution:**
- Parses and classifies 8,494 Sephora products by ingredient function
- Analyzes 1M+ reviews for sentiment about specific aspects
- Ranks products using 6 evidence-based signals (not just popularity)
- Shows complete score breakdowns - every number is explainable

### Q1.2: Who is the target audience?

**Answer:**
1. **Primary:** Beauty consumers who care about ingredients (ingredient-conscious shoppers)
2. **Secondary:** Dermatology-aware users looking for specific functional benefits
3. **Research:** Dataset for studying ingredient-rating correlations

**Not for:** Medical diagnosis or treatment recommendations (we explicitly state "non-medical")

### Q1.3: What makes your project unique compared to existing solutions?

**Answer:**

| Feature | IngredientIQ | Typical E-commerce |
|---|---|---|
| **Ranking basis** | Ingredient composition + sentiment | Popularity / sales |
| **Explainability** | Complete score breakdown shown | Black box |
| **LLM role** | Only writes explanations | Often picks products (unreliable) |
| **Deterministic** | Same input → same output | Often changes |
| **Ingredient-aware** | 705 ingredients classified by function | Keyword search only |
| **Review analysis** | Sentiment + aspect-level (texture, scent) | Star rating only |

**Key principle:** Data and code choose products, LLM only describes them (cannot hallucinate products).

---

## 2. ARCHITECTURE & DESIGN DECISIONS

### Q2.1: Explain the overall system architecture

**Answer:**

```
┌─────────────┐
│   Frontend  │  React + TanStack Start (port 8080)
│   (Client)  │  User Interface
└──────┬──────┘
       │ HTTP/JSON
       ▼
┌─────────────┐
│  Backend    │  FastAPI (Python, port 8000)
│  (API)      │  Business logic, recommendation engine
└──────┬──────┘
       │ SQL queries
       ▼
┌─────────────┐
│  Database   │  PostgreSQL 18 (Docker, port 5433)
│  (Postgres) │  Products, ingredients, reviews, signals
└─────────────┘
```

**Flow for a recommendation:**
1. User selects goals, category, budget on frontend
2. Frontend sends POST to `/recommend` endpoint
3. API queries database for matching products
4. Recommendation engine scores each product (6 signals)
5. LLM (OpenRouter) writes friendly summaries
6. JSON response with ranked products + explanations
7. Frontend displays results with score breakdowns

### Q2.2: Why did you separate frontend and backend?

**Answer:**

**Advantages of separation:**
1. **Independent scaling:** Can deploy API separately if needed
2. **Multiple clients:** Same API can serve web, mobile, or other frontends
3. **Security:** Database credentials never exposed to browser
4. **Technology choice:** Best tool for each layer (React for UI, Python for ML/data)
5. **Testing:** Can test API logic independently

**Trade-off:** Slightly more complex deployment (2 processes instead of 1)

### Q2.3: Why did you choose port 5433 for PostgreSQL instead of default 5432?

**Answer:**
**Problem:** During setup, discovered local PostgreSQL installation already using port 5432, causing conflict.

**Solution:** 
- Changed `docker-compose.yml` to map `5433:5432`
- Updated `.env` to `PGPORT=5433`
- All code reads from `.env`, so no hardcoding

**Advantage:** Docker container and local Postgres coexist without interference.

---

## 3. TECHNOLOGY STACK & WHY

### Q3.1: Why Python for the backend?

**Answer:**

**Reasons:**
1. **Data science ecosystem:** NumPy (vectors), pandas (data processing), psycopg (Postgres)
2. **NLP libraries:** VADER sentiment analysis built-in
3. **FastAPI:** Modern, fast, auto-generates API documentation
4. **Team familiarity:** Easier to maintain

**Alternatives considered:**
- Node.js: Less mature ML libraries
- Java: More verbose, heavier

### Q3.2: Why React and TanStack Start for frontend?

**Answer:**

**React:**
- Component-based (reusable UI pieces)
- Large ecosystem (shadcn/ui for components)
- Good developer experience

**TanStack Start/Router:**
- Modern routing with type safety
- Server-side rendering (SSR) for better performance
- Data fetching integrated with routing

**Alternatives:**
- Vue: Smaller ecosystem
- Angular: Too heavy for this use case
- Next.js: Considered, but TanStack had better TypeScript support for our needs

### Q3.3: Why PostgreSQL instead of MySQL or MongoDB?

**Answer:**

| Feature | Why it matters for IngredientIQ |
|---|---|
| **JSONB type** | Stores aspects (sentiment per topic) efficiently |
| **Array types** | Natural for ingredient lists |
| **Full-text search** | Product/ingredient search |
| **ACID compliance** | Data integrity for product data |
| **Mature** | Well-tested, good tooling |

**Why not MongoDB:** Need structured schema, complex queries with joins (products ↔ ingredients ↔ knowledge table)

**Why not MySQL:** PostgreSQL's JSONB is faster, better array support

### Q3.4: Why Docker for the database?

**Answer:**

**Benefits:**
1. **Consistency:** Same Postgres version everywhere (18)
2. **Easy setup:** One command (`docker compose up`) starts DB
3. **Isolation:** Won't interfere with other projects
4. **Portability:** Works on Windows/Mac/Linux identically
5. **Version lock:** Dump made with PG 18 requires PG 18 to restore

**Without Docker:** Team members would need to install Postgres manually, remember credentials, restore dump individually (error-prone).

### Q3.5: Why OpenRouter instead of calling OpenAI/Google directly?

**Answer:**

**OpenRouter advantages:**
1. **One API for many models:** Can switch between GPT-4, Claude, Gemini with one line
2. **Cost optimization:** Choose cheaper models for simple tasks
3. **Fallback:** If one provider is down, try another
4. **Rate limiting handled:** Unified rate limit management

**Current model:** `google/gemini-2.5-flash-lite` (fast, cheap, good enough for summaries)

---

## 4. DATABASE & DATA MANAGEMENT

### Q4.1: Describe your database schema

**Answer:**

**Core tables:**
```
products (8,494 rows)
├── product_id (TEXT, PK): "P473671"
├── product_name, brand, category, subcategory
├── price, rating, review_count, loves_count
└── raw_ingredients (TEXT): unparsed ingredient list

ingredients (12,512 rows)
├── ingredient_id (PK)
└── canonical_name: "glycerin" (normalized)

product_ingredients (260,197 rows)  ← JOIN TABLE
├── product_id → products
├── ingredient_id → ingredients
├── position (1-based order)
├── presence_type: PRIMARY or MAY_CONTAIN
├── section: "main" or shade name
└── concentration: % if available

ingredient_knowledge (705 rows)  ← CURATED
├── ingredient_id → ingredients
├── functional_groups: ['humectant', 'emollient']
├── user_goals: ['hydration', 'barrier_support']
└── confidence: HIGH/MEDIUM/LOW
```

**Derived tables:**
```
product_functional_profiles (7,544 rows)
└── features (JSONB): {"fg_humectant": 5, "goal_hydration": 8, ...}

reviews (1,093,895 rows)
├── product_id → products
├── review_text, rating, is_recommended
└── skin_type, eye_color (user attributes)

product_review_signals (2,351 rows)  ← OUR COMPUTATION
├── product_id → products (PK)
├── avg_sentiment (-1 to 1), review_score (0 to 1)
└── aspects (JSONB): {"hydration": {mentions: 487, positive_share: 0.62}}
```

### Q4.2: Why is ingredient_knowledge only 705 out of 12,512 ingredients?

**Answer:**

**Coverage:**
- 705 ingredients = **manually curated** based on:
  - Dermatology literature
  - Cosmetic ingredient databases (INCIDecoder, Paula's Choice)
  - Common knowledge (glycerin → hydration, salicylic acid → exfoliation)

**Limitation:** 
- Many ingredients are bases/stabilizers without clear benefit claims
- Some categories weak: brightening (4 tagged), barrier_support (5)
- Trade-off: Quality over quantity (better to correctly tag 705 than guess 12,512)

**Future work:** Expand knowledge base or use LLM to classify unknowns (with human verification)

### Q4.3: How did you handle the database dump file (205 MB)?

**Answer:**

**Created with:**
```powershell
.\scripts\export_db.ps1
```
This runs `pg_dump` to create `ingredientiq_full.dump` containing:
- Schema (table definitions)
- All data (products, reviews, computed signals)
- Indexes

**Restored with:**
```powershell
.\scripts\setup_db.ps1 -Dump <path>
```
This:
1. Checks if DB already has data (skip if yes)
2. Copies dump into Docker container
3. Runs `pg_restore` with 4 parallel jobs (`-j 4`)
4. Applies migrations (e.g., `003_review_signals.sql`)

**Not committed to Git:** Too large, added `*.dump` to `.gitignore`

### Q4.4: What is the `product_functional_profiles` table used for?

**Answer:**

**Purpose:** Pre-computed feature vectors for similarity calculation

**Contents:** Each product has a JSONB with 126 numeric features:
- 37 `fg_*` (functional group counts): `fg_humectant: 5` (product has 5 humectants)
- 24 `goal_*` (goal-relevant ingredient counts): `goal_hydration: 8`
- Coverage stats, primary ingredient counts

**Why pre-compute:**
- Building vectors from scratch (joining products → ingredients → knowledge) for 8K products is slow
- Profiles are computed once offline, stored in DB
- Vector index loads profiles at API startup (~0.6s), kept in RAM

**Generated by:** `scripts/run_ingredient_parser.py` or similar


---

## 5. MACHINE LEARNING & NLP

### Q5.1: What ML/NLP techniques are used in your project?

**Answer:**

**1. Sentiment Analysis (VADER)**
- **What:** Rule-based sentiment analyzer
- **Input:** Review text
- **Output:** Compound score (-1 to +1)
- **Why VADER:** Fast, no training needed, works well for short texts
- **Alternative considered:** BERT-based models (too slow for 1M reviews)

**2. Vector Similarity (Cosine Similarity)**
- **What:** Measuring closeness of ingredient profiles
- **Math:** `cosine(A, B) = (A · B) / (||A|| * ||B||)`
- **Range:** 0 (unrelated) to 1 (identical)
- **Use:** "similarity_score" in recommendations

**3. Weighted Ensemble (Hybrid Scoring)**
- **What:** Combining 6 signals into one score
- **Weights:** `goal: 0.30, similarity: 0.20, intent: 0.15, review: 0.15, rating: 0.12, popularity: 0.08`
- **Not ML per se:** Hand-tuned weights, not learned

**No deep learning:** Intentionally kept simple for explainability

### Q5.2: Explain the sentiment analysis process in detail

**Answer:**

**Step-by-step (`src/reviews/sentiment.py`):**

1. **Preprocessing:**
   - Use `review_text` if available, else `review_title`
   - Handle empty/null reviews

2. **VADER scoring:**
   ```python
   from vaderSentiment import SentimentIntensityAnalyzer
   sia = SentimentIntensityAnalyzer()
   sentiment = sia.polarity_scores(text)['compound']  # -1 to +1
   ```

3. **Classification:**
   - Positive: `sentiment > 0.05`
   - Negative: `sentiment < -0.05`
   - Neutral: in between

4. **Aspect-level sentiment:**
   - Split review into sentences
   - If sentence contains keyword (e.g., "hydrat", "moistur"), score it
   - Aggregate per aspect (hydration, texture, scent, ...)
   - Keep aspects with ≥5 mentions

5. **Smoothing:**
   - `review_score = (n * product_avg + 20 * global_avg) / (n + 20)`
   - Prevents products with 2 good reviews from scoring 1.0
   - 20 = "virtual reviews" at global mean

6. **Storage:**
   - Save to `product_review_signals` table
   - Run once with `python -m scripts.run_review_nlp` (~12 min)

**Result:** 2,351 products have sentiment signals (all Skincare)

### Q5.3: Why VADER and not a transformer model like BERT?

**Answer:**

| Criteria | VADER | BERT/RoBERTa |
|---|---|---|
| **Speed** | 1M reviews in 12 min | ~10 hours+ |
| **Setup** | pip install, ready | Download 500MB+ model, GPU helpful |
| **Accuracy** | 0.73 correlation with ratings | Maybe 0.78-0.80 |
| **Explainability** | Word-level weights (can see "love" = +0.3) | Black box |
| **Resource needs** | Runs on CPU | GPU recommended |

**Decision:** VADER is "good enough" for this use case. The 5% accuracy gain from BERT doesn't justify 50x slower processing.

**Trade-off acknowledged:** VADER misses sarcasm, context. Example: "Not bad at all" (positive) might score neutral/negative.

### Q5.4: How do you handle products with no reviews?

**Answer:**

**Problem:** Only 2,351 of 8,494 products have reviews (only Skincare category)

**Solution:**
- Compute `NEUTRAL_REVIEW_SCORE = 0.84` (average of all reviewed products)
- In scoring, if product has no reviews: use 0.84 instead of dropping review weight
- **Why:** Dropping weight gives unfair advantage (review-less products scored without penalty)

**Display:**
- API returns `review_score: null` for products without reviews
- Frontend shows "no review data available"
- Honest about limitation

**Verified:** Evaluation showed no-review products reached fair rankings after this fix

### Q5.5: Explain cosine similarity and why you use it

**Answer:**

**What it is:**
Cosine similarity measures the angle between two vectors, ignoring magnitude.

**Formula:**
```
cos(θ) = (A · B) / (|A| * |B|)
```
Where:
- `A · B` = dot product (sum of element-wise products)
- `|A|`, `|B|` = vector lengths (Euclidean norm)

**Example:**
```
Product A: [3 humectants, 2 emollients] → vector [3, 2]
Goal "hydration": [5 humectants, 4 emollients] → vector [5, 4]

cos(θ) = (3*5 + 2*4) / (√(9+4) * √(25+16)) 
       = 23 / (3.6 * 6.4) = 0.998 ≈ 1.0  (very similar)
```

**Why use it:**
1. **Magnitude-independent:** Product with 100 ingredients isn't automatically "better" than one with 20
2. **Direction matters:** Cares about *composition* (ratios), not absolute counts
3. **Fast:** Simple dot product, computed in milliseconds for all 8K products
4. **Interpretable:** 1 = same profile, 0 = totally different

**Alternative considered:**
- Euclidean distance: Would favor longer ingredient lists
- Jaccard similarity: Only cares about presence/absence, not proportions

---

## 6. RECOMMENDATION ALGORITHM

### Q6.1: Explain the hybrid scoring system in detail

**Answer:**

**Six signals, each normalized to 0-1:**

**1. Goal Match Score (30%):**
- Counts distinct ingredients whose `user_goals` contains the requested goal
- Formula: `1 - exp(-k * n)` where `n` = matching ingredients
- `k = 3 / min(goal_ingredient_count, 20)` (adaptive)
- **Why exponential:** Diminishing returns (10 → 11 matters less than 1 → 2)

**2. Similarity Score (20%):**
- Cosine similarity between product vector and goal vector
- Goal vector = weighted sum of `goal_*` and relevant `fg_*` features
- Range: 0 (no overlap) to 1 (identical profile)

**3. Intent Score (15%):**
- Lookup in `GOAL_SUBCATEGORY_AFFINITY` dict
- Examples: `hydration + Moisturizers = 1.0`, `hydration + Cleansers = 0.5`
- Unlisted types: `0.25` (after evaluation fix)
- **Why:** Moisturizers *should* rank higher for hydration than cleansers

**4. Review Score (15%):**
- From `product_review_signals.review_score`
- If missing: use `NEUTRAL_REVIEW_SCORE = 0.84`
- Smoothed with 20 "virtual reviews" at global mean

**5. Rating Score (12%):**
- `rating / 5` (star rating normalized)
- Example: 4.5/5 → 0.90

**6. Popularity Score (8%):**
- `min((ln(1 + reviews) + ln(1 + loves)) / 25, 1)`
- Logarithm: 10 → 100 reviews matters less than 1 → 10
- Loves = "hearts" on Sephora (saved to wishlist)

**Final formula:**
```
score = 0.30*goal + 0.20*sim + 0.15*intent + 0.15*review + 0.12*rating + 0.08*pop
```

**If signal missing:** Drop it, rescale remaining weights to sum to 1

### Q6.2: Why these specific weights (30%, 20%, 15%, ...)?

**Answer:**

**Design philosophy:**
1. **Goal match highest (30%):** This is primary intent (user wants hydration)
2. **Similarity medium (20%):** Broad composition match, less precise
3. **Intent medium (15%):** Product type matters (serum vs cleanser)
4. **Review medium (15%):** Social proof, but only for 1/4 of products
5. **Rating low (12%):** Often biased (popular brands get more reviews)
6. **Popularity lowest (8%):** Avoid echo chamber (don't just show bestsellers)

**How determined:**
- Started with intuition
- Adjusted based on evaluation results
- Checked if top-10 made sense (type precision test)

**Not ML-tuned:** No training data with "correct" rankings, so manually balanced

**Trade-off acknowledged:** Different users might prefer different weights (future: let user adjust)

### Q6.3: How do you handle edge cases (no goals, multiple goals, no reviews)?

**Answer:**

**No goals:**
- Drop goal, similarity, intent scores (all require goals)
- Rank by: `review (0.33) + rating (0.27) + popularity (0.18)` (rescaled)
- Becomes "best-reviewed, highly-rated, popular products"

**Multiple goals:**
- Goal match: Count ingredients matching ANY goal
- Similarity: Goal vector = sum of individual goal vectors
- Intent: Average intent scores across goals
- Works well for related goals (hydration + soothing)
- Conflicting goals (oil control + moisturization) get lower intent scores

**No reviews (2,351 of 8,494 products):**
- Use `NEUTRAL_REVIEW_SCORE = 0.84`
- Display shows "no review data"
- Doesn't penalize or advantage product

**No ingredients (950 products):**
- Goal match = 0, similarity = 0
- Still scored on review + rating + popularity
- Rarely appears in top-10 (rank ~500+)

### Q6.4: How do you prevent "gaming" the system with long ingredient lists?

**Answer:**

**Problem:** Products with 200 ingredients could match 40 goal ingredients, beating focused serums with 15 ingredients (5 matches).

**Solutions:**

**1. Exponential decay in goal match:**
- `1 - exp(-k * n)` saturates at ~95% by n=10
- 40 matches → 0.999, 10 matches → 0.95 (only 5% difference)

**2. Similarity uses normalized vectors:**
- Vectors scaled to length 1 before comparison
- Long list ≠ automatically higher similarity

**3. Intent score:**
- Gift sets (often 200+ ingredients) have weak intent (0.25-0.5)
- Focused products (Treatments, Serums) score 0.8-1.0

**Verified:** Evaluation showed gift sets rarely reach top-10 (only 2% of 220 slots)

---

## 7. BACKEND API

### Q7.1: What endpoints does your API expose?

**Answer:**

| Method | Endpoint | Purpose | Input | Output |
|---|---|---|---|---|
| GET | `/health` | System status | - | DB connection, product counts, LLM status |
| GET | `/goals` | List supported goals | - | `[{id, label, supported_by_vectors}]` |
| GET | `/categories` | List categories + subcategories | - | `[{category, product_count, subcategories[]}]` |
| POST | `/recommend` | Main recommendation | `{goals[], category, price, ingredients}` | `{count, results[], weights, llm_used}` |
| GET | `/products?q=&limit=` | Search products | `q` (query), `limit` | `[{product_id, name, brand, price, rating}]` |
| GET | `/products/{id}` | Product detail | `product_id` | Full product: ingredients, reviews, signals |
| GET | `/products/{id}/similar` | Similar products | `product_id`, `k` (count) | `[{product, similarity}]` sorted by similarity |
| GET | `/ingredients?q=` | Search ingredients | `q` (query) | `[{ingredient_id, name, product_count}]` |
| GET | `/ingredients/{id}` | Ingredient detail | `ingredient_id` | Goals, related ingredients, products containing it |

**Documentation:** Auto-generated by FastAPI at `/docs` (Swagger UI)

### Q7.2: Explain the `/recommend` endpoint flow

**Answer:**

**1. Request validation (`RecommendBody` schema):**
```python
{
  "goals": ["hydration"],
  "category": "Skincare",
  "subcategory": null,
  "min_price": null,
  "max_price": 50,
  "required_ingredients": [],
  "excluded_ingredients": ["fragrance"],
  "top_k": 10,
  "explain": true
}
```
- Validates data types, ranges
- Returns 422 if invalid (e.g., unknown goal)

**2. Database query (`repository.py`):**
```sql
SELECT product_id, name, ... 
FROM products 
WHERE category = 'Skincare' 
  AND price <= 50
```
- Applies filters (category, price, etc.)
- Excludes products with "fragrance" in ingredient list

**3. Scoring (`engine.py`):**
- For each candidate product:
  - Fetch ingredient matches
  - Load functional profile (vector)
  - Compute 6 signals
  - Weighted average → final score
- Sort by score descending

**4. LLM explanations (`openrouter.py`):**
- Batch request (one API call for all products)
- Sends: user choices + product facts + scores
- Returns: 2-3 sentence summary per product
- If fails: template text fallback

**5. Response:**
```json
{
  "count": 128,
  "llm_used": true,
  "weights": {"goal": 0.30, "similarity": 0.20, ...},
  "request": {...},
  "results": [...]
}
```

**Time:** ~200-500ms without LLM, ~2s with LLM

---

**[File continues with sections 8-13... I'll add them in the next append]**
