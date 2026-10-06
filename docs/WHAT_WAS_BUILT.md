# IngredientIQ — what was built, in simple words

Written for people new to tech. Read top to bottom; each part says **what it is**,
**what the project had before**, **what was added**, and **what to study**.

---

## 0. The big picture (one minute)

IngredientIQ recommends beauty products. You tell it what you want
("hydrating, Skincare, under $50, no fragrance") and it gives you a ranked list
with a short reason for each product.

**Idea:** decide using **facts from the data** (ingredients, reviews, ratings), not
a chatbot's guess. A chatbot (the LLM) is only used at the very end to
*write the reason in friendly English*.

```
Your request
   │
   ▼
Database (Postgres)  ──►  Scoring code  ──►  Top 10 products  ──►  LLM writes the reason  ──►  Website
 products, ingredients,    6 signals mixed       (ranked list)       (OpenRouter)               (frontend)
 1M+ reviews               into one score
```

---

## 1. What the project ALREADY had (before this work)

| Piece | Plain meaning |
|---|---|
| Cleaned data | 8,494 Sephora products, ~1.09 million customer reviews |
| Ingredient parser | Turns the messy ingredient text into a clean list per product |
| Ingredient knowledge table | 705 ingredients labelled with what they do (e.g. glycerin → hydration) |
| Database design (Postgres) | Tables for products, ingredients, reviews and a loader script |
| Simple recommender | Ranked products by ingredient match + rating + popularity |
| Template explanations | Fixed sentences like "Highly rated at 4.5/5" |
| Website (frontend) | Looked good, but showed **12 made-up products**, not real data |
| 40 tests | Automatic checks that the code behaves |

## 2. What was ADDED / CHANGED (this work)

### A. The database now runs in Docker (so it is easy to share)
- **Before:** you had to install Postgres yourself, remember a password, and load data by hand.
- **Now:** one file `docker-compose.yml` starts Postgres in a "container" (a small
  sealed box that has Postgres inside). `scripts/setup_db.ps1` restores the data with one command.
  `scripts/export_db.ps1` packs the whole database (including our new results) into one file
  (`ingredientiq_full.dump`) to send to someone.
- **Study:** what a database is, what Docker/containers are (just the idea), what a "dump/backup" is.

### B. Review sentiment analysis ("do reviewers like this product?")
- **Before:** reviews were stored but never read by the computer.
- **Now:** `src/reviews/sentiment.py` reads every review (1,093,895 of them) and gives it a
  mood score from -1 (angry) to +1 (happy) using **VADER**, a ready-made word-based tool
  (it knows "love" is good and "terrible" is bad). Then, per product, we save:
  average mood, % positive, % negative, a final **review score (0–1)**, and mood about
  specific topics (hydration, texture, scent, packaging, value...). Saved in a new table
  `product_review_signals`. Run it with `python -m scripts.run_review_nlp` (about 12 minutes).
- **Fairness trick:** a product with only 3 reviews is "pulled toward the average" so it
  cannot look perfect by luck (called *smoothing*).
- **Result:** the review mood agrees with star ratings (correlation 0.73 — meaning that when the text is happy, the stars are usually high).
- **Limit:** only 2,351 products have reviews (all Skincare). Others show "no review data".
- **Study:** sentiment analysis, what "correlation" means, why we smooth small samples.

### C. Product vectors + cosine similarity ("how close is this product to what I want?")
- **Before:** only "how many matching ingredients".
- **Now:** `src/recommender/vectors.py` (~120 lines, only numpy).
  - A **vector** is just a list of numbers. Each product becomes a list saying how much of its
    ingredient list does each *job* (moisturizer-type, exfoliant, antioxidant...).
  - Your goal (e.g. "hydration") also becomes a list of numbers (the jobs hydration needs).
  - **Cosine similarity** compares two lists: 1 = pointing the same way (very similar),
    0 = unrelated.
- **Study:** vectors as lists of numbers, cosine similarity (the angle between two arrows), numpy basics.

### D. The hybrid recommender (the "brain")
- **Before:** score = 55% ingredient match + 25% product type + 15% rating + 5% popularity.
- **Now:** six signals mixed (`src/recommender/config.py`, `scorer.py`, `engine.py`):

  | Signal | Weight | Meaning |
  |---|---|---|
  | Ingredient match | 30% | how many of the goal's helpful ingredients it contains |
  | Vector similarity | 20% | cosine similarity from part C |
  | Product type | 15% | is it the right kind of product (moisturizer for hydration)? |
  | Review sentiment | 15% | from part B |
  | Rating | 12% | star rating |
  | Popularity | 8% | reviews + "loves" |

- **Rules for missing data:** no goal given → ignore goal-based signals. No reviews → score it
  with an *average* review value (so products are neither rewarded nor punished for having
  or lacking reviews); the screen still honestly says "no review data".
- **Same input → same output** (deterministic), so results are explainable and testable.
- **Extra fixes:** "fragrance-free" now removes products containing "fragrance" or "parfum";
  11 user goals supported (hydration, brightening, exfoliation, soothing, oil control, UV protection...).
- **Study:** weighted average, why normalising scores to 0–1 matters, trade-offs of choosing weights.

### E. LLM explanations (OpenRouter)
- **Before:** fixed sentences made by `if` rules.
- **Now:** `src/llm/openrouter.py`. After the code has chosen the top products, we send the
  *facts* (name, ingredients, scores) to a small AI model (`google/gemini-2.5-flash-lite`
  through OpenRouter) and ask it to write 2–3 friendly sentences per product.
