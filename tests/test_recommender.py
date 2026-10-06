from src.recommender.models import RecommendationRequest
from src.recommender.scorer import (
    component_scores,
    hybrid_score,
    product_intent_score,
    rating_score,
    saturating_score,
)


def test_saturating_score():
    assert saturating_score(0) == 0.0
    assert saturating_score(1) > 0.0
    assert saturating_score(5) > saturating_score(1)

    # Score should remain bounded.
    assert saturating_score(100) < 1.0


def test_rating_score():
    assert rating_score(5) == 1.0
    assert rating_score(0) == 0.0
    assert rating_score(None) == 0.0


def test_product_intent_score():
    assert product_intent_score(
        "Moisturizers",
        ["hydration"],
    ) == 1.0

    assert product_intent_score(
        "Cleansers",
        ["hydration"],
    ) == 0.45

    # A type missing from the goal's list is a poor fit; an unknown goal is neutral.
    assert product_intent_score("Unknown", ["hydration"]) == 0.25
    assert product_intent_score("Moisturizers", ["no_such_goal"]) == 0.5


def test_component_scores():
    components = component_scores(
        match_count=3,
        rating=4.5,
        review_count=100,
        loves_count=50,
        subcategory="Moisturizers",
        goals=["hydration"],
        similarity=0.8,
        review_score=0.7,
    )

    assert 0.0 < components["goal"] < 1.0
    assert components["similarity"] == 0.8
    assert components["intent"] == 1.0
    assert components["review"] == 0.7
    assert components["rating"] == 0.9
    assert 0.0 <= components["popularity"] <= 1.0

    assert 0.0 < hybrid_score(components) <= 1.0


def test_recommendation_request_defaults():
    request = RecommendationRequest()

    assert request.category is None
    assert request.goals == []
    assert request.top_k == 10