"""
Evaluation of the hybrid recommender (needs the database, read-only, no network).

Run from the project root:
    python -m scripts.evaluate_recommender            # full report (a few minutes)
    python -m scripts.evaluate_recommender --quick    # small grid (about a minute)

What it does, in plain words:
  1. HARD CHECKS   - many different requests; for every answer we re-check the
                     rules with our OWN SQL (not the engine's filter code).
  2. PLAUSIBILITY  - for each goal: do the top-10 products have a sensible type,
                     and do they contain ingredients that fit the goal?
  3. BASELINES     - same numbers for simple rankings (random, popularity,
                     rating, ingredient-match only) under the SAME filters.
  4. SPOT CHECKS   - top 5 for a few known answers, printed with names.
  5. PROBLEMS      - things that look wrong, with counts.

There are no human labels and no click data. The only "truth" we have is
common sense (lists written by hand below) and the curated ingredient table.
"""
import argparse
import json
import os
import random
import re
import statistics
import sys
import time
from pathlib import Path

import psycopg

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.recommender import RecommendationEngine, RecommendationRequest  # noqa: E402
from src.recommender.config import GOAL_LABELS, NEUTRAL_REVIEW_SCORE  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")  # product names contain symbols

GOALS = list(GOAL_LABELS)
TOP_K = 10
BIG = 10**6  # "give me every candidate"

# The documented formula (README). We re-compute every score with these numbers.
WEIGHTS = {"goal": 0.30, "similarity": 0.20, "intent": 0.15,
           "review": 0.15, "rating": 0.12, "popularity": 0.08}

# ---------------------------------------------------------------------------
# Hand-written "truth" (decided before looking at results)
# ---------------------------------------------------------------------------

# Product types (subcategory) where a product for this goal looks normal.
# This is NOT copied from config.GOAL_SUBCATEGORY_AFFINITY (that is the scorer's
# own opinion; copying it would make the test circular).
# "Treatments" is a broad skincare bucket (serums, spot care ...), so it is allowed.
# Gift sets and minis are deliberately NOT allowed: a set is not a clear answer.
_CARE = {"Moisturizers", "Treatments", "Masks", "Eye Care", "Body Moisturizers",
         "Lip Balms & Treatments"}
EXPECTED_TYPES = {
    "hydration": _CARE,
    "moisturization": _CARE,
    "soothing": _CARE,
    "brightening": {"Treatments", "Moisturizers", "Masks", "Eye Care"},
    "exfoliation": {"Treatments", "Cleansers", "Masks", "Bath & Shower", "Body Care"},
    "antioxidant": {"Treatments", "Moisturizers", "Eye Care", "Masks", "Sunscreen"},
    "oil_control": {"Treatments", "Cleansers", "Masks", "Moisturizers"},
    "uv_protection": {"Sunscreen", "Moisturizers", "Body Moisturizers",
                      "Lip Balms & Treatments"},
    "cleansing": {"Cleansers", "Bath & Shower", "Shampoo & Conditioner"},
    "barrier_support": {"Treatments", "Moisturizers", "Body Moisturizers", "Eye Care",
                        "Lip Balms & Treatments"},
    # In this dataset hair masks sit in "Hair Styling & Treatments"; "Masks" is face masks.
    "hair_conditioning": {"Shampoo & Conditioner", "Hair Styling & Treatments"},
}

# A few textbook ingredients per goal. They are searched as text inside the raw
# ingredient list, so this check does not use the parser or the knowledge table.
KEY_INGREDIENTS = {
    "hydration": ("hyaluron", "glycerin", "sodium pca", "polyglutamic"),
    "moisturization": ("shea", "butyrospermum", "ceramide", "squalane", "glycerin",
                       "petrolatum", "simmondsia"),
    "brightening": ("niacinamide", "ascorb", "arbutin", "kojic", "tranexamic",
                    "glycyrrhiza", "licorice", "azelaic"),
    "exfoliation": ("glycolic", "lactic acid", "salicylic", "mandelic",
                    "gluconolactone", "lactobionic", "papain", "bromelain"),
    "antioxidant": ("tocopher", "ascorb", "resveratrol", "ferulic", "camellia sinensis",
                    "green tea", "ubiquinone", "astaxanthin"),
    "soothing": ("allantoin", "panthenol", "centella", "madecassoside", "bisabolol",
                 "aloe", "chamomilla", "avena sativa", "glycyrrhiz"),
    "oil_control": ("salicylic", "niacinamide", "zinc pca", "kaolin", "charcoal",
                    "hamamelis"),
    "uv_protection": ("zinc oxide", "titanium dioxide", "avobenzone", "octocrylene",
                      "homosalate", "octisalate", "octinoxate", "oxybenzone",
                      "tinosorb", "uvinul"),
    "cleansing": ("sulfate", "sulfonate", "cocoyl", "glucoside", "sarcosinate",
                  "cocamidopropyl", "taurate"),
    "barrier_support": ("ceramide", "cholesterol", "linoleic", "niacinamide",
                        "sphingo", "squalane"),
    "hair_conditioning": ("behentrimonium", "cetrimonium", "stearamidopropyl",
                          "amodimethicone", "quaternium", "keratin"),
}

# Common fragrance allergens, to see what a "fragrance-free" answer still contains.
ALLERGENS = ("limonene", "linalool", "citronellol", "geraniol", "citral", "eugenol",
             "coumarin", "benzyl salicylate", "hexyl cinnamal", "amyl cinnamal")

GIFT_OR_MINI = {"Value & Gift Sets", "Mini Size"}
GIFT_WORDS = re.compile(r"\b(mini|set|kit|duo|trio|travel|discovery|sampler)\b", re.I)


# ---------------------------------------------------------------------------
# Our own view of the database (own SQL, not the engine's repository)
# ---------------------------------------------------------------------------

def connect():
    conn = psycopg.connect(
        host=os.getenv("PGHOST", "localhost"),
        port=os.getenv("PGPORT", "5432"),
        dbname=os.getenv("PGDATABASE", "ingredientiq"),
        user=os.getenv("PGUSER", "postgres"),
        password=os.getenv("PGPASSWORD"),
        connect_timeout=5,  # fail fast when the database is not running
    )
    conn.read_only = True  # this script never writes
    return conn


class Facts:
    """The truth about every product, read straight from the tables."""

    def __init__(self, conn):
        self.products = {}
        rows = conn.execute(
            "SELECT product_id, product_name, brand, category, subcategory, price, "
            "rating, review_count, loves_count, LOWER(COALESCE(raw_ingredients, '')) "
            "FROM products"
        ).fetchall()
        for pid, name, brand, cat, sub, price, rating, reviews, loves, raw in rows:
            self.products[pid] = {
                "name": name, "brand": brand, "category": cat or "",
                "subcategory": sub or "",
                "price": float(price) if price is not None else None,
                "rating": float(rating) if rating is not None else None,
                "reviews": reviews, "loves": loves, "raw": raw,
            }

        # Ingredient names per product. "primary" = real ingredients only,
        # "ingredients" = also the "may contain" ones.
        self.ingredients = {pid: set() for pid in self.products}
        self.primary = {pid: set() for pid in self.products}
        for pid, name, kind in conn.execute(
            "SELECT pi.product_id, LOWER(i.canonical_name), pi.presence_type "
            "FROM product_ingredients pi JOIN ingredients i ON i.ingredient_id = pi.ingredient_id"
        ):
            self.ingredients[pid].add(name)
            if kind == "PRIMARY":
                self.primary[pid].add(name)

        self.fragrance_ids = {
            pid for pid, names in self.ingredients.items()
            if any(word in name for name in names for word in ("fragrance", "parfum"))
        }
        self.reviewed = {
            row[0] for row in conn.execute(
                "SELECT product_id FROM product_review_signals WHERE review_score IS NOT NULL"
            )
        }
        # Products having at least one ingredient that the knowledge table tags with the goal.
        self.goal_products = {}
        for goal in GOALS:
            self.goal_products[goal] = {
                row[0] for row in conn.execute(
                    "SELECT DISTINCT pi.product_id FROM product_ingredients pi "
                    "JOIN ingredient_knowledge ik ON ik.ingredient_id = pi.ingredient_id "
                    "WHERE ik.user_goals @> %s::jsonb", (json.dumps([goal]),)
                )
            }


def _lower(text):
    return (text or "").strip().lower()


def rule_violations(facts, pid, req):
    """Reasons why this product must NOT be in the answer to this request ([] = fine)."""
    p = facts.products[pid]
    names = facts.ingredients[pid]
    bad = []
    if req.category and p["category"].strip().lower() != _lower(req.category):
        bad.append(f"category {p['category']!r} is not {req.category!r}")
    if req.subcategory and p["subcategory"].strip().lower() != _lower(req.subcategory):
        bad.append(f"subcategory {p['subcategory']!r} is not {req.subcategory!r}")
    if req.min_price is not None and (p["price"] is None or p["price"] < req.min_price):
        bad.append(f"price {p['price']} below min {req.min_price}")
    if req.max_price is not None and (p["price"] is None or p["price"] > req.max_price):
        bad.append(f"price {p['price']} above max {req.max_price}")
    for name in map(_lower, req.required_ingredients):
        if name not in names:
            bad.append(f"required ingredient {name!r} missing")
    excluded = set(map(_lower, req.excluded_ingredients))
    for name in sorted(excluded & names):
        bad.append(f"excluded ingredient {name!r} present")
    if excluded & {"fragrance", "parfum"} and pid in facts.fragrance_ids:
        bad.append("fragrance/parfum present although excluded")
    return bad


def eligible_ids(facts, req):
    """Every product that obeys all the request's rules (our own count)."""
    return [pid for pid in facts.products if not rule_violations(facts, pid, req)]


# ---------------------------------------------------------------------------
# 1. Hard checks
# ---------------------------------------------------------------------------

SCORE_FIELDS = ("score", "goal_match_score", "similarity_score", "intent_score",
                "review_score", "rating_score", "popularity_score")


def formula_score(r, has_goals, use_review=True):
    """Recompute the hybrid score from the components, as the README describes."""
    parts = {"rating": r.rating_score, "popularity": r.popularity_score}
    if has_goals:
        parts.update(goal=r.goal_match_score, similarity=r.similarity_score,
                     intent=r.intent_score)
    if use_review:  # no reviews -> the engine uses the neutral prior (see NEUTRAL_REVIEW_SCORE)
        parts["review"] = r.review_score if r.review_score is not None else NEUTRAL_REVIEW_SCORE
    return sum(WEIGHTS[k] * v for k, v in parts.items()) / sum(WEIGHTS[k] for k in parts)


def answer_problems(facts, results, req):
    """Checks on the answer itself: shape, ranges, order, formula, review link."""
    bad = []
    ids = [r.product_id for r in results]
    if len(set(ids)) != len(ids):
        bad.append("duplicate products in the answer")
    if len(results) > req.top_k:
        bad.append(f"{len(results)} results but top_k={req.top_k}")
    order = [(-r.score, r.product_id) for r in results]
    if order != sorted(order):
        bad.append("not sorted by score desc / product_id")

    goals = [_lower(g) for g in req.goals if _lower(g)]
    # Unknown goals make the engine drop 'similarity', so the formula check needs known goals.
    formula_applies = all(g in GOAL_LABELS for g in goals)

    for r in results:
        for field in SCORE_FIELDS:
            value = getattr(r, field)
            if value is not None and not 0.0 <= value <= 1.0:
                bad.append(f"{r.product_id}: {field}={value} outside 0..1")
        if formula_applies and abs(formula_score(r, bool(goals)) - r.score) > 1e-9:
            bad.append(f"{r.product_id}: score {r.score} differs from the formula")
        if (r.review_score is not None) != (r.product_id in facts.reviewed):
            bad.append(f"{r.product_id}: review score does not match product_review_signals")
        stray = set(r.matched_ingredients) - facts.ingredients[r.product_id]
        if stray:
            bad.append(f"{r.product_id}: matched ingredients not in the product: {sorted(stray)}")
    return bad


def check_request(engine, facts, req, twice=True):
    """Run one request and verify everything. Returns (results, list of problems)."""
    results = engine.recommend(req)
    bad = answer_problems(facts, results, req)
    for r in results:
        bad += [f"{r.product_id}: {why}" for why in rule_violations(facts, r.product_id, req)]
    expected = min(req.top_k, len(eligible_ids(facts, req)))
    if len(results) != expected:
        bad.append(f"returned {len(results)} products, expected {expected}")
    if twice and [r.to_dict() for r in engine.recommend(req)] != [r.to_dict() for r in results]:
        bad.append("two identical runs gave different output")
    return results, bad


def describe(req):
    parts = [f"goals={'+'.join(req.goals) or '-'}"]
    for name in ("category", "subcategory", "min_price", "max_price"):
        if getattr(req, name) is not None:
            parts.append(f"{name}={getattr(req, name)}")
    if req.required_ingredients:
        parts.append(f"require={req.required_ingredients}")
    if req.excluded_ingredients:
        parts.append(f"exclude={req.excluded_ingredients}")
    if req.top_k != TOP_K:
        parts.append(f"top_k={req.top_k}")
    return " ".join(parts)


def build_grid(quick):
    goals = ["hydration", "exfoliation", "hair_conditioning"] if quick else GOALS
    categories = [None, "Skincare"] if quick else [None, "Skincare", "Hair", "Makeup"]
    prices = [None, 25] if quick else [None, 25, 60]
    grid = [
        RecommendationRequest(
            goals=[goal], category=category, max_price=price, top_k=TOP_K,
            excluded_ingredients=["fragrance"] if fragrance_free else [],
        )
        for goal in goals for category in categories
        for price in prices for fragrance_free in (False, True)
    ]
    extras = [
        RecommendationRequest(goals=["hydration"], required_ingredients=["glycerin"]),
        RecommendationRequest(goals=["brightening"], required_ingredients=["niacinamide"]),
        RecommendationRequest(goals=["hydration"], category="Skincare", max_price=60,
                              required_ingredients=["glycerin", "niacinamide"]),
        RecommendationRequest(required_ingredients=["glycerin"],
                              excluded_ingredients=["fragrance"]),  # no goals
        RecommendationRequest(goals=["hydration", "brightening"], category="Skincare"),
        RecommendationRequest(goals=["uv_protection"], subcategory="Sunscreen"),
        RecommendationRequest(goals=["hair_conditioning"], subcategory="Shampoo & Conditioner",
                              min_price=20, max_price=40),
        RecommendationRequest(goals=["cleansing"], min_price=10, max_price=25,
                              excluded_ingredients=["parfum"]),
        RecommendationRequest(goals=["soothing"], category="Skincare",
                              excluded_ingredients=["alcohol", "fragrance"]),
        RecommendationRequest(goals=["Hydration"], category="skincare",
                              required_ingredients=["Glycerin"]),  # upper / lower case
        RecommendationRequest(goals=["hydration"], max_price=0),  # nothing is that cheap
        RecommendationRequest(goals=["hydration"], min_price=50, max_price=20),  # impossible
        RecommendationRequest(goals=["hydration"], top_k=3),
        RecommendationRequest(goals=["hydration"], top_k=25),
        RecommendationRequest(goals=["not_a_goal"], category="Skincare"),
    ]
    return grid + (extras[:5] if quick else extras)


def hard_checks(engine, facts, quick):
    grid = build_grid(quick)
    print(f"Checking {len(grid)} requests (each one is run twice to test determinism)...")
    all_results, violations = [], []
    for i, req in enumerate(grid, 1):
        results, bad = check_request(engine, facts, req)
        all_results.append((req, results))
        violations += [(describe(req), why) for why in bad]
        if i % 20 == 0:
            print(f"  ... {i}/{len(grid)}", flush=True)

    checked = sum(len(results) for _, results in all_results)
    empty = sum(1 for _, results in all_results if not results)
    print(f"\nRequests checked        : {len(grid)}")
    print(f"Products checked        : {checked} (each against category, subcategory, price, "
          "required, excluded, fragrance, ranges, formula, review link)")
    print(f"Requests with 0 results : {empty}")
    print(f"VIOLATIONS              : {len(violations)}")
    for label, why in violations[:25]:
        print(f"  [{label}] {why}")
    return all_results, violations


# ---------------------------------------------------------------------------
# 2 + 3. Plausibility metrics and baselines
# ---------------------------------------------------------------------------

def table(headers, rows):
    rows = [[str(x) for x in row] for row in rows]
    widths = [max(len(str(c)) for c in col) for col in zip(headers, *rows)]
    line = lambda row: "  ".join(
        cell.ljust(w) if i == 0 else cell.rjust(w)
        for i, (cell, w) in enumerate(zip(row, widths)))
    print(line(headers))
    print("  ".join("-" * w for w in widths))
    for row in rows:
        print(line(row))


def pct(x):
    return f"{100 * x:.0f}%"


def base_name(brand, name):
    """Brand + name without 'mini' / 'travel', so a mini matches its full-size product."""
    name = re.sub(r"\b(mini|travel size|travel)\b", " ", name.lower())
    return brand, " ".join(name.split())


def type_hit(facts, r, goal):
    return r.subcategory in EXPECTED_TYPES[goal]


def evidence_hit(facts, r, goal):
    return r.product_id in facts.goal_products[goal]


def key_hit(facts, r, goal):
    raw = facts.products[r.product_id]["raw"]
    return any(word in raw for word in KEY_INGREDIENTS[goal])


METRICS = {"type precision": type_hit, "ingredient evidence": evidence_hit,
           "key ingredient": key_hit}
METHODS = ["hybrid", "random", "popularity", "rating", "ingredient-only"]


def metric(facts, top_lists, goal, fn):
    """Average share of 'hits' in the top lists (random has many lists, others one)."""
    shares = [sum(fn(facts, r, goal) for r in top) / len(top) for top in top_lists]
    return sum(shares) / len(shares)


def jaccard(a, b):
    a, b = {r.product_id for r in a}, {r.product_id for r in b}
    return len(a & b) / len(a | b) if a | b else 0.0


def unreviewed_share(facts, top):
    return sum(r.product_id not in facts.reviewed for r in top) / len(top)


def evaluate_goal(engine, facts, goal, category):
    """Rank every candidate for this goal+category, then take the top 10 in 5 ways."""
    pool = engine.recommend(RecommendationRequest(goals=[goal], category=category, top_k=BIG))
    rng = random.Random(42)  # fixed seed
    by = lambda key: sorted(pool, key=key)[:TOP_K]
    tops = {
        "hybrid": [pool[:TOP_K]],
        "random": [rng.sample(pool, TOP_K) for _ in range(200)],  # average of 200 draws
        "popularity": [by(lambda r: (-(r.loves_count or 0), r.product_id))],
        "rating": [by(lambda r: (-(r.rating or 0), -(r.review_count or 0), r.product_id))],
        "ingredient-only": [by(lambda r: (-r.goal_match_score, r.product_id))],
    }
    # What would the ranking look like if review scores did not exist?
    without_review = sorted(pool, key=lambda r: (-formula_score(r, True, False), r.product_id))
    reviewed = [r for r in pool if r.review_score is not None]
    boosts = [r.score - formula_score(r, True, False) for r in reviewed]
    comps = {"goal": "goal_match_score", "similarity": "similarity_score",
             "intent": "intent_score", "rating": "rating_score",
             "popularity": "popularity_score"}
    influence = {name: WEIGHTS[name] * statistics.pstdev(getattr(r, attr) for r in pool)
                 for name, attr in comps.items()}
    if len(reviewed) > 1:
        influence["review"] = WEIGHTS["review"] * statistics.pstdev(r.review_score for r in reviewed)
    # Products that SHOULD be recommended: right type and ingredient evidence for the goal.
    good = [r for r in pool if type_hit(facts, r, goal) and evidence_hit(facts, r, goal)]
    rank_hybrid = {r.product_id: i for i, r in enumerate(pool, 1)}
    rank_plain = {r.product_id: i for i, r in enumerate(without_review, 1)}
    unreviewed = [r for r in good if r.product_id not in facts.reviewed]
    best = min(unreviewed, key=lambda r: rank_plain[r.product_id]) if unreviewed else None
    return {
        "goal": goal, "category": category, "pool_size": len(pool), "tops": tops,
        "no_review_top": without_review[:TOP_K],
        "top50": pool[:50],
        "best_empty_rank": next(
            (i for i, r in enumerate(pool, 1) if not facts.ingredients[r.product_id]), None),
        "good_size": len(good),
        "good_unreviewed": unreviewed_share(facts, good) if good else 0.0,
        "best_unreviewed": (
            (best.product_name, best.subcategory, rank_plain[best.product_id],
             rank_hybrid[best.product_id]) if best else None),
        "boost": statistics.mean(boosts) if boosts else 0.0,
        "boost_share": sum(b > 0 for b in boosts) / len(boosts) if boosts else 0.0,
        "spread": pool[0].score - pool[TOP_K - 1].score if len(pool) >= TOP_K else 0.0,
        "sim_pool_median": statistics.median(r.similarity_score for r in pool),
        "sim_top_mean": statistics.mean(r.similarity_score for r in pool[:TOP_K]),
        "influence": influence,
        "review_scores": [r.review_score for r in reviewed],
        "ratings": [r.rating for r in pool if r.rating is not None],
    }


def scope_for(goal, scope):
    """Second scope = Skincare (Hair for the hair goal, where Skincare makes no sense)."""
    if scope == "all":
        return None
    return "Hair" if goal == "hair_conditioning" else "Skincare"


def plausibility_and_baselines(engine, facts, quick):
    goals = (["hydration", "exfoliation", "uv_protection", "hair_conditioning"]
             if quick else GOALS)
    evals = {"all": [], "category": []}
    for goal in goals:
        for scope in evals:
            evals[scope].append(evaluate_goal(engine, facts, goal, scope_for(goal, scope)))

    names = {"all": "no category filter", "category": "inside Skincare (Hair for hair_conditioning)"}
    for scope, rows in evals.items():
        print(f"\n--- Scope: {names[scope]} ---")

        print("\nHybrid top-10 per goal:")
        table(["goal", "candidates", *METRICS],
              [[e["goal"], e["pool_size"]] + [
                  pct(metric(facts, e["tops"]["hybrid"], e["goal"], fn)) for fn in METRICS.values()]
               for e in rows])

        for metric_name, fn in METRICS.items():
            print(f"\n{metric_name} (share of the top-10), hybrid vs baselines:")
            table(["goal", *METHODS],
                  [[e["goal"]] + [pct(metric(facts, e["tops"][m], e["goal"], fn)) for m in METHODS]
                   for e in rows]
                  + [["AVERAGE"] + [
                      pct(statistics.mean(metric(facts, e["tops"][m], e["goal"], fn) for e in rows))
                      for m in METHODS]])

    print("\n--- Does the hybrid just repeat the ingredient match? ---")
    print("Jaccard = overlap of two top-10 lists (1.0 = same products, 0 = nothing in common).")
    print("'no-review ranking' = the hybrid with the review part removed (everyone is scored "
          "like an un-reviewed product).")
    for scope, rows in evals.items():
        print(f"\nScope: {names[scope]}")
        table(["goal", "Jaccard hybrid vs ingredient-only", "Jaccard hybrid vs no-review ranking"],
              [[e["goal"],
                f"{jaccard(e['tops']['hybrid'][0], e['tops']['ingredient-only'][0]):.2f}",
                f"{jaccard(e['tops']['hybrid'][0], e['no_review_top']):.2f}"] for e in rows])

    print("\n--- Review coverage effect (only 2,351 of 8,494 products have review signals) ---")
    print("'good' = products with an expected type AND ingredient evidence for the goal.")
    print("'unreviewed' = share WITHOUT review signals. 'best good unreviewed' = the rank of "
          "the best such product: without reviews -> in the hybrid.")
    for scope, rows in evals.items():
        print(f"\nScope: {names[scope]}")
        table(["goal", "good products", "good unreviewed", "hybrid top-10 unreviewed",
               "no-review top-10 unreviewed", "best good unreviewed (rank)",
               "avg review boost", "top1-top10 gap"],
              [[e["goal"], e["good_size"], pct(e["good_unreviewed"]),
                pct(unreviewed_share(facts, e["tops"]["hybrid"][0])),
                pct(unreviewed_share(facts, e["no_review_top"])),
                f"{e['best_unreviewed'][2]} -> {e['best_unreviewed'][3]}"
                if e["best_unreviewed"] else "-",
                f"{e['boost']:+.3f}", f"{e['spread']:.3f}"] for e in rows])
    print("\navg review boost = mean (score with reviews - score without the review part), over "
          "reviewed products. If it is as big as the top1-top10 gap, it can reorder a whole top-10.")
    return evals


# ---------------------------------------------------------------------------
# 4. Known-answer spot checks (soft: WARN, never a failure)
# ---------------------------------------------------------------------------

def spot_checks(engine, facts):
    contains = lambda words: lambda p: any(w in p["raw"] for w in words)
    cases = [
        ("hydration -> hyaluronic acid / glycerin products",
         RecommendationRequest(goals=["hydration"], top_k=TOP_K),
         contains(("hyaluron", "glycerin")), 0.8),
        ("exfoliation -> AHA / BHA acid products",
         RecommendationRequest(goals=["exfoliation"], top_k=TOP_K),
         contains(KEY_INGREDIENTS["exfoliation"]), 0.8),
        ("uv_protection -> mostly sunscreens",
         RecommendationRequest(goals=["uv_protection"], top_k=TOP_K),
         lambda p: p["subcategory"] == "Sunscreen", 0.6),
        ("hair_conditioning -> only hair products",
         RecommendationRequest(goals=["hair_conditioning"], top_k=TOP_K),
         lambda p: p["category"] == "Hair", 1.0),
        ("hydration, Skincare, fragrance-free -> no fragrance word in the raw ingredient text",
         RecommendationRequest(goals=["hydration"], category="Skincare",
                               excluded_ingredients=["fragrance"], top_k=TOP_K),
         lambda p: "fragrance" not in p["raw"] and "parfum" not in p["raw"], 1.0),
    ]
    for title, req, test, minimum in cases:
        results = engine.recommend(req)
        share = sum(test(facts.products[r.product_id]) for r in results) / max(len(results), 1)
        print(f"\n{title}\n  -> {pct(share)} of top-10 (needed {pct(minimum)}): "
              f"{'OK' if share >= minimum else 'WARN'}")
        for i, r in enumerate(results[:5], 1):
            print(f"  {i}. {r.brand} - {r.product_name[:52]} | {r.subcategory} | "
                  f"${r.price:.0f} | score {r.score:.3f}")


# ---------------------------------------------------------------------------
# 5. Problems
# ---------------------------------------------------------------------------

def all_hybrid_tops(evals):
    return [(e["goal"], e["category"], e["tops"]["hybrid"][0])
            for rows in evals.values() for e in rows]


def problems(engine, facts, evals, grid_results):
    tops = all_hybrid_tops(evals)
    slots = sum(len(top) for _, _, top in tops)
    lists = len(tops)
    products = facts.products

    print(f"\n(Counts below use the {lists} hybrid top-10 lists of section 2 = {slots} slots.)")

    print("\n[P1] Gift sets / minis / kits in the top-10")
    tagged = [r for _, _, top in tops for r in top
              if r.subcategory in GIFT_OR_MINI or r.category == "Mini Size"]
    named = [r for _, _, top in tops for r in top if GIFT_WORDS.search(r.product_name)]
    print(f"  tagged Value & Gift Sets / Mini Size: {len(tagged)}/{slots} slots ({pct(len(tagged)/slots)})")
    print(f"  name says mini/set/kit/duo/trio/travel: {len(named)}/{slots} slots ({pct(len(named)/slots)})")
    for r in named[:4]:
        print(f"    e.g. {r.product_name[:60]} ({r.subcategory}, ${r.price:.0f})")
    top50 = [r for rows in evals.values() for e in rows for r in e["top50"]]
    gifts50 = [r for r in top50 if r.subcategory in GIFT_OR_MINI or r.category == "Mini Size"]
    print(f"  deeper look, top-50 of every goal: {len(gifts50)}/{len(top50)} slots "
          f"({pct(len(gifts50)/len(top50))}) are tagged gift set / mini")

    print("\n[P2] Same product in several sizes (same brand + name, 'Mini' ignored) in one top-10")
    dup_lists, shown = 0, 0
    for goal, cat, top in tops:
        keys = [base_name(r.brand, r.product_name) for r in top]
        if len(set(keys)) < len(keys):
            dup_lists += 1
            if shown < 3:
                dup = next(k for k in keys if keys.count(k) > 1)
                sizes = [f"{r.product_id} ${r.price:.0f}" for r in top
                         if base_name(r.brand, r.product_name) == dup]
                print(f"    e.g. goal={goal} cat={cat}: {dup[0]} - {dup[1][:50]} -> {sizes}")
                shown += 1
    in_db = len({base_name(p["brand"], p["name"]) for p in products.values()})
    print(f"  top-10 lists with a repeated product: {dup_lists}/{lists}")
    print(f"  (the catalogue has {len(products) - in_db} extra rows that repeat a brand+name)")

    print("\n[P3] Odd product types in the top-10 (not in the hand-written expected list)")
    off, neutral = {}, 0
    for goal, cat, top in tops:
        for r in top:
            if r.subcategory not in EXPECTED_TYPES[goal]:
                off.setdefault(f"{r.category} / {r.subcategory}", []).append(goal)
                neutral += r.intent_score == 0.5
    total_off = sum(len(v) for v in off.values())
    print(f"  {total_off}/{slots} slots ({pct(total_off/slots)}) are not an expected type "
          f"({neutral} of them only got the neutral intent score 0.50 = type not listed in the config). "
          "Most common:")
    for label, gs in sorted(off.items(), key=lambda kv: -len(kv[1]))[:8]:
        print(f"    {len(gs):3d} x {label}  (goals: {', '.join(sorted(set(gs))[:4])})")

    print("\n[P4] Goals with weak results (hybrid, no category filter)")
    for e in evals["all"]:
        scores = {name: metric(facts, e["tops"]["hybrid"], e["goal"], fn)
                  for name, fn in METRICS.items()}
        weak = [f"{n} {pct(s)}" for n, s in scores.items() if s < 0.7]
        if weak:
            print(f"    {e['goal']}: " + ", ".join(weak))

    print("\n[P5] How much does each part of the score actually move the ranking?")
    print("  influence = weight x standard deviation of the component across all candidates "
          "(no category filter), averaged over goals. Bigger = separates products more.")
    parts = ["goal", "similarity", "intent", "review", "rating", "popularity"]
    table(["component", "weight", "avg influence"],
          [[p, WEIGHTS[p], f"{statistics.mean(e['influence'][p] for e in evals['all'] if p in e['influence']):.4f}"]
           for p in parts])
    scores = [s for e in evals["all"][:1] for s in e["review_scores"]]
    ratings = [s for e in evals["all"][:1] for s in e["ratings"]]
    q = lambda xs, f: sorted(xs)[int(f * (len(xs) - 1))]
    print(f"  review_score (n={len(scores)}): min {min(scores):.2f}, p10 {q(scores, .1):.2f}, "
          f"median {q(scores, .5):.2f}, p90 {q(scores, .9):.2f}, max {max(scores):.2f}, "
          f"std {statistics.pstdev(scores):.3f}")
    print(f"  rating       (n={len(ratings)}): min {min(ratings):.2f}, p10 {q(ratings, .1):.2f}, "
          f"median {q(ratings, .5):.2f}, p90 {q(ratings, .9):.2f}, max {max(ratings):.2f}, "
          f"std {statistics.pstdev(ratings):.3f}")

    print("\n[P6] Is the similarity part tiny for narrow goals?")
    table(["goal", "median sim (all candidates)", "mean sim (top-10)"],
          [[e["goal"], f"{e['sim_pool_median']:.2f}", f"{e['sim_top_mean']:.2f}"]
           for e in evals["all"]])

    print("\n[P7] Products with empty or very short ingredient lists")
    no_list = [pid for pid in products if not facts.ingredients[pid]]
    few = [pid for pid in products if 0 < len(facts.ingredients[pid]) <= 3]
    print(f"  catalogue: {len(no_list)} products have NO parsed ingredients "
          f"({pct(len(no_list)/len(products))}), {len(few)} have 1-3")
    top_no = [r for _, _, top in tops for r in top if not facts.ingredients[r.product_id]]
    top_few = [r for _, _, top in tops for r in top if 0 < len(facts.ingredients[r.product_id]) <= 3]
    print(f"  in the hybrid top-10s: {len(top_no)} slots with no ingredients, "
          f"{len(top_few)} with 1-3 ingredients (of {slots})")
    for r in (top_no + top_few)[:4]:
        print(f"    e.g. {r.product_name[:50]} ({r.subcategory}) score {r.score:.3f}, "
              f"{len(facts.ingredients[r.product_id])} ingredients")
    empty_ranks = sorted(e["best_empty_rank"] for e in evals["all"] if e["best_empty_rank"])
    print(f"  best rank of a product with no ingredient list, per goal (no category filter): "
          f"{empty_ranks}")
    for category in (None, "Skincare"):
        res = engine.recommend(RecommendationRequest(category=category, top_k=TOP_K))
        n_empty = sum(not facts.ingredients[r.product_id] for r in res)
        n_gift = sum(r.subcategory in GIFT_OR_MINI or r.category == "Mini Size" for r in res)
        print(f"  request WITHOUT goals, category={category}: top-10 has {n_empty} without ingredient "
              f"list, {n_gift} gift sets/minis (ranked by rating, popularity, reviews only)")
    ff = [(req, res) for req, res in grid_results
          if any(_lower(x) in ("fragrance", "parfum") for x in req.excluded_ingredients)]
    ff_products = [r for _, res in ff for r in res]
    ff_no_list = [r for r in ff_products if not facts.ingredients[r.product_id]]
    ff_leak = [r for r in ff_products if any(
        w in facts.products[r.product_id]["raw"] for w in ("fragrance", "parfum"))]
    ff_allergen = [r for r in ff_products if any(
        a in n for n in facts.ingredients[r.product_id] for a in ALLERGENS)]
    n = max(len(ff_products), 1)
    print(f"  'fragrance-free' answers ({len(ff)} requests, {len(ff_products)} products):")
    print(f"    {len(ff_no_list)} ({pct(len(ff_no_list)/n)}) have NO ingredient list at all "
          "(unknown, counted as fragrance-free)")
    print(f"    {len(ff_leak)} mention fragrance/parfum in the raw text (parser missed it)")
    print(f"    {len(ff_allergen)} ({pct(len(ff_allergen)/n)}) still list a fragrance allergen "
          "such as limonene/linalool (documented limitation)")

    print("\n[P8] Price filter edge cases (engine vs our own SQL data, no goals, every candidate)")
    for label, kwargs, test in [
        ("max_price=25", {"max_price": 25}, lambda p: p <= 25),
        ("max_price=60", {"max_price": 60}, lambda p: p <= 60),
        ("min_price=60", {"min_price": 60}, lambda p: p >= 60),
    ]:
        got = {r.product_id for r in engine.recommend(RecommendationRequest(top_k=BIG, **kwargs))}
        want = {pid for pid, p in products.items() if p["price"] is not None and test(p["price"])}
        bound = kwargs.get("max_price") or kwargs.get("min_price")
        on_bound = sum(1 for pid in want if products[pid]["price"] == bound)
        print(f"    {label}: engine {len(got)}, expected {len(want)} -> "
              f"{'OK' if got == want else 'MISMATCH'} ({on_bound} products priced exactly {bound})")

    print("\n[P9] 'Required ingredient' recall (engine matches the exact ingredient name)")
    rows = []
    for name in ("glycerin", "niacinamide", "hyaluronic acid", "salicylic acid", "zinc oxide"):
        got = {r.product_id for r in engine.recommend(
            RecommendationRequest(required_ingredients=[name], top_k=BIG))}
        in_text = {pid for pid, p in products.items() if name in p["raw"]}
        real = {pid for pid in got if name in facts.primary[pid]}
        rows.append([name, len(got), len(real), len(in_text), pct(len(got & in_text) / max(len(in_text), 1))])
    table(["required", "engine returns", "of which real ingredient", "raw text mentions",
           "found / raw text"], rows)
    print("  'real ingredient' = listed as a main ingredient; the rest are only 'may contain'.")

    print("\n[P10] Odd inputs")
    for label, req in [
        ("category ' Skincare ' (spaces)", RecommendationRequest(goals=["hydration"], category=" Skincare ")),
        ("category 'SKINCARE'", RecommendationRequest(goals=["hydration"], category="SKINCARE")),
        ("goal 'not_a_goal'", RecommendationRequest(goals=["not_a_goal"], category="Skincare")),
        ("no goals at all", RecommendationRequest(category="Skincare")),
    ]:
        res = engine.recommend(req)
        print(f"    {label}: {len(res)} results"
              + (f", first: {res[0].product_name[:40]}" if res else ""))

    print("\n[P11] Excluding an ingredient matches its exact name only")
    got = engine.recommend(RecommendationRequest(
        category="Skincare", excluded_ingredients=["alcohol"], top_k=BIG))
    denat = [r for r in got if any(
        n.startswith(("alcohol denat", "sd alcohol")) for n in facts.ingredients[r.product_id])]
    print(f"  excluded=['alcohol'] (Skincare) returns {len(got)} products, "
          f"{len(denat)} of them still list 'alcohol denat.' / 'SD alcohol'")

    print("\n[P12] Results with NO ingredient evidence for the goal (grid requests with one goal)")
    rows, example = [], "-"
    for category in (None, "Skincare", "Hair", "Makeup"):
        slots_c = [r for req, res in grid_results
                   if req.category == category and len(req.goals) == 1 and req.goals[0] in GOALS
                   and not req.subcategory and not req.required_ingredients
                   for r in res]
        none_c = [r for r in slots_c if not r.matched_goals]
        rows.append([category or "(none)", len(slots_c), len(none_c), pct(len(none_c) / max(len(slots_c), 1))])
        if category == "Hair" and none_c:
            example = ", ".join(f"{r.product_name[:30]} ({r.subcategory})" for r in none_c[:3])
    table(["category filter", "result slots", "no goal ingredient", "share"], rows)
    print(f"  e.g. with category=Hair (goals such as uv_protection): {example}")

    print("\n[P13] Review signals only exist for one category")
    counts = {}
    for pid, p in products.items():
        total, with_reviews = counts.get(p["category"], (0, 0))
        counts[p["category"]] = (total + 1, with_reviews + (pid in facts.reviewed))
    table(["category", "products", "with review signals"],
          [[c, t, w] for c, (t, w) in sorted(counts.items(), key=lambda kv: -kv[1][0])])
    value = statistics.mean(e["influence"]["review"] for e in evals["all"])
    presence = statistics.mean(e["boost"] for e in evals["all"])
    print(f"  A better review score moves the final score by about {value:.3f} "
          f"(weight x std among reviewed products),")
    print(f"  but HAVING a review score moves it by {presence:+.3f} on average "
          "(the weight is dropped and the rest renormalised, review scores are high: ~0.84).")
    print("  Best good un-reviewed product per goal, rank without reviews -> hybrid rank (no category filter):")
    for e in evals["all"]:
        if e["best_unreviewed"]:
            name, sub, plain, hybrid = e["best_unreviewed"]
            print(f"    {e['goal']}: {name[:45]} ({sub}) {plain} -> {hybrid}")


# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    parser.add_argument("--quick", action="store_true", help="small grid (about a minute)")
    args = parser.parse_args()

    started = time.time()
    engine = RecommendationEngine()
    facts = Facts(connect())
    print(f"Catalogue: {len(facts.products)} products, {len(facts.reviewed)} with review signals, "
          f"{len(facts.fragrance_ids)} with a fragrance ingredient.")

    print("\n" + "=" * 78 + "\n1. HARD CHECKS (own SQL, must all hold)\n" + "=" * 78)
    grid_results, _ = hard_checks(engine, facts, args.quick)

    print("\n" + "=" * 78 + "\n2 + 3. PLAUSIBILITY METRICS AND BASELINES\n" + "=" * 78)
    evals = plausibility_and_baselines(engine, facts, args.quick)

    print("\n" + "=" * 78 + "\n4. KNOWN-ANSWER SPOT CHECKS\n" + "=" * 78)
    spot_checks(engine, facts)

    print("\n" + "=" * 78 + "\n5. PROBLEMS FOUND\n" + "=" * 78)
    problems(engine, facts, evals, grid_results)
    print(f"\nDone in {time.time() - started:.0f} seconds.")


if __name__ == "__main__":
    main()
