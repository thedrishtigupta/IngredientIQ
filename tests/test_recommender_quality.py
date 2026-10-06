"""
Fast quality checks for the recommender. They need the database and are
skipped when it is not reachable. The full report is scripts/evaluate_recommender.py.

The checks re-read the rules from the database tables with their own SQL
(Facts in the evaluation script), so they do not trust the engine's filter code.
"""
import sys
from pathlib import Path

import psycopg
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.evaluate_recommender import (  # noqa: E402
    Facts,
    check_request,
    connect,
    describe,
    evaluate_goal,
    metric,
    type_hit,
)
from src.recommender import RecommendationEngine, RecommendationRequest  # noqa: E402


@pytest.fixture(scope="module")
def world():
    try:
        facts = Facts(connect())  # connect() gives up after 5 seconds
        engine = RecommendationEngine()
    except psycopg.Error as exc:
        pytest.skip(f"database not reachable or not loaded: {exc}")
    return engine, facts


def small_grid():
    grid = [
        RecommendationRequest(
            goals=[goal], category=category, max_price=price,
            excluded_ingredients=["fragrance"] if fragrance_free else [],
        )
        for goal in ("hydration", "uv_protection")
        for category in (None, "Skincare")
        for price in (None, 25)
        for fragrance_free in (False, True)
    ]
    grid += [
        RecommendationRequest(goals=["hydration"], required_ingredients=["glycerin"]),
        RecommendationRequest(goals=["brightening"], required_ingredients=["niacinamide"],
                              category="Skincare"),
        RecommendationRequest(goals=["hair_conditioning"], category="Hair", min_price=20),
        RecommendationRequest(required_ingredients=["glycerin"]),  # no goals
    ]
    return grid


def test_filters_ranges_order_and_formula_hold(world):
    """Category, price, required / excluded / fragrance, 0..1 ranges, sort order, formula."""
    engine, facts = world
    problems = []
    for req in small_grid():
        _, bad = check_request(engine, facts, req, twice=False)
        problems += [f"{describe(req)}: {why}" for why in bad]
    assert problems == []


def test_same_request_gives_same_answer(world):
    engine, facts = world
    for req in (
        RecommendationRequest(goals=["hydration"], category="Skincare", max_price=25,
                              excluded_ingredients=["fragrance"]),
        RecommendationRequest(goals=["uv_protection"]),
    ):
        _, bad = check_request(engine, facts, req, twice=True)
        assert bad == []


def test_fragrance_free_answers_have_no_fragrance_word_in_the_raw_text(world):
    engine, facts = world
    results = engine.recommend(RecommendationRequest(
        goals=["hydration"], category="Skincare", excluded_ingredients=["fragrance"]))
    assert results
    for r in results:
        raw = facts.products[r.product_id]["raw"]
        assert "fragrance" not in raw and "parfum" not in raw, r.product_name


@pytest.mark.parametrize("goal", ["hydration", "uv_protection"])
def test_hybrid_top10_is_mostly_the_right_product_type(world, goal):
    """Hybrid should be mostly the right type, and far better than random picks."""
    engine, facts = world
    top_lists = evaluate_goal(engine, facts, goal, None)["tops"]
    hybrid = metric(facts, top_lists["hybrid"], goal, type_hit)
    random_pick = metric(facts, top_lists["random"], goal, type_hit)
    assert hybrid >= 0.8
    assert hybrid > random_pick + 0.3
