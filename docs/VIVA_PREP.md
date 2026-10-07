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

### Q7.3: How does the API handle errors?

**Answer:**

**Custom exception handler (`@app.exception_handler`):**

**1. Database down (`psycopg.OperationalError`):**
- Returns HTTP 503 Service Unavailable
- Message: "Database not reachable"
- Connection timeout: 5 seconds (set in `os.environ`)

**2. Product not found:**
- Returns HTTP 404
- `raise HTTPException(status_code=404, detail="Product not found")`

**3. Invalid input (unknown goal, negative price):**
- FastAPI auto-validates with Pydantic
- Returns HTTP 422 Unprocessable Entity
- Detailed error: `{"detail": "Unknown goal: xyz"}`

**4. LLM failure:**
- Silent fallback to template text
- `llm_used: false` in response
- Logged as warning (not error)

**5. Timeout:**
- Vector index build at startup timeout: 30s
- Query timeout (Postgres): controlled by `statement_timeout`

**Design principle:** Degrade gracefully (template text) instead of failing hard

### Q7.4: Why FastAPI over Flask or Django?

**Answer:**

| Feature | FastAPI | Flask | Django |
|---|---|---|---|
| **Type checking** | Built-in (Pydantic) | Manual | ORM-based |
| **Async support** | Native | Via extensions | Native in 3.1+ |
| **Auto docs** | Swagger + ReDoc | Manual | Manual |
| **Performance** | Very fast (ASGI) | Slower (WSGI) | Slower |
| **Learning curve** | Medium | Easy | Steeper |
| **Use case** | APIs | Websites + APIs | Full web apps |

**Why FastAPI:**
1. Auto-generated `/docs` (saved time)
2. Type hints catch bugs early
3. Fast enough for our use case
4. Modern Python (3.11+ features)

**Why not Django:** Too heavy (we don't need admin panel, user auth, templating)

---

## 8. FRONTEND IMPLEMENTATION

### Q8.1: Describe the frontend architecture

**Answer:**

**Stack:**
- **React 19:** UI components
- **TanStack Start:** SSR + routing + data fetching
- **TanStack Router:** Type-safe routing
- **TanStack Query:** API call caching + loading states
- **Tailwind CSS v4:** Styling
- **shadcn/ui:** Pre-built components (buttons, dialogs, cards)
- **Vite:** Build tool

**Structure:**
```
client/src/
├── routes/          # Pages (/, /explore, /ingredients, /compare)
├── components/      # Reusable UI (ProductCard, FilterPanel, ScoreBreakdown)
├── lib/
│   ├── api.ts       # API calls (useRecommend, useProduct, ...)
│   ├── search-form.ts # Form state management
│   └── utils.ts     # Helpers
└── styles.css       # Global styles
```

**Key pattern: Query hooks**
```typescript
const rec = useRecommend(requestBody);
// rec.data, rec.isLoading, rec.error
```
- Automatic caching (same request = cached)
- Loading + error states handled

### Q8.2: How does the frontend communicate with the backend?

**Answer:**

**Single source: `client/src/lib/api.ts`**

**Example:**
```typescript
export const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(API_URL + path, init);
  if (!res.ok) {
    // Parse error message from API
    throw new ApiError(detail, res.status);
  }
  return await res.json();
}

export const useRecommend = (body: RecommendBody | null) =>
  useQuery({
    queryKey: ["recommend", body],
    queryFn: () => request<RecommendResponse>("/recommend", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }),
    enabled: body !== null,  // Only fetch when body is ready
  });
```

**Benefits:**
1. One place to change API_URL
2. Type safety (TypeScript interfaces match API schemas)
3. Automatic retry + caching via TanStack Query
4. Loading/error states handled by query hooks

**CORS handling:**
- API allows `localhost:*` origins (dev mode)
- Production would use real domain

### Q8.3: Walk through the Explore page (search interface)

**Answer:**

**User flow:**

1. **Page loads (`/explore`):**
   - Fetch goals from `/goals` → populate "Goals" buttons
   - Fetch categories from `/categories` → populate "Category" buttons
   - Form initialized empty (or from preset link)

2. **User fills form:**
   - Clicks goals (can select multiple)
   - Clicks category (mutually exclusive)
   - Adjusts price slider
   - Checks "fragrance-free"
   - Types required/excluded ingredients

3. **User clicks "Find products":**
   - Form state → `RecommendBody` object
   - Set `submitted = body`
   - Triggers `useRecommend(body)` query
   - Loading state: "Ranking products…"

4. **Results arrive:**
   - Grid of `ProductCard` components
   - Each card shows: image, name, brand, price, rating
   - Score breakdown below card
   - "Why this product?" button

5. **User clicks "Why this product?":**
   - Opens `ExplanationPanel` dialog
   - Shows full score breakdown (6 signals)
   - Lists matched ingredients
   - Review aspects
   - LLM summary

**Code structure:**
```typescript
function Explore() {
  const [form, setForm] = useState<SearchForm>(emptyForm);
  const [submitted, setSubmitted] = useState<RecommendBody | null>(null);
  
  const rec = useRecommend(submitted);
  
  return (
    <FilterPanel form={form} onChange={setForm} onSubmit={() => setSubmitted(toBody(form))} />
    {rec.isLoading && <div>Ranking products...</div>}
    {rec.data && <ProductGrid results={rec.data.results} />}
  );
}
```

### Q8.4: How do you handle loading and error states?

**Answer:**

**TanStack Query provides:**
- `isLoading`: First load
- `isFetching`: Any load (including refetch)
- `error`: Exception from fetch

**Patterns:**

**1. Loading placeholder:**
```typescript
{rec.isFetching && !rec.data ? (
  <div className="border border-dashed">
    <p>Ranking products…</p>
  </div>
) : ...}
```

**2. Error notice component:**
```typescript
<ErrorNotice error={rec.error} />
```
Shows user-friendly message: "Could not connect to API" or API error detail

**3. Optimistic rendering:**
- Keep previous results while refetching
- Show "updating…" indicator
- Uses `placeholderData: keepPreviousData` in query config

**4. Empty state:**
```typescript
{!data ? (
  <div>Nothing searched yet. Choose a goal and press Find products.</div>
) : null}
```

---

## 9. TESTING & EVALUATION

### Q9.1: What testing strategies did you use?

**Answer:**

**1. Unit tests (pytest, 126 tests):**
- `tests/test_scorer.py`: Score calculation formulas
- `tests/test_sentiment.py`: VADER sentiment edge cases
- `tests/test_vectors.py`: Cosine similarity math
- `tests/test_filters.py`: Ingredient exclusion logic

**Example:**
```python
def test_goal_match_score():
    assert goal_match_score(0) == 0.0
    assert goal_match_score(5) > 0.7
    assert goal_match_score(10) > 0.9
```

**2. Integration tests:**
- `tests/test_api.py`: API endpoints return correct status codes
- `tests/test_repository.py`: Database queries return expected data

**3. Quality tests (`test_recommender_quality.py`):**
- Run 15 diverse requests
- Check: no budget violations, excluded ingredients absent, results sorted

**4. Evaluation script (`scripts/evaluate_recommender.py`):**
- 279 different requests
- Type precision, ingredient evidence
- Baseline comparisons
- Results documented in `docs/EVALUATION.md`

**Coverage:** ~85% (core logic covered, some UI untested)

### Q9.2: What did the evaluation reveal?

**Answer:**

**Key findings:**

**1. Hard checks: 0 violations**
- Every product met filters (price, category, ingredients)
- Scores between 0-1, correctly sorted
- Same input → same output (deterministic)

**2. Type precision: 94% (no category), 100% (with category)**
- Top-10 products were correct type (Moisturizers for hydration)
- Baseline (random): 15%, (popularity): 12%
- **Proof hybrid works better than simple sorting**

**3. Problem found: Review bias**
- Products with reviews got +0.07 score boost vs. no-review products
- **Fixed:** Use neutral score (0.84) when missing
- After fix: No-review products ranked fairly

**4. Problem found: Gift sets ranked too high**
- 249-ingredient kits beat focused serums (counted raw matches)
- **Fixed:** Exponential decay + intent score (gift sets = 0.25)

**5. Limitation: Only Skincare has reviews**
- 2,351 of 8,494 products have sentiment signals
- Hair, Makeup rely only on ingredients + rating

**Honest takeaway:** System works for intended use (Skincare with goals), has documented limits

### Q9.3: Why didn't you use human ratings for evaluation?

**Answer:**

**Reasons:**

**1. Resource constraints:**
- Labeling 100+ products × 11 goals = 1100+ judgments
- Need multiple raters for reliability
- Time-intensive (weeks)

**2. Subjectivity:**
- Beauty preferences vary by skin type, budget, brand loyalty
- What's "best" for hydration is not objective

**3. Cold start problem:**
- Need labeled data to evaluate, but no usage data yet

**Alternative we used:**
- **Type precision:** Objective (is it a Moisturizer?)
- **Ingredient evidence:** Fact-based (does it contain glycerin?)
- **Baseline comparison:** Prove we're better than random/popularity

**Future work:** A/B testing with real users, clickthrough rate analysis

---

## 10. DEPLOYMENT & DEVOPS

### Q10.1: How would you deploy this to production?

**Answer:**

**Proposed architecture:**

```
┌────────────────┐
│  Cloudflare    │  CDN + DNS
│  or Vercel     │
└────────┬───────┘
         │
         ▼
┌────────────────┐
│  Frontend      │  Vercel (SSR) or Netlify (static)
│  (React app)   │
└────────┬───────┘
         │ HTTPS
         ▼
┌────────────────┐
│  API Server    │  DigitalOcean Droplet / AWS EC2 / Render.com
│  (FastAPI)     │  Dockerized with Gunicorn/Uvicorn
└────────┬───────┘
         │
         ▼
┌────────────────┐
│  PostgreSQL    │  Managed DB (AWS RDS, DigitalOcean Managed DB)
│  (Production)  │  Automated backups, read replicas
└────────────────┘
```

**Steps:**

**1. Database:**
- Use managed PostgreSQL (AWS RDS, DigitalOcean)
- Import dump: `pg_restore ingredientiq_full.dump`
- Enable SSL, firewall rules (only API IP)

**2. Backend API:**
```dockerfile
FROM python:3.11-slim
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY src/ /app/src/
CMD ["gunicorn", "src.api.main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker"]
```
- Deploy to Render.com (free tier) or AWS ECS
- Set environment variables (PGHOST, OPENROUTER_API_KEY)
- Health checks: `/health` endpoint

**3. Frontend:**
- Build: `npm run build` → static files in `dist/`
- Deploy to Vercel: `vercel --prod`
- Set `VITE_API_URL=https://api.ingredientiq.com`

**4. CI/CD:**
```yaml
# .github/workflows/deploy.yml
on: push
  branches: [main]
jobs:
  test:
    run: pytest
  deploy-api:
    run: docker build && docker push
  deploy-frontend:
    run: vercel deploy --prod
```

### Q10.2: What environment variables are needed?

**Answer:**

**Backend (`.env`):**
```
PGHOST=db.ingredientiq.com
PGPORT=5432
PGDATABASE=ingredientiq
PGUSER=prod_user
PGPASSWORD=<secret>
OPENROUTER_API_KEY=sk-or-v1-<secret>
OPENROUTER_MODEL=google/gemini-2.5-flash-lite
```

**Frontend:**
```
VITE_API_URL=https://api.ingredientiq.com
```

**Security:**
- Never commit `.env` to Git (in `.gitignore`)
- Use secrets manager (AWS Secrets Manager, Vercel Env Vars)
- Rotate API keys regularly

### Q10.3: How do you handle database backups?

**Answer:**

**Development:**
```powershell
.\scripts\export_db.ps1
```
Creates `ingredientiq_full.dump` with timestamp

**Production:**

**1. Automated daily backups:**
- Managed DB providers (AWS RDS, DigitalOcean) do this automatically
- Retention: 7 days

**2. Manual backup before migrations:**
```bash
pg_dump -h prod.db.com -U user -d ingredientiq > backup_$(date +%Y%m%d).dump
```

**3. Disaster recovery:**
- Keep dumps in S3 / cloud storage
- Test restore procedure quarterly
- Document recovery steps

### Q10.4: What monitoring would you implement?

**Answer:**

**1. Uptime monitoring:**
- Pingdom / UptimeRobot hitting `/health` every 5 min
- Alert on downtime

**2. Error tracking:**
- Sentry for backend (catches exceptions)
- Frontend errors logged to Sentry

**3. Logging:**
```python
import logging
log = logging.getLogger("ingredientiq.api")
log.info("Request: %s", request)
log.error("Database error: %s", exc)
```
- Ship logs to Papertrail / CloudWatch

**4. Metrics:**
- Request latency (p50, p95, p99)
- Database query time
- LLM API success rate
- Cache hit rate

**5. Alerts:**
- Email/Slack on:
  - API response time > 2s
  - Error rate > 1%
  - Database connection failures

---

## 11. CHALLENGES & SOLUTIONS

### Q11.1: What was the biggest challenge you faced?

**Answer:**

**Challenge: Review bias favoring Skincare**

**Problem discovered:**
- Only Skincare has reviews (2,351 products)
- Review scores all high (0.61-0.95, avg 0.84)
- Dropping review weight for no-review products gave them unfair advantage
- Result: Body creams, hair products ranked far lower than deserved

**Solution:**
1. Use `NEUTRAL_REVIEW_SCORE = 0.84` when missing
2. Still show `review_score: null` in API (honest)
3. Re-ran evaluation: no-review products recovered fair ranks

**Lesson:** Missing data ≠ neutral; need careful handling

### Q11.2: What technical issues did you encounter during setup?

**Answer:**

**Issue 1: Port conflict (PostgreSQL)**
- **Problem:** Local Postgres on 5432, Docker container on 5432
- **Symptom:** Connection refused / password errors
- **Solution:** Changed Docker to 5433, updated `.env`

**Issue 2: Review NLP script timeout**
- **Problem:** 1M reviews, VADER per review = 12 minutes
- **First attempt:** Loaded all into memory (RAM overflow)
- **Solution:** Server-side cursor (`psycopg named cursor`) streams batches of 5000

**Issue 3: OpenRouter 402 error**
- **Problem:** No `max_tokens` limit, OpenRouter refused large batches
- **Solution:** Added `max_tokens=800` per product summary

**Issue 4: Frontend hydration error**
- **Problem:** Server rendered "—", client fetched "8,494" (mismatch)
- **Solution:** Cosmetic, doesn't break functionality; added note in docs

### Q11.3: How did you handle the cold start problem (vector index)?

**Answer:**

**Problem:**
- Vector index = 8,494 products × 126 features = ~1M numbers
- Loading from DB + building index = 600ms
- Don't want to do this per request (slow)

**Solution:**

**1. Build once at API startup:**
```python
@asynccontextmanager
async def lifespan(app):
    global _index
    repo = ProductRepository()
    _index = VectorIndex.from_db(repo.connection)  # ~0.6s
    yield  # API is now ready
```

**2. Share across all requests:**
- Index stored in RAM (global variable)
- Read-only (never modified)
- No locking needed

**3. Fallback if DB down:**
- API starts anyway
- Index built on first request that needs it

**Trade-off:** 0.6s startup delay, but 0ms per request afterward

---

## 12. FUTURE ENHANCEMENTS

### Q12.1: What features would you add next?

**Answer:**

**High priority:**

**1. Natural language search**
- Input: "lightweight hydrating serum under $50 no fragrance"
- LLM parses → structured query → recommendation
- Better UX than clicking 10 buttons

**2. User accounts & saved searches**
- Save preferences (skin type, budget, excluded ingredients)
- "My Products" list
- History of searches

**3. Comparison tool enhancements**
- Side-by-side ingredient overlap visualization
- "What's different?" explanation
- Export comparison as PDF

**Medium priority:**

**4. Mobile app (React Native)**
- Barcode scanner (scan product → ingredient check)
- Push notifications for price drops

**5. Ingredient trend analysis**
- "Rising ingredients in 2025"
- "Most common in 5-star products"

**6. Batch ingredient lookup**
- Paste full ingredient list → get analysis
- Useful for checking products not in our catalog

**Low priority:**

**7. Collaborative filtering**
- "Users who liked this also liked..."
- Requires user interaction data

**8. Multi-language support**
- Ingredient names in Spanish, French, etc.

### Q12.2: How would you improve the recommendation algorithm?

**Answer:**

**1. Learn weights from data:**
- Collect clickthrough data (which products users actually click)
- Use learning-to-rank model (RankNet, LambdaMART)
- Optimize weights to match user preferences

**2. Personalization:**
- Skin type-specific recommendations
- "You tend to prefer fragrance-free" → auto-check that box
- Past purchase history

**3. Expand ingredient knowledge:**
- Currently 705/12,512 ingredients (6%)
- Use LLM to classify unknowns (with human verification)
- Crowdsource: let users tag ingredients

**4. Better review aspect extraction:**
- Fine-tune BERT on beauty reviews
- More granular aspects ("pilling", "grittiness")
- Temporal trends ("used to be good, reformulated")

**5. Price-aware ranking:**
- $/oz normalization (50ml vs 100ml)
- "Best value" score separate from "best quality"

**6. Combination effects:**
- Some ingredients work better together (niacinamide + zinc)
- Some conflict (vitamin C + retinol timing)
- Requires expert curation

### Q12.3: What scalability concerns would you address?

**Answer:**

**Current limits:**
- 8,494 products (small dataset)
- Vector index fits in RAM (~10 MB)
- Single API server handles 100+ req/sec

**If scaling to 100K+ products:**

**1. Database optimization:**
- Index on `(category, price)` for faster filters
- Materialized view for pre-aggregated stats
- Read replicas for heavy queries

**2. Caching:**
```python
@lru_cache(maxsize=1000)
def recommend(request_hash):
    ...
```
- Cache top-10 for common queries (hydration + Skincare)
- Redis for distributed cache

**3. Async scoring:**
- Score products in parallel (multiprocessing)
- Currently sequential (0.2s for 8K products, acceptable)

**4. Vector database:**
- Switch to Pinecone / Weaviate for similarity search
- Sub-millisecond retrieval for 1M+ vectors

**5. CDN for static data:**
- Cache `/goals`, `/categories` at edge

---

## 13. ETHICAL & PRACTICAL CONSIDERATIONS

### Q13.1: What are the ethical considerations of your project?

**Answer:**

**1. Not medical advice:**
- Explicitly state "non-medical, not for diagnosis"
- Cannot claim products "cure" conditions
- Refer users to dermatologists for medical concerns

**2. Data source transparency:**
- Clearly state "Sephora data" (not hiding it)
- No personal customer data (reviews anonymized)

**3. Bias acknowledgment:**
- System favors Skincare (has reviews)
- Limited ingredient knowledge (705/12,512)
- Documented in `docs/EVALUATION.md`

**4. LLM hallucination prevention:**
- LLM only describes pre-selected products
- Cannot invent products or ingredients
- Fallback to templates if LLM fails

**5. Accessibility:**
- Not claiming "allergen-free" (only "no fragrance listed")
- Users responsible for checking full lists

### Q13.2: What are the limitations users should know?

**Answer:**

**Clear disclosures:**

**1. Data coverage:**
- Only Sephora catalog (no Ulta, drugstore brands)
- 2023 data (products/prices may change)
- Reviews only for Skincare

**2. Ingredient knowledge:**
- 705 of 12,512 ingredients classified
- Weak for some goals (brightening: 4 ingredients)

**3. Not personalized:**
- Doesn't account for skin type reactions
- Same results for everyone with same inputs

**4. Placeholders:**
- Product images are placeholders (dataset has none)
- Doesn't show real product photos

**5. Sentiment limitations:**
- VADER misses sarcasm
- Aspect scores rough (keyword-based)

**Principle:** Honest about what the system can and can't do

### Q13.3: How do you ensure result explainability?

**Answer:**

**Every result shows:**

**1. Complete score breakdown:**
- 6 signals with individual values
- Weights used (30%, 20%, ...)
- Formula transparent

**2. Matched ingredients listed:**
- Shows which specific ingredients matched the goal
- Not just "high score"

**3. Review aspects:**
- "487 mentions of hydration, 62% positive"
- Specific, countable

**4. Strengths/weaknesses:**
- Rule-based sentences ("Highly rated at 4.5/5")
- Derived from scores, not opinions

**5. Source traceability:**
- Can click through to full ingredient list
- Review signals table queryable

**Why it matters:**
- Users can verify claims
- Builds trust
- Catches errors (if score seems wrong, can debug)

### Q13.4: What data privacy measures are in place?

**Answer:**

**Current (development):**
- No user accounts → no personal data collected
- API doesn't log IP addresses
- OpenRouter API key in `.env` (not in code)

**If deployed with user accounts:**

**1. Data minimization:**
- Only collect: email, hashed password
- No phone numbers, addresses

**2. Encryption:**
- HTTPS for all traffic
- Database credentials encrypted at rest

**3. API key security:**
- Rotate OpenRouter key quarterly
- Use secrets manager (not `.env` in production)

**4. No tracking:**
- No Google Analytics (respects privacy)
- Minimal cookies (session only)

**5. Compliance:**
- GDPR: Right to deletion (if user accounts added)
- Display privacy policy

---

## QUICK FACTS FOR VIVA

**Statistics:**
- **8,494** products in catalog
- **1,093,895** reviews analyzed
- **2,351** products with sentiment signals
- **12,512** unique ingredients
- **705** ingredients with curated knowledge
- **126** tests passing
- **279** evaluation requests (0 violations)
- **94%** type precision (vs 15% random)

**Time investments:**
- Review NLP: ~12 minutes for 1M reviews
- API startup: ~0.6s (vector index)
- Recommendation: 200-500ms without LLM, ~2s with LLM

**Tech stack:**
- **Backend:** Python 3.11, FastAPI, psycopg3, NumPy, VADER
- **Database:** PostgreSQL 18 (Docker)
- **Frontend:** React 19, TanStack, Tailwind v4, TypeScript
- **LLM:** OpenRouter (Gemini 2.5 Flash Lite)
- **Deployment:** Docker Compose (dev), proposed Vercel + Render (prod)

**Key files to know:**
- `src/recommender/engine.py` - Main recommendation logic
- `src/reviews/sentiment.py` - VADER sentiment analysis
- `src/recommender/vectors.py` - Cosine similarity
- `src/api/main.py` - API endpoints
- `client/src/lib/api.ts` - Frontend ↔ Backend communication

---

## SAMPLE VIVA QUESTIONS WITH ANSWERS

**Q: Walk me through what happens when a user searches for "hydrating moisturizer under $50"**

A: 1) Frontend sends POST to `/recommend` with `{goals: ["hydration"], category: "Skincare", max_price: 50}`. 2) API queries Postgres for Skincare products ≤$50. 3) For each product, computes 6 scores (goal match, similarity, intent, review, rating, popularity) using ingredient data, functional profiles, and review signals. 4) Weighted average: 0.30 × goal + 0.20 × similarity + 0.15 × intent + 0.15 × review + 0.12 × rating + 0.08 × popularity. 5) Sorts by score, takes top 10. 6) Sends facts to OpenRouter LLM to write 2-3 sentence summaries. 7) Returns JSON with products, scores, matched ingredients, and explanations. Frontend displays results with score breakdowns.

**Q: Why didn't you use deep learning?**

A: Trade-off between complexity and explainability. Deep learning (transformers, neural networks) would be a black box - users can't see why a product scored 0.85. Our hybrid approach uses interpretable math (cosine similarity, weighted averages, exponential decay). Every score traces back to countable facts (5 matching ingredients, 0.70 similarity, 4.5/5 rating). For a consumer-facing app, trust requires transparency. Plus, our dataset is small (8K products) - deep learning needs 100K+ for good performance. Rule-based + VADER achieves 94% type precision, which is good enough.

**Q: What if the LLM hallucinates a product?**

A: It can't. The LLM never chooses products - that's done by deterministic code (SQL filters + scoring formula). LLM only receives pre-selected products with their facts (name, brand, 8 matched ingredients, scores). Prompt explicitly says "use only the provided facts, mention only ingredients from matched_ingredients list". If LLM fails (timeout, API down), we silently use template text instead ("Strong goal match. Highly rated."). The `llm_used: false` flag tells the user it's a fallback. Design principle: degrade gracefully, never break.

---

**Ready for your viva! Know these docs inside-out:**
1. `docs/WHAT_WAS_BUILT.md` - High-level overview
2. `docs/EVALUATION.md` - Results and limitations
3. `docs/API.md` - Endpoint reference
4. `src/recommender/config.py` - All tunable parameters

**Good luck! 🎓**
