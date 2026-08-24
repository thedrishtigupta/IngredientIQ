from src.recommender.explanations import build_explanation
from src.recommender.models import RecommendationResult


def make_result(**overrides):
    data = dict(
        product_id="P123",
        product_name="Test Moisturizer",
        brand="Test Brand",
        category="Skincare",
        subcategory="Moisturizers",
        price=30.0,
        rating=4.7,
        review_count=1000,
        loves_count=500,
        score=0.90,
        goal_match_score=0.85,
        intent_score=1.0,
        rating_score=0.94,
        popularity_score=0.80,
        matched_goals=["hydration"],
        matched_ingredients=[
            "glycerin",
            "hyaluronic acid",
        ],
    )

    data.update(overrides)
    return RecommendationResult(**data)

def test_strong_recommendation_explanation():
    result = make_result()

    explanation = build_explanation(result)

    assert explanation.strengths
    assert result.matched_goals == ["hydration"]
    assert "glycerin" in result.matched_ingredients



def test_weak_goal_match_creates_warning():

    result = make_result(
        goal_match_score=0.30,
        intent_score=0.40,
        rating=3.5,
        popularity_score=0.30,
    )

    explanation = build_explanation(result)

    assert explanation.weaknesses



def test_low_goal_score_creates_weakness():

    result = make_result(
        goal_match_score=0.30,
        intent_score=0.80,
    )

    explanation = build_explanation(result)

    assert any(
        "Limited ingredient evidence" in weakness
        for weakness in explanation.weaknesses
    )


def test_low_intent_score_creates_weakness():

    result = make_result(
        goal_match_score=0.80,
        intent_score=0.40,
    )

    explanation = build_explanation(result)

    assert any(
        "less aligned" in weakness
        for weakness in explanation.weaknesses
    )


def test_high_rating_creates_strength():

    result = make_result(rating=4.8)

    explanation = build_explanation(result)

    assert any(
        "Highly rated" in strength
        for strength in explanation.strengths
    )


def test_low_rating_creates_weakness():

    result = make_result(rating=3.2)

    explanation = build_explanation(result)

    assert any(
        "Lower rating" in weakness
        for weakness in explanation.weaknesses
    )


def test_high_popularity_creates_strength():

    result = make_result(popularity_score=0.90)

    explanation = build_explanation(result)

    assert "Strong popularity signal." in explanation.strengths


def test_low_popularity_creates_weakness():

    result = make_result(popularity_score=0.20)

    explanation = build_explanation(result)

    assert "Limited popularity signal." in explanation.weaknesses

def test_recommendation_result_to_dict():

    result = make_result()

    result.explanation = build_explanation(result)

    data = result.to_dict()

    assert data["product_id"] == result.product_id
    assert data["product_name"] == result.product_name
    assert data["price"] == result.price
    assert data["rating"] == result.rating

    assert data["matched_goals"] == result.matched_goals
    assert data["matched_ingredients"] == result.matched_ingredients

    assert data["explanation"] is not None
    assert (
        data["explanation"]["strengths"]
        == result.explanation.strengths
    )
    assert (
        data["explanation"]["weaknesses"]
        == result.explanation.weaknesses
    )