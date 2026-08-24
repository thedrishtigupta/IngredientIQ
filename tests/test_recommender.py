from src.recommender.models import RecommendationRequest
from src.recommender.scorer import (
    calculate_score,
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

    assert product_intent_score(
        "Unknown",
        ["hydration"],
    ) == 0.5


def test_calculate_score():
    result = calculate_score(
        match_count=3,
        rating=4.5,
        review_count=100,
        loves_count=50,
        subcategory="Moisturizers",
        goals=["hydration"],
    )

    assert len(result) == 5

    (
        final_score,
        goal_score,
        intent_score,
        rating_component,
        popularity_component,
    ) = result

    assert 0.0 < final_score <= 1.0
    assert 0.0 < goal_score < 1.0
    assert intent_score == 1.0
    assert rating_component == 0.9
    assert 0.0 <= popularity_component <= 1.0


def test_recommendation_request_defaults():
    request = RecommendationRequest()

    assert request.category is None
    assert request.goals == []
    assert request.top_k == 10