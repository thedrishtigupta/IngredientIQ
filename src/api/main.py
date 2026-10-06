"""IngredientIQ API.

Run:  python -m uvicorn src.api.main:app --port 8000   (from the project root, venv active)
Docs: http://localhost:8000/docs
"""
import logging
import os
from contextlib import asynccontextmanager

import psycopg
from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from psycopg.rows import dict_row

from src.api.schemas import (
    Category,
    Goal,
    Health,
    IngredientDetail,
    IngredientListItem,
    ProductDetail,
    ProductSummary,
    RecommendBody,
    RecommendResponse,
    SimilarProduct,
)
from src.llm.openrouter import explain_results, llm_enabled, template_summary
from src.recommender import RecommendationEngine, RecommendationRequest
from src.recommender.config import GOAL_LABELS, HYBRID_WEIGHTS
from src.recommender.repository import ProductRepository
from src.recommender.vectors import VectorIndex

log = logging.getLogger("ingredientiq.api")

# If the database does not answer, give up after 5 seconds (-> HTTP 503) instead of hanging.
os.environ.setdefault("PGCONNECT_TIMEOUT", "5")

# The vector index is built once and shared by all requests (it is only read, never changed).
_index = None


def get_index(conn):
    """Return the shared VectorIndex, building it from the database the first time."""
    global _index
    if _index is None:  # ponytail: no lock; two first requests at once just build it twice
        _index = VectorIndex.from_db(conn)
    return _index


@asynccontextmanager
async def lifespan(app):
    # Build the index at startup. If the database is down, start anyway:
    # the index is built on the first request that needs it.
    try:
        repo = ProductRepository()
        try:
            get_index(repo.connection)
        finally:
            repo.close()
    except psycopg.Error as e:
        log.warning("Database not reachable at startup (%s); index built on first request", e)
    yield


app = FastAPI(
    title="IngredientIQ API",
    description="Ingredient-aware beauty product recommendations (Sephora data).",
    lifespan=lifespan,
)

# The frontend dev server runs on another port, so allow any localhost origin.
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"^http://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(psycopg.OperationalError)
async def database_down(request: Request, exc: psycopg.OperationalError):
    """Any lost or refused database connection becomes a clean 503 instead of a stack trace."""
    return JSONResponse(
        status_code=503,
        content={"detail": "Database unreachable. Is the ingredientiq-db container running?"},
    )


def get_repo():
    """One repository (= one DB connection) per request, always closed afterwards."""
    repo = ProductRepository()
    try:
        yield repo
    finally:
        repo.close()


def query(repo, sql, params=()):
    """Run a SELECT and return the rows as a list of dicts."""
    with repo.connection.cursor(row_factory=dict_row) as cur:
        cur.execute(sql, params)
        return cur.fetchall()


def query_one(repo, sql, params=()):
    rows = query(repo, sql, params)
    return rows[0] if rows else None


# Columns shared by the light product lists (search, similar).
SUMMARY_COLUMNS = "product_id, product_name, brand, category, subcategory, price, rating, review_count"


# ---------- small endpoints ----------

@app.get("/health", response_model=Health)
def health():
    """Is the API up, can it reach the database, is an LLM key configured?"""
    try:
        repo = ProductRepository()
    except psycopg.Error:
        return Health(status="degraded", db=False, llm_enabled=llm_enabled(), products=0)
    try:
        products = query_one(repo, "SELECT count(*) AS n FROM products")["n"]
        reviewed = query_one(
            repo, "SELECT count(*) AS n, COALESCE(sum(review_count), 0)::bigint AS reviews FROM product_review_summary"
        )
    finally:
        repo.close()
    return Health(
        status="ok",
        db=True,
        llm_enabled=llm_enabled(),
        products=products,
        reviewed_products=reviewed["n"],
        reviews=reviewed["reviews"],
    )


@app.get("/goals", response_model=list[Goal])
def goals():
    """The goals a user can pick (for /recommend)."""
    supported = _index.supported_goals if _index else []
    return [
        Goal(id=goal_id, label=label, supported_by_vectors=goal_id in supported)
        for goal_id, label in GOAL_LABELS.items()
    ]


@app.get("/categories", response_model=list[Category])
def categories(repo=Depends(get_repo)):
    """Categories with their subcategories and product counts (for the filter dropdowns)."""
    rows = query(
        repo,
        """SELECT category, subcategory, count(*) AS n FROM products
           WHERE category IS NOT NULL GROUP BY category, subcategory ORDER BY category, subcategory""",
    )
    by_category = {}
    for row in rows:
        cat = by_category.setdefault(
            row["category"], {"category": row["category"], "product_count": 0, "subcategories": []}
        )
        cat["product_count"] += row["n"]
        if row["subcategory"]:
            cat["subcategories"].append({"name": row["subcategory"], "product_count": row["n"]})
    return sorted(by_category.values(), key=lambda c: -c["product_count"])


# ---------- recommendations ----------

@app.post("/recommend", response_model=RecommendResponse)
def recommend(body: RecommendBody, repo=Depends(get_repo)):
    """Rank products for the user's goals and filters, best first."""
    engine = RecommendationEngine(repository=repo, vector_index=get_index(repo.connection))
    results = engine.recommend(
        RecommendationRequest(
            category=body.category,
            subcategory=body.subcategory,
            min_price=body.min_price,
            max_price=body.max_price,
            goals=body.goals,
            required_ingredients=body.required_ingredients,
            excluded_ingredients=body.excluded_ingredients,
            top_k=body.top_k,
        )
    )

    items = [r.to_dict() for r in results]
    llm_wrote_text = False
    if body.explain:
        # LLM text if a key is set, otherwise a fixed template. Never raises.
        texts = explain_results(results, body.goals)
        # True only if at least one text really came from the LLM (not the template fallback).
        llm_wrote_text = llm_enabled() and any(
            texts.get(r.product_id) != template_summary(r, body.goals) for r in results
        )
        for item in items:
            explanation = item["explanation"] or {"strengths": [], "weaknesses": []}
            explanation["summary"] = texts.get(item["product_id"])
            item["explanation"] = explanation

    return {
        "count": len(items),
        "llm_used": bool(body.explain and items and llm_wrote_text),
        "request": body,
        "weights": HYBRID_WEIGHTS,
        "results": items,
    }


# ---------- products ----------

@app.get("/products", response_model=list[ProductSummary])
def search_products(
    q: str = Query("", description="Text to look for in the product name or brand"),
    category: str | None = None,
    limit: int = Query(20, ge=1, le=50),
    repo=Depends(get_repo),
):
    """Simple text search. Most-loved products first."""
    sql = f"SELECT {SUMMARY_COLUMNS} FROM products WHERE (product_name ILIKE %s OR brand ILIKE %s)"
    params = [f"%{q}%", f"%{q}%"]
    if category:
        sql += " AND LOWER(category) = LOWER(%s)"
        params.append(category)
    sql += " ORDER BY loves_count DESC NULLS LAST, product_id LIMIT %s"
    params.append(limit)
    return query(repo, sql, params)


@app.get("/products/{product_id}", response_model=ProductDetail)
def product_detail(product_id: str, repo=Depends(get_repo)):
    """Everything we know about one product: ingredients, functional profile, review data."""
    product = query_one(
        repo,
        """SELECT product_id, product_name, brand, category, subcategory, price, sale_price_usd,
                  rating, review_count, loves_count, highlights, variation_type, variation_value,
                  limited_edition, is_new, online_only, out_of_stock, sephora_exclusive
           FROM products WHERE product_id = %s""",
        (product_id,),
    )
    if product is None:
        raise HTTPException(404, f"Product {product_id} not found")

    # The ingredient list in label order. "main" is the normal list; other sections
    # are shade/variant-specific lists.
    product["ingredients"] = query(
        repo,
        """SELECT pi.ingredient_id, pi.position, i.canonical_name AS name, pi.presence_type, pi.section, pi.concentration,
                  COALESCE(ik.functional_groups, '[]'::jsonb) AS functional_groups,
                  COALESCE(ik.user_goals, '[]'::jsonb) AS user_goals
           FROM product_ingredients pi
           JOIN ingredients i ON i.ingredient_id = pi.ingredient_id
           LEFT JOIN ingredient_knowledge ik ON ik.ingredient_id = pi.ingredient_id
           WHERE pi.product_id = %s
           ORDER BY (pi.section <> 'main'), pi.section, pi.position""",
        (product_id,),
    )

    profile = query_one(
        repo, "SELECT features FROM product_functional_profiles WHERE product_id = %s", (product_id,)
    )
    product["functional_profile"] = profile["features"] if profile else None

    product["review_signals"] = query_one(
        repo,
        """SELECT review_count, analyzed_count, avg_sentiment, positive_share, negative_share,
                  review_score, aspects, method
           FROM product_review_signals WHERE product_id = %s""",
        (product_id,),
    )
    product["review_summary"] = query_one(
        repo,
        """SELECT review_count, average_review_rating, recommendation_count, recommendation_rate,
                  average_helpfulness, review_text_count, earliest_review_date, latest_review_date
           FROM product_review_summary WHERE product_id = %s""",
        (product_id,),
    )
    return product


@app.get("/products/{product_id}/similar", response_model=list[SimilarProduct])
def similar_products(product_id: str, k: int = Query(5, ge=1, le=20), repo=Depends(get_repo)):
    """Products with the most similar ingredient-function mix (cosine similarity),
    from the same category as the product."""
    source = query_one(repo, "SELECT category FROM products WHERE product_id = %s", (product_id,))
    if source is None:
        raise HTTPException(404, f"Product {product_id} not found")

    # Ingredient mix alone ignores product type (a face cream can sit next to a
    # mascara), so look at a wide pool of neighbours and keep the same-category ones.
    pairs = get_index(repo.connection).similar_products(product_id, 200)  # [(id, cosine), ...]
    rows = query(
        repo,
        f"SELECT {SUMMARY_COLUMNS} FROM products WHERE product_id = ANY(%s)",
        ([pid for pid, _ in pairs],),
    )
    info = {row["product_id"]: row for row in rows}
    same_category = [
        (pid, cosine) for pid, cosine in pairs
        if pid in info and info[pid]["category"] == source["category"]
    ]
    return [{**info[pid], "similarity": round(cosine, 4)} for pid, cosine in same_category[:k]]


# ---------- ingredients ----------

@app.get("/ingredients", response_model=list[IngredientListItem])
def list_ingredients(
    q: str = Query("", description="Text to look for in the ingredient name"),
    limit: int = Query(50, ge=1, le=200),
    repo=Depends(get_repo),
):
    """Ingredients found in the most products first. Counts each product once (~0.3 s).

    MATERIALIZED: without it Postgres picks a slow plan for some searches (6 s for "hyalur").
    """
    return query(
        repo,
        """WITH counts AS MATERIALIZED (
               SELECT ingredient_id, count(DISTINCT product_id) AS product_count
               FROM product_ingredients GROUP BY ingredient_id)
           SELECT i.ingredient_id, i.canonical_name AS name, c.product_count,
                  COALESCE(ik.functional_groups, '[]'::jsonb) AS functional_groups
           FROM ingredients i
           JOIN counts c ON c.ingredient_id = i.ingredient_id
           LEFT JOIN ingredient_knowledge ik ON ik.ingredient_id = i.ingredient_id
           WHERE i.canonical_name ILIKE %s
           ORDER BY c.product_count DESC, i.canonical_name LIMIT %s""",
        (f"%{q}%", limit),
    )


@app.get("/ingredients/{ingredient_id}", response_model=IngredientDetail)
def ingredient_detail(ingredient_id: int, repo=Depends(get_repo)):
    """One ingredient: what it does, how common it is, what it appears with, products using it."""
    ingredient = query_one(
        repo,
        """SELECT i.ingredient_id, i.canonical_name AS name,
                  COALESCE(ik.functional_groups, '[]'::jsonb) AS functional_groups,
                  COALESCE(ik.user_goals, '[]'::jsonb) AS user_goals
           FROM ingredients i LEFT JOIN ingredient_knowledge ik ON ik.ingredient_id = i.ingredient_id
           WHERE i.ingredient_id = %s""",
        (ingredient_id,),
    )
    if ingredient is None:
        raise HTTPException(404, f"Ingredient {ingredient_id} not found")

    # Products that contain it (a product counts once even if it lists the ingredient in several sections).
    with_it = "SELECT DISTINCT product_id FROM product_ingredients WHERE ingredient_id = %s"
    stats = query_one(
        repo,
        f"""SELECT count(*) AS product_count, avg(rating) AS avg_rating,
                   percentile_cont(0.5) WITHIN GROUP (ORDER BY price) AS median_price,
                   (SELECT count(*) FROM products) AS all_products
            FROM products WHERE product_id IN ({with_it})""",
        (ingredient_id,),
    )
    ingredient["product_count"] = stats["product_count"]
    ingredient["catalog_share"] = stats["product_count"] / stats["all_products"]
    ingredient["avg_rating"] = round(float(stats["avg_rating"]), 2) if stats["avg_rating"] is not None else None
    ingredient["median_price"] = stats["median_price"]
    ingredient["related"] = query(
        repo,
        f"""SELECT i.ingredient_id, i.canonical_name AS name, count(DISTINCT b.product_id) AS product_count
            FROM ({with_it}) a
            JOIN product_ingredients b ON b.product_id = a.product_id AND b.ingredient_id <> %s
            JOIN ingredients i ON i.ingredient_id = b.ingredient_id
            GROUP BY i.ingredient_id, i.canonical_name
            ORDER BY product_count DESC, i.canonical_name LIMIT 6""",
        (ingredient_id, ingredient_id),
    )
    ingredient["products"] = query(
        repo,
        f"""SELECT {SUMMARY_COLUMNS} FROM products WHERE product_id IN ({with_it})
            ORDER BY loves_count DESC NULLS LAST, product_id LIMIT 12""",
        (ingredient_id,),
    )
    return ingredient
