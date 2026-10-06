# IngredientIQ API

Base URL (local): `http://localhost:8000`. Interactive docs: `http://localhost:8000/docs`.

```
.venv\Scripts\python.exe -m uvicorn src.api.main:app --port 8000
```

- All responses are JSON. CORS allows any `http://localhost:*` / `http://127.0.0.1:*` origin.
- Needs the Postgres container (`ingredientiq-db`). If the database is down every DB endpoint returns
  **503** `{"detail": "Database unreachable. Is the ingredientiq-db container running?"}`.
- Validation errors are **422** `{"detail": [...]}`; unknown product is **404** `{"detail": "Product X not found"}`.
- Prices are USD numbers; `rating` is 0..5; every score is 0..1 (higher is better).
- Fields that can be `null`: price, rating, brand, `review_score` (product has no reviews), `explanation.summary` (when `explain` is false).

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | API / DB / LLM status |
| GET | `/goals` | Goals the user can pick |
| GET | `/categories` | Categories + subcategories with counts |
| POST | `/recommend` | The main call: ranked products |
| GET | `/products?q=&category=&limit=` | Text search |
| GET | `/products/{product_id}` | Full product detail |
| GET | `/products/{product_id}/similar?k=` | Similar products |
| GET | `/ingredients?q=&limit=` | Ingredient search / most common ingredients |
| GET | `/ingredients/{ingredient_id}` | One ingredient: stats, related ingredients, products |

## GET /health

```json
{"status": "ok", "db": true, "llm_enabled": false, "products": 8494,
 "reviewed_products": 2351, "reviews": 1093895}
```
`status` is `"degraded"` (and `db` false, counts 0) when the database is unreachable. `llm_enabled` is true when an OpenRouter key is configured.
`reviewed_products` / `reviews`: only those products have review signals.

## GET /goals

```json
[
  {"id": "hydration", "label": "Hydration", "supported_by_vectors": true},
  {"id": "antioxidant", "label": "Antioxidant protection", "supported_by_vectors": true}
]
```
Use `id` in `/recommend`. `supported_by_vectors` says whether the vector-similarity signal knows the goal.

## GET /categories

```json
[
  {"category": "Skincare", "product_count": 2420,
   "subcategories": [{"name": "Cleansers", "product_count": 361},
                     {"name": "Moisturizers", "product_count": 551}]}
]
```
Sorted by `product_count`, biggest first. Use the exact `category` / `name` strings as filters.

## POST /recommend

Request body (everything optional):

| Field | Type | Default | Notes |
|---|---|---|---|
| `goals` | string[] | `[]` | ids from `/goals`. Unknown id -> 422 listing the valid ones |
| `category` | string | null | e.g. `"Skincare"` (case-insensitive) |
| `subcategory` | string | null | e.g. `"Moisturizers"` |
| `min_price`, `max_price` | number | null | USD, >= 0 |
| `required_ingredients` | string[] | `[]` | product must contain all of them |
| `excluded_ingredients` | string[] | `[]` | product must contain none (`"fragrance"` works) |
| `top_k` | int | 10 | 1..20, else 422 |
| `explain` | bool | true | add a plain-English `explanation.summary` to every result |

```json
{"goals": ["hydration"], "category": "Skincare", "max_price": 50,
 "excluded_ingredients": ["fragrance"], "top_k": 3, "explain": true}
```

Response (one result shown, others trimmed; numbers rounded). `results` is sorted by `score`, best first.

```json
{
  "count": 3,
  "llm_used": false,
  "weights": {"goal": 0.3, "similarity": 0.2, "intent": 0.15, "review": 0.15, "rating": 0.12, "popularity": 0.08},
  "request": {"goals": ["hydration"], "category": "Skincare", "subcategory": null,
              "min_price": null, "max_price": 50.0, "required_ingredients": [],
              "excluded_ingredients": ["fragrance"], "top_k": 3, "explain": true},
  "results": [
    {
      "product_id": "P458209",
      "product_name": "Daily Greens Oil-Free Gel Moisturizer with Moringa and Papaya",
      "brand": "Farmacy",
      "category": "Skincare",
      "subcategory": "Moisturizers",
      "price": 42.0,
      "rating": 4.06,
      "review_count": 1356,
      "loves_count": 72156,
      "score": 0.798,
      "goal_match_score": 0.8,
      "similarity_score": 0.574,
      "intent_score": 1.0,
      "review_score": null,
      "rating_score": 0.81,
      "popularity_score": 0.9,
      "matched_goals": ["hydration"],
      "matched_ingredients": ["betaine", "gluconolactone", "glucose"],
      "aspects": {},
      "explanation": {
        "strengths": ["Strong match for the requested goal (goal score: 0.80)."],
        "weaknesses": [],
        "summary": "Daily Greens Oil-Free Gel Moisturizer ... by Farmacy is a recommended option for hydration, with ingredients such as betaine, gluconolactone, glucose. It has ..."
      }
    }
  ]
}
```

Field guide:

- `score`: final hybrid score. Built from `goal_match_score` (share of the goal's ingredients present),
  `similarity_score` (cosine of goal vector vs product vector), `intent_score` (does the product type fit the goal),
  `review_score` (review sentiment, `null` if no reviews), `rating_score`, `popularity_score`.
- `weights`: how much each score part counts (sums to 1). A part with no data (`review_score` null, or no goals
  selected for goal/similarity/intent) is dropped and the others are rescaled, so missing data is never a zero.
- `aspects`: per-aspect review sentiment, e.g. `{"scent": {"mentions": 120, "positive_share": 0.91}}`. `{}` if none.
- `llm_used`: true only when an LLM key is set **and** `explain` is true. With no key (or if the LLM call fails)
  `summary` is a fixed template sentence, never empty when `explain` is true.
- With `explain: false`, `explanation.summary` is `null` (strengths/weaknesses are still filled).
- Unknown extra fields the engine adds in future are passed through unchanged.

422 example (unknown goal):
```json
{"detail": [{"loc": ["body", "goals"], "msg": "Value error, Unknown goals ['glow']. Valid goals: ['antioxidant', ..., 'uv_protection']", "type": "value_error"}]}
```

## GET /products?q=&category=&limit=20

`q` is matched (case-insensitive substring) against product name and brand. `category` is optional. `limit` 1..50.
Most-loved products first. Returns a light list:

```json
[{"product_id": "P420652", "product_name": "Lip Sleeping Mask Intense Hydration with Vitamin C",
  "brand": "LANEIGE", "category": "Skincare", "subcategory": "Lip Balms & Treatments",
  "price": 24.0, "rating": 4.35, "review_count": 16118}]
```

## GET /products/{product_id}

404 if unknown.

```json
{
  "product_id": "P458209", "product_name": "Daily Greens Oil-Free Gel Moisturizer ...", "brand": "Farmacy",
  "category": "Skincare", "subcategory": "Moisturizers",
  "price": 42.0, "sale_price_usd": null, "rating": 4.06, "review_count": 1356, "loves_count": 72156,
  "highlights": ["Good for: Pores", "Niacinamide", "Cruelty-Free"],
  "variation_type": "Size", "variation_value": "1.7 oz/ 50 mL",
  "limited_edition": false, "is_new": false, "online_only": false,
  "out_of_stock": false, "sephora_exclusive": false,
  "ingredients": [
    {"ingredient_id": 12001, "position": 1, "name": "water/aqua/eau", "presence_type": "PRIMARY", "section": "main",
     "concentration": null, "functional_groups": ["solvent"], "user_goals": ["formulation_base"]}
  ],
  "functional_profile": {"fg_humectant": 4, "fg_emollient": 3, "goal_hydration": 5, "...": 0},
  "review_signals": {"review_count": 1356, "analyzed_count": 1300, "avg_sentiment": 0.41,
                     "positive_share": 0.78, "negative_share": 0.09, "review_score": 0.72,
                     "aspects": {"scent": {"mentions": 120, "positive_share": 0.91}}, "method": "vader_v1"},
  "review_summary": {"review_count": 1356, "average_review_rating": 4.061, "recommendation_count": 1000,
                     "recommendation_rate": 0.8, "average_helpfulness": 0.5, "review_text_count": 1300,
                     "earliest_review_date": "2019-01-02", "latest_review_date": "2023-03-01"}
}
```

- `ingredients` are in label order; `ingredient_id` is the id for `GET /ingredients/{ingredient_id}`. `section` is `"main"` for the normal list; products with shade/variant-specific
  lists have extra sections (listed after `main`). `presence_type` is `PRIMARY` or `MAY_CONTAIN`.
  `functional_groups` / `user_goals` are `[]` for ingredients we have no knowledge about.
- `functional_profile`, `review_signals`, `review_summary` are `null` when not available for the product
  (review values above are illustrative; `review_signals` is `null` until the review NLP has been run).

## GET /products/{product_id}/similar?k=5

`k` 1..20. Products with the most similar mix of ingredient functions (cosine similarity), best first.
Returns `[]` for a product that has no ingredient vector. 404 if the product does not exist.

```json
[{"product_id": "P479985", "product_name": "Photo Finish Primerizer+ Hydrating Face Primer with Hyaluronic Acid",
  "brand": "Smashbox", "category": "Makeup", "subcategory": "Face", "price": 42.0, "rating": 4.54,
  "review_count": 521, "similarity": 0.9585}]
```

## GET /ingredients?q=&limit=50

`q` is matched (case-insensitive substring) against the ingredient name; `limit` 1..200. Ingredients in the most
products first (each product counted once). Takes about 0.3 s. `functional_groups` is `[]` when we have no knowledge about it.

```json
[{"ingredient_id": 5159, "name": "glycerin", "product_count": 3750, "functional_groups": ["humectant"]}]
```

## GET /ingredients/{ingredient_id}

404 if unknown.

```json
{
  "ingredient_id": 5159, "name": "glycerin", "product_count": 3750, "functional_groups": ["humectant"],
  "user_goals": ["hydration", "moisturization"],
  "catalog_share": 0.4415, "avg_rating": 4.2, "median_price": 36.0,
  "related": [{"ingredient_id": 8835, "name": "phenoxyethanol", "product_count": 2414}],
  "products": [{"product_id": "P420652", "product_name": "Lip Sleeping Mask Intense Hydration with Vitamin C",
                "brand": "LANEIGE", "category": "Skincare", "subcategory": "Lip Balms & Treatments",
                "price": 24.0, "rating": 4.35, "review_count": 16118}]
}
```

- `catalog_share`: share of all products that contain it (0..1). `avg_rating` / `median_price`: over those products.
- `related`: the 6 ingredients found together with it in the most products (`product_count` = products with both).
- `products`: the most-loved products containing it (up to 12).