- **Important design rule:** the LLM never chooses products. It can't invent a product,
  because it only describes the ones already picked. If the LLM fails or there is no key,
  the app silently uses template sentences instead, so it never breaks.
- **Bug found and fixed while testing:** our request did not limit the reply length, so
  OpenRouter refused (HTTP 402, "not enough credits for 65k tokens"). We added `max_tokens`.
  The API field `llm_used` is now only `true` if the LLM really wrote the text.
- **Study:** what an LLM is, what a *prompt* is, *tokens*, API keys (never put them in code
  or GitHub — ours lives only in the git-ignored `.env` file), why "fallbacks" matter.

### F. The backend API (FastAPI)
- **Before:** none. The website could not talk to the database.
- **Now:** `src/api/main.py`. An **API** is a waiter between the website and the database:
  the website sends a request, the API gets the data and replies in JSON.

  | Endpoint | Does |
  |---|---|
  | `POST /recommend` | main feature: goals, category, budget → ranked products + reasons |
  | `GET /products/{id}` | one product: ingredients, review signals |
  | `GET /products/{id}/similar` | similar products (same category) |
  | `GET /goals`, `/categories`, `/ingredients`, `/health` | lists and a "is it alive?" check |

  Open http://localhost:8000/docs to try it in the browser. Full reference: `docs/API.md`.
- **Study:** what an API/endpoint/JSON is, GET vs POST, HTTP status codes (200 ok, 404 not found, 422 bad input, 503 DB down).

### G. The website (frontend) now uses real data
- **Before:** 12 fake products and a fake scoring formula inside the browser.
- **Now:** same design (nothing redesigned), but the data layer was replaced:
  the Explore page has a real form (goal, category, budget, fragrance-free) and shows real
  ranked products with a "Why this product?" panel; Product, Compare, Ingredients and Home
  pages also use real data. `client/src/lib/api.ts` is the one file that talks to the API.
- **Study:** React basics, "fetching data from an API", loading/error states.

### H. Testing and evaluation ("does it actually make sense?")
- Tests went from **40 to 124** (`python -m pytest -q`).
- `scripts/evaluate_recommender.py` ran **279 different requests with 0 rule violations**
  (budget respected, excluded ingredients never appear, same input gives same output).
- It also compared our ranking to dumb baselines. With no category chosen, **94% of our top 10
  were the right product type, versus 11–15% for random / most-popular / best-rated.**
  Details and honest limits: `docs/EVALUATION.md`.
- Problems the evaluation found, and what we did: reviewed products had an unfair bonus
  (fixed with the average-review rule), wrong product types scored too high (fixed),
  spaces in a category name broke search (fixed), the "irritation" review topic gave misleading
  warnings (removed from explanations).
- **Study:** why we test, baselines (comparing against simple alternatives), precision.

### I. Housekeeping
`requirements.txt` rewritten (it was in a wrong file encoding and listed unused packages),
`.gitignore` updated (zips, dumps, `.env`), `.env.example` added, README updated.

---

## 3. A request, step by step (what to explain to teachers)

1. User picks **Hydration + Skincare + under $50 + fragrance-free** on the website.
2. The website sends it to `POST /recommend`.
3. The API asks the database for matching products and removes anything over $50 or containing fragrance.
4. For each remaining product it computes the 6 signals and mixes them into one score.
5. It sorts by score and keeps the top 10.
6. The LLM turns each product's facts into 2–3 friendly sentences (or templates if the LLM is unavailable).
7. The website shows the list, scores and "Why this product?".

## 4. Words to know

| Word | Simple meaning |
|---|---|
| Database / Postgres | organised storage of tables, searchable with SQL |
| Docker | runs software (Postgres) in a sealed box, same everywhere |
| Sentiment analysis | computer guessing if text is positive or negative |
| Vector | a list of numbers describing something |
| Cosine similarity | how alike two vectors are (0 to 1) |
| Hybrid | mixing several signals into one decision |
| API / endpoint | a URL the website calls to get data |
| LLM | a text-writing AI model |
| Prompt | the instructions + facts you send to an LLM |
| Fallback | a backup plan when something fails |
| Frontend / backend | what you see (website) / what works behind it (API + database) |

## 5. Suggested study order for newcomers
1. What a database and a table are → look at `sql/001_create_schema.sql`.
2. Python basics, then read `src/recommender/scorer.py` (short, plain maths).
3. Sentiment analysis idea → `src/reviews/sentiment.py`.
4. Vectors and cosine similarity → `src/recommender/vectors.py`.
5. APIs → open http://localhost:8000/docs and click "Try it out".
6. LLMs and prompts → `src/llm/openrouter.py`.
7. Last: the website → `client/src/lib/api.ts`, then `client/src/routes/explore.tsx`.

## 6. Honest limits (say these out loud — it shows understanding)
- Reviews exist only for Skincare (2,351 products); other categories rely on ingredients, rating and popularity.
- Ingredient knowledge covers 705 of 12,512 ingredients; weak for goals like brightening (4 ingredients).
- Sentiment uses a simple word-based tool; topic-level scores are rough.
- There is no human-labelled "correct answer" set, so the evaluation checks rules and sensible
  product types, not real user satisfaction.
- Product pictures are placeholders (the dataset has none).

## 7. Run it
```powershell
.\scripts\setup_db.ps1 -Dump <path to ingredientiq_full.dump>   # database (once)
python -m venv .venv; .venv\Scripts\activate; pip install -r requirements.txt
python -m uvicorn src.api.main:app --port 8000                  # backend
cd client; npm install; npm run dev                             # website
```
Add `OPENROUTER_API_KEY=...` to `.env` (copy from `.env.example`) to switch on the LLM.
