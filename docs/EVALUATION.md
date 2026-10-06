# Evaluating the IngredientIQ recommender

Question we ask: **do the recommendations make sense?**

We have no human ratings and no click data, so we cannot measure "user satisfaction".
What we can do is check, with numbers, that the engine (1) never breaks its own rules,
(2) recommends products of a sensible type that contain ingredients that fit the goal, and
(3) does this clearly better than simple rankings. We also looked for things that look wrong.

Everything is produced by one script (read-only, no network, no LLM):

```text
python -m scripts.evaluate_recommender            # full report, 5-7 minutes
python -m scripts.evaluate_recommender --quick    # small grid, 1-2 minutes
python -m pytest tests/test_recommender_quality.py   # fast subset, about 15 seconds
```

The numbers below are pasted from one full run (deterministic: two runs gave identical numbers).

---

## 1. What is measured

| Part | Question | How |
|---|---|---|
| Hard checks | Does the engine always obey its rules? | 279 different requests. Every answer is re-checked against the database tables with our own SQL, not with the engine's filter code. |
| Plausibility | Is the top-10 sensible? | Per goal, top-10, with and without a category filter: **type precision**, **ingredient evidence**, **key ingredient** (see below). |
| Baselines | Is the hybrid better than something trivial? | Same filters, same metrics: random, popularity only, rating only, ingredient match only. |
| Spot checks | Does it find the obvious answers? | Top 5 printed with names for 5 known cases. |
| Problems | What looks wrong? | Counts and examples (section 5). |

The three plausibility metrics, each = share of the top-10 that is a "hit":

* **Type precision**: the product's subcategory is in a hand-written list of "normal" product types for the goal
  (e.g. hydration: Moisturizers, Treatments, Masks, Eye Care, Body Moisturizers, Lip Balms).
  The list is common sense, written before we looked at results, and deliberately *not* copied from the
  scorer's own `GOAL_SUBCATEGORY_AFFINITY`. Gift sets and minis are not "normal" types.
* **Ingredient evidence**: the product contains at least one ingredient that the knowledge table
  (`ingredient_knowledge.user_goals`) tags with the goal.
* **Key ingredient**: the raw ingredient text contains one of a few textbook ingredients for the goal
  (hydration: hyaluron, glycerin ...; exfoliation: glycolic, lactic acid, salicylic ...; UV: zinc oxide,
  titanium dioxide, avobenzone ...). This is plain text search, so it does not depend on our parser or on
  the knowledge table.

Hard checks (all on every returned product, 279 requests, each run twice):
category, subcategory and price bounds respected; excluded ingredients (including the fragrance/parfum rule)
absent; required ingredients present; no duplicate products; at most `top_k` and exactly
`min(top_k, products that qualify)` returned (nothing eligible is lost); every score and component between 0 and 1;
sorted by score (ties by product id); same request twice gives identical output; the score equals the documented
formula (0.30 goal + 0.20 similarity + 0.15 intent + 0.15 review + 0.12 rating + 0.08 popularity, missing parts
dropped and renormalised) to 1e-9; the review score exists exactly for the products that have a row in
`product_review_signals`; matched ingredients really belong to the product.

Grid: 11 goals x 4 categories (none, Skincare, Hair, Makeup) x 3 price caps (none, 25, 60) x fragrance-free (no / yes) = 264,
plus 15 extra cases (required ingredients, subcategory, price range, two goals, no goals, upper/lower case,
price cap 0, impossible price range, `top_k` 3 and 25, unknown goal).

---

## 2. Results

### 2.1 Hard checks

| | |
|---|---|
| Requests checked | 279 |
| Products checked (all rules above) | 2,778 |
| Requests with 0 results | 2 (price cap 0, and min 50 / max 20: correct, nothing qualifies) |
| **Violations** | **0** |

Price edge: 294 products cost exactly 25 and 69 exactly 60; the engine includes them for `max_price` and `min_price`
exactly as the database says (set of products identical, 2,314 / 6,516 / 2,047).

### 2.2 Hybrid top-10 per goal, no category filter (8,494 candidates)

| goal | type precision | ingredient evidence | key ingredient |
|---|---|---|---|
| hydration | 100% | 100% | 100% |
| moisturization | 100% | 100% | 100% |
| brightening | 100% | 100% | 100% |
| exfoliation | 100% | 100% | 100% |
| antioxidant | 100% | 100% | 100% |
| soothing | 100% | 100% | 80% |
| **oil_control** | **30%** | 100% | 80% |
| uv_protection | 100% | 100% | 100% |
| cleansing | 100% | 100% | 100% |
| barrier_support | 100% | 100% | 100% |
| hair_conditioning | 100% | 100% | 100% |

Inside Skincare (Hair for `hair_conditioning`) every goal has 100% type precision and 100% ingredient evidence;
key ingredient is 100% except soothing (80%).

### 2.3 Hybrid versus simple baselines (average over the 11 goals)

Baselines use exactly the same filters and candidates. Random = average of 200 draws (fixed seed 42).
Rating-only ties are broken by review count.

| Scope | Metric | Hybrid | Random | Popularity | Rating | Ingredient-only |
|---|---|---|---|---|---|---|
| No category | type precision | **94%** | 15% | 12% | 11% | 42% |
| No category | ingredient evidence | 100% | 29% | 31% | 17% | 100% |
| No category | key ingredient | 96% | 28% | 26% | 24% | 96% |
| Skincare | type precision | **100%** | 52% | 63% | 50% | 50% |
| Skincare | ingredient evidence | 100% | 45% | 42% | 47% | 100% |
| Skincare | key ingredient | 98% | 49% | 44% | 55% | 99% |

Type precision per goal, no category filter:

| goal | Hybrid | Random | Popularity | Rating | Ingredient-only |
|---|---|---|---|---|---|
| hydration | 100% | 19% | 20% | 10% | 20% |
| moisturization | 100% | 18% | 20% | 10% | 0% |
| brightening | 100% | 15% | 10% | 10% | 40% |
| exfoliation | 100% | 13% | 10% | 10% | 70% |
| antioxidant | 100% | 16% | 10% | 10% | 20% |
| soothing | 100% | 19% | 20% | 10% | 30% |
| oil_control | 30% | 17% | 10% | 10% | 0% |
| uv_protection | 100% | 11% | 10% | 0% | 90% |
| cleansing | 100% | 8% | 0% | 20% | 90% |
| barrier_support | 100% | 16% | 20% | 10% | 50% |
| hair_conditioning | 100% | 12% | 0% | 20% | 50% |

### 2.4 Do the extra signals change the ranking?

Jaccard = overlap of two top-10 lists (1.0 identical, 0 nothing in common).

| Comparison | No category (range / mean) | Skincare (range / mean) |
|---|---|---|
| Hybrid vs ingredient-only | 0.00 - 0.25 / 0.15 | 0.00 - 0.33 / 0.17 |
| Hybrid vs hybrid without the review part | 0.67 - 1.00 / 0.77 | 0.67 - 1.00 / 0.81 |

The hybrid is a very different list from "most matching ingredients". Look at why: the ingredient-only
top-10 for *moisturization* is nine gift sets / kits (e.g. "The Youth Vault: 13-Piece ..." with 249 listed
ingredients, 41 of them matching) and a lip mask. Counting matches rewards long ingredient lists; the type
(intent) and similarity parts are what fix this. The review part changes 0 to 2 of the 10 products.

### 2.5 Known-answer spot checks (soft, printed with names by the script)

| Case | Result |
|---|---|
| hydration shows hyaluronic acid / glycerin products | 100% of top-10 (needed 80%): OK. #1 innisfree Green Tea Hyaluronic Acid Hydrating Serum |
| exfoliation shows AHA / BHA acid products | 100% (needed 80%): OK. #1 Paula's Choice 25% AHA + 2% BHA Exfoliant Peel |
| uv_protection mostly sunscreens | 100% Sunscreen (needed 60%): OK. #1 Dr. Jart+ Every Sun Day Sun Fluid SPF 50+ |
| hair_conditioning only hair products | 100% category Hair (needed 100%): OK |
| hydration, Skincare, fragrance-free | 100% have no "fragrance"/"parfum" anywhere in the raw ingredient text: OK |

---

## 3. What the numbers mean

* The engine obeys all its rules on everything we threw at it (0 violations in 2,778 checked products).
  The filters, the score formula, the ordering and determinism are trustworthy.
* For 10 of 11 goals the top-10 are products of the right type that contain goal ingredients, and the hybrid
  is far above random, popularity-only and rating-only (94% vs 11-15% type precision without a category filter).
  Popularity and rating alone are not recommendations for a goal: they pick well-known products of any type.
* "Ingredient-only" reaches 100% ingredient evidence **by construction** (it *is* the evidence). The honest comparison
  for it is type precision: 42% / 50% against 94% / 100% for the hybrid.
* The hybrid is not a copy of the ingredient match (overlap 0.15 on average), and the review part
  moves only a small part of the list (section 5, problem 1 shows it is not neutral though).
* The best-looking numbers (100% almost everywhere) are partly expected: the "type" list and the scorer's
  intent part are both common sense about product types, and the evidence metric uses the same knowledge table the
  goal score uses. That is why we added the *key ingredient* check (plain text, our own list): hybrid 96% / 98%
  against about 25-50% for the simple baselines.

---

## 4. Limitations (please read)

* **No human relevance labels and no real user clicks.** We measure plausibility, not satisfaction.
* **The ground truth is partly circular.** Ingredient evidence uses the same curated knowledge table that produces the goal score.
  The type list and the scorer's intent part are written by the same people with the same common sense.
  The key-ingredient lists are our own judgement (short substring lists, e.g. "sulfate" is crude).
* Only top-10 of 11 goals and 2 scopes (22 lists, 220 slots); one request per cell. Single-goal requests dominate;
  multi-goal quality is only covered by the hard checks, not by plausibility metrics.
* Type lists were fixed before looking at results, but they are still opinions (e.g. makeup powder foundations
  for oil control are arguable; we counted them as not expected).
* Explanations, LLM text and the API are not evaluated here.
* The counterfactual "ranking without the review part" is recomputed from the documented formula.

---

## 5. Problems found (most important first)

Counts use the 22 hybrid top-10 lists (220 slots) unless stated.

1. **Review signal works as a "has reviews" bonus, and only Skincare has reviews.**
   Review rows exist for 2,351 of 8,494 products: 2,351 of 2,420 Skincare products and **0** products of every
   other category (Makeup 2,369, Hair 1,464, Fragrance 1,432, Bath & Body 405 ...). Dropping the review weight and
   renormalising is not neutral because review scores are all high (min 0.61, median 0.84, max 0.95): a reviewed product gains on
   average **+0.071** (range +0.041 to +0.086 per goal) compared with scoring it without reviews, which is as big as the whole
   gap between rank 1 and rank 10 (0.02 - 0.10). The *value* of the review score moves the final score by only
   about 0.007 (weight 0.15 x std 0.048).
   Effect: good un-reviewed products (body creams, body scrubs, hair) are pushed down. Examples without a category filter:
   best good un-reviewed hydration product (Watermelon Glow AHA Pink Dream Body Cream) rank 46 -> 88; exfoliation (The Body Exfoliator)
   49 -> 96; uv_protection (Clean Conscious Body Sunscreen Mist) 12 -> 23. Un-reviewed share of the top-10 drops
   from 90% to 70% (oil_control), 80% to 60% (cleansing), 40% to 30% (moisturization) compared with the no-review ranking.
   Inside Skincare (97% reviewed) the effect is small, but the 69 un-reviewed Skincare products rank far lower (e.g. brightening 460 -> 1191).
2. **oil_control without a category returns eyeshadow, blush and brow powder.** Type precision 30%, 7 of 10 are Makeup:
   Anastasia Beverly Hills Soft Glam Eyeshadow Palette, tarte Tartelette Toasted Eyeshadow Palette, Laura Mercier RoseGlow Blush,
   Brow Powder Duo, ... They contain silica / kaolin / boron nitride (tagged oil_control) and all got the neutral intent score 0.50 because
   Makeup subcategories are not listed in `GOAL_SUBCATEGORY_AFFINITY` (7 of 7 odd slots). A listed but weak type such as
   Eye Care (0.20) therefore scores *below* an unlisted eyeshadow palette (0.50). Reproduce:
   `RecommendationEngine().recommend(RecommendationRequest(goals=["oil_control"]))`.
   Inside Skincare the same goal is fine (100%).
3. **"Fragrance-free" cannot check products without an ingredient list.** 950 products (11%) have no parsed
   ingredients (raw text "NaN"). They pass every exclusion and required-free filter as "unknown = fine":
   22 of 1,350 products returned in fragrance-free requests (2%) have no ingredient list at all
   (e.g. goal uv_protection, category Hair: "The Leave-In Conditioner Cream for Hydrated Hair"). 164 (12%) still list a
   fragrance allergen (limonene, linalool ...; documented), and excluding `alcohol` leaves 159 of 2,190 Skincare products that list
   "alcohol denat." / "SD alcohol" (exclusion matches the exact ingredient name only). The fragrance rule itself is sound: no result
   mentions fragrance/parfum in its raw text.
4. **Required ingredients match the exact name, and "may contain" counts as present.** `required=['hyaluronic acid']` finds 176 products but
   281 labels mention it (63%; the others say "sodium hyaluronate" etc.); glycerin 87%, salicylic acid 92%, niacinamide 98%.
   For zinc oxide 9 of 113 matches are only "may contain" entries.
5. **Same product in two sizes in one top-10, and minis.** The Moroccanoil All in One Leave-In Conditioner (full size, $30) and its Mini ($14)
   are ranks 2 and 3 for hair_conditioning (2 of 22 lists). 5 of 220 slots (2%) are mini/set/duo by name; none are tagged
   Value & Gift Sets / Mini Size, and 20 of 1,100 slots (2%) in the top-50 are. The catalogue has 636 extra rows that repeat a brand + name
   (mostly sizes and minis), so this will appear more often for other goals.
6. **The similarity part is weak for narrow goals.** Median similarity over all candidates is 0.00 for 7 of 11 goals
   (exfoliation, soothing, oil_control, uv_protection, cleansing, barrier_support, hair_conditioning), while the top-10 mean is 0.23 - 0.75.
   Influence on the ranking (weight x standard deviation across candidates): goal 0.052, intent 0.024, rating 0.022, similarity 0.019,
   popularity 0.011, review 0.007.
7. **Goals with no matching products in the chosen category return zero-evidence products.** With category Hair, 49 of 660 slots (7%) have
   no ingredient matching the goal (e.g. hair tools such as a scalp massager, detangling brushes and hair clips come back for brightening, oil_control or uv_protection); Makeup 12 of 660 (2%); Skincare 1 of 670.
   The answer does not say "nothing really fits".
8. **Small input handling gaps.** Category " Skincare " (with spaces) returns 0 results, but "SKINCARE" works. An unknown goal
   (`not_a_goal`) is silently ignored and gives the same list as no goals.
9. **Products with very short ingredient lists.** Only one product with 1-3 ingredients reaches a top-10 ("100% L-Ascorbic Acid Powder", in 2 lists, a
   legitimate single-ingredient product). No product without an ingredient list reaches a top-10 (the best rank of such a product is 544 or worse for every goal).
   For requests without goals, 1 of the top-10 (no category) lacks an ingredient list.

### What we recommend fixing

1. Make the missing-review case neutral: use the typical review score (for example the median of the reviewed candidates) instead of dropping
   the weight, or scale the review part around 0.84, so review presence does not add about +0.07.
2. Give unlisted subcategories a low intent score (for example 0.2) when the goal has a type map (this removes eyeshadow for oil control),
   or list the Makeup / Fragrance subcategories as unrelated.
3. Treat "no ingredient list" as unknown in fragrance-free / required filters (exclude those products, or flag them), and consider matching
   a few synonyms (hyaluronic acid / sodium hyaluronate, alcohol / alcohol denat.).
4. Collapse a mini and its full-size product (same brand + base name) into one result.
5. Strip spaces from `category` / `subcategory` before the SQL filter; tell the user when a goal is unknown.

---

## Changes made after this evaluation

| Problem found | Change |
|---|---|
| Reviewed products got a built-in bonus (only Skincare has reviews) | A product with no reviews is now scored with a neutral review score (`NEUTRAL_REVIEW_SCORE = 0.84`, the average of reviewed products). The result still shows `review_score = None` ("no review data"). The hard-check formula in `scripts/evaluate_recommender.py` was updated to match. |
| Product types missing from a goal's list scored a neutral 0.5 (beat listed bad types) | Unlisted types now score `UNLISTED_SUBCATEGORY_INTENT = 0.25`. |
| `category = " Skincare "` returned 0 results | Category and subcategory are stripped before the SQL lookup. |
| "Irritation" review aspect shown as a weakness | Excluded from explanations (`UNRELIABLE_ASPECTS`): the keyword sits in negative-sounding sentences even in happy reviews. |

Still open (known limitations): `oil_control` with **no category** still returns some
makeup powders (they contain oil-absorbing ingredients; pick a category to avoid this),
"fragrance-free" cannot check the ~950 products with no ingredient list, required
ingredients match the exact name only, and mini + full-size versions of one product can
both appear.
