import psycopg
import pytest

from src.recommender.config import (
    GOAL_LABELS,
    GOAL_SUBCATEGORY_AFFINITY,
    HYBRID_WEIGHTS,
)
from src.recommender.engine import RecommendationEngine
from src.recommender.explanations import build_explanation
from src.recommender.filters import filter_products
from src.recommender.models import RecommendationRequest, RecommendationResult
from src.recommender.repository import ProductRepository
from src.recommender.scorer import (
    component_scores,
    goal_curve_steepness,
    hybrid_score,
    saturating_score,
)


# ---------------------------------------------------------------
# Small fakes, so the engine can be tested without a database
# ---------------------------------------------------------------

def make_product(product_id, subcategory="Moisturizers", price=30.0):
    # (product_id, name, brand, category, subcategory,
    #  price, rating, review_count, loves_count)
    return (
        product_id,
        f"Product {product_id}",
        "Brand",
        "Skincare",
        subcategory,
        price,
        4.5,
        100,
        50,
    )


class FakeRepository:
    def __init__(self, products, ingredients=None, review_signals=None):
        self.products = products
        self.ingredients = ingredients or {}
        self.review_signals = review_signals or {}

    def find_candidates(self, **filters):
        return self.products

    def get_product_ingredient_names(self, product_ids):
        return self.ingredients

    def get_goal_matches(self, product_ids, goals):
        return {}

    def count_goal_ingredients(self, goals):
        return 40

    def get_review_signals(self, product_ids):
        return self.review_signals


class FakeVectorIndex:
    def __init__(self, similarity=0.6, knows_goals=True):
        self.similarity_value = similarity
        self.knows_goals = knows_goals

    def goal_vector(self, goals):
        return [1.0] if self.knows_goals else None

    def similarity(self, goals, product_ids):
        return {pid: self.similarity_value for pid in product_ids}


# ---------------------------------------------------------------
# Weights and the hybrid formula
# ---------------------------------------------------------------

def test_hybrid_weights_sum_to_one():
    assert sum(HYBRID_WEIGHTS.values()) == pytest.approx(1.0)


def test_every_affinity_goal_has_a_label():
    for goal in GOAL_SUBCATEGORY_AFFINITY:
        assert goal in GOAL_LABELS


def test_hybrid_score_is_weighted_sum():
    components = {
        "goal": 1.0,
        "similarity": 0.5,
        "intent": 1.0,
        "review": 0.8,
        "rating": 0.9,
        "popularity": 0.4,
    }

    expected = (
        0.30 * 1.0
        + 0.20 * 0.5
        + 0.15 * 1.0
        + 0.15 * 0.8
        + 0.12 * 0.9
        + 0.08 * 0.4
    )

    assert hybrid_score(components) == pytest.approx(expected)


def test_missing_review_renormalises_the_other_weights():
    components = {
        "goal": 1.0,
        "similarity": 0.5,
        "intent": 1.0,
        "review": None,
        "rating": 0.9,
        "popularity": 0.4,
    }

    weighted_sum = (
        0.30 * 1.0
        + 0.20 * 0.5
        + 0.15 * 1.0
        + 0.12 * 0.9
        + 0.08 * 0.4
    )

    # The review weight (0.15) is gone, so the rest is divided by 0.85.
    assert hybrid_score(components) == pytest.approx(weighted_sum / 0.85)


def test_missing_review_is_not_a_penalty():
    perfect_without_review = {
        "goal": 1.0,
        "similarity": 1.0,
        "intent": 1.0,
        "review": None,
        "rating": 1.0,
        "popularity": 1.0,
    }

    assert hybrid_score(perfect_without_review) == pytest.approx(1.0)


def test_hybrid_score_with_nothing_is_zero():
    assert hybrid_score({}) == 0.0


# ---------------------------------------------------------------
# Goal curve depends on how many ingredients the goal has
# ---------------------------------------------------------------

def test_long_goal_lists_keep_the_default_curve():
    assert goal_curve_steepness(40) == pytest.approx(0.15)
    assert goal_curve_steepness(None) == 0.15


def test_short_goal_lists_get_a_steeper_curve():
    # Exfoliation has 5 ingredients: having 4 of them must be a strong match.
    k = goal_curve_steepness(5)

    assert saturating_score(4, k) > 0.75
    assert saturating_score(4, 0.15) < 0.5


# ---------------------------------------------------------------
# No-goal mode
# ---------------------------------------------------------------

def test_no_goals_drops_goal_similarity_and_intent():
    components = component_scores(
        match_count=5,
        rating=4.0,
        review_count=100,
        loves_count=50,
        subcategory="Moisturizers",
        goals=[],
        similarity=0.9,
        review_score=0.8,
    )

    assert components["goal"] is None
    assert components["similarity"] is None
    assert components["intent"] is None

    # Only review, rating and popularity (0.15 + 0.12 + 0.08 = 0.35) are used.
    expected = (
        0.15 * 0.8
        + 0.12 * components["rating"]
        + 0.08 * components["popularity"]
    ) / 0.35

    assert hybrid_score(components) == pytest.approx(expected)


def test_engine_without_goals_never_needs_the_vector_index():
    repository = FakeRepository([make_product("P1")])
    engine = RecommendationEngine(repository=repository)

    results = engine.recommend(RecommendationRequest())

    assert len(results) == 1
    assert results[0].similarity_score == 0.0
    assert engine.vector_index is None


# ---------------------------------------------------------------
# Engine: ordering, missing review, unknown goal
# ---------------------------------------------------------------

def test_equal_scores_are_ordered_by_product_id():
    # Same data for all three, so the scores tie. Listed in a mixed order.
    products = [make_product("P3"), make_product("P1"), make_product("P2")]
    engine = RecommendationEngine(
        repository=FakeRepository(products),
        vector_index=FakeVectorIndex(),
    )

    request = RecommendationRequest(goals=["hydration"])

    first = [r.product_id for r in engine.recommend(request)]
    second = [r.product_id for r in engine.recommend(request)]

    assert first == ["P1", "P2", "P3"]
    assert second == first


def test_product_without_review_signal_has_no_review_score():
    repository = FakeRepository(
        [make_product("P1"), make_product("P2")],
        review_signals={
            "P1": {
                "review_score": 0.9,
                "avg_sentiment": 0.8,
                "analyzed_count": 50,
                "aspects": {},
            },
        },
    )
    engine = RecommendationEngine(
        repository=repository,
        vector_index=FakeVectorIndex(),
    )

    results = {
        r.product_id: r
        for r in engine.recommend(RecommendationRequest(goals=["hydration"]))
    }

    assert results["P1"].review_score == 0.9
    assert results["P2"].review_score is None


def test_goal_unknown_to_the_vector_index_drops_similarity():
    products = [make_product("P1")]

    known = RecommendationEngine(
        repository=FakeRepository(products),
        vector_index=FakeVectorIndex(similarity=0.0, knows_goals=True),
    ).recommend(RecommendationRequest(goals=["hydration"]))

    unknown = RecommendationEngine(
        repository=FakeRepository(products),
        vector_index=FakeVectorIndex(knows_goals=False),
    ).recommend(RecommendationRequest(goals=["hydration"]))

    # Similarity 0.0 counts against the product. "Unknown goal" leaves it out.
    assert unknown[0].similarity_score == 0.0
    assert unknown[0].score > known[0].score


def test_top_k_limits_results():
    products = [make_product(f"P{i}") for i in range(5)]
    engine = RecommendationEngine(repository=FakeRepository(products))

    results = engine.recommend(RecommendationRequest(top_k=2))

    assert len(results) == 2


# ---------------------------------------------------------------
# Fragrance-free filter
# ---------------------------------------------------------------

def run_filter(excluded, ingredient_map):
    products = [make_product(product_id) for product_id in ingredient_map]
    request = RecommendationRequest(excluded_ingredients=excluded)

    kept = filter_products(products, request, ingredient_map)

    return [product[0] for product in kept]


def test_excluding_fragrance_removes_every_spelling():
    ingredient_map = {
        "P1": {"glycerin", "fragrance"},
        "P2": {"glycerin", "parfum (fragrance)"},
        "P3": {"glycerin", "fragrance/parfum"},
        "P4": {"glycerin", "natural fragrance"},
        "P5": {"glycerin", "parfum"},
        "P6": {"glycerin", "squalane"},
    }

    assert run_filter(["fragrance"], ingredient_map) == ["P6"]
    assert run_filter(["Parfum"], ingredient_map) == ["P6"]


def test_other_exclusions_stay_exact_match():
    ingredient_map = {
        "P1": {"glycerin extract"},
        "P2": {"glycerin"},
    }

    # "glycerin" must not match "glycerin extract".
    assert run_filter(["glycerin"], ingredient_map) == ["P1"]


def test_fragrance_allergens_need_to_be_named():
    ingredient_map = {
        "P1": {"limonene", "linalool"},
        "P2": {"glycerin"},
    }

    # Excluding "fragrance" does not remove products that only list allergens.
    assert run_filter(["fragrance"], ingredient_map) == ["P1", "P2"]
    assert run_filter(["limonene"], ingredient_map) == ["P2"]


def test_without_fragrance_exclusion_fragrance_products_stay():
    ingredient_map = {"P1": {"fragrance"}, "P2": {"glycerin"}}

    assert run_filter([], ingredient_map) == ["P1", "P2"]


# ---------------------------------------------------------------
# Explanations for the new signals
# ---------------------------------------------------------------

def make_result(**overrides):
    data = dict(
        product_id="P1",
        product_name="Test Moisturizer",
        brand="Test Brand",
        category="Skincare",
        subcategory="Moisturizers",
        price=30.0,
        rating=4.2,
        review_count=1000,
        loves_count=500,
        score=0.80,
        goal_match_score=0.85,
        intent_score=1.0,
        rating_score=0.84,
        popularity_score=0.5,
        matched_goals=["hydration"],
        matched_ingredients=["glycerin"],
    )

    data.update(overrides)
    return RecommendationResult(**data)


def all_text(explanation):
    return " ".join(explanation.strengths + explanation.weaknesses)


def test_high_similarity_creates_strength():
    explanation = build_explanation(make_result(similarity_score=0.82))

    assert any(
        "good fit" in strength for strength in explanation.strengths
    )


def test_low_similarity_creates_weakness():
    explanation = build_explanation(make_result(similarity_score=0.05))

    assert any(
        "weakly similar" in weakness for weakness in explanation.weaknesses
    )


def test_zero_similarity_says_nothing():
    explanation = build_explanation(make_result(similarity_score=0.0))

    assert "similar" not in all_text(explanation)
    assert "good fit" not in all_text(explanation)


def test_high_review_score_creates_strength():
    explanation = build_explanation(make_result(review_score=0.92))

    assert any(
        "Reviewers are very positive" in strength
        for strength in explanation.strengths
    )


def test_low_review_score_creates_weakness():
    explanation = build_explanation(make_result(review_score=0.65))

    assert any(
        "less positive than for most products" in weakness
        for weakness in explanation.weaknesses
    )


def test_no_review_score_says_nothing_about_reviews():
    explanation = build_explanation(make_result(review_score=None))

    assert "Reviewers" not in all_text(explanation)


def test_best_and_worst_aspects_are_quoted():
    aspects = {
        "hydration": {"mentions": 120, "positive_share": 0.91},
        "scent": {"mentions": 40, "positive_share": 0.40},
        "texture": {"mentions": 60, "positive_share": 0.70},
    }

    explanation = build_explanation(
        make_result(review_score=0.82, aspects=aspects)
    )

    assert any(
        "mention hydration are 91% positive" in strength
        for strength in explanation.strengths
    )
    assert any(
        "mention scent are only 40% positive" in weakness
        for weakness in explanation.weaknesses
    )


def test_aspects_with_few_mentions_are_ignored():
    aspects = {"hydration": {"mentions": 2, "positive_share": 1.0}}

    explanation = build_explanation(
        make_result(review_score=0.7, aspects=aspects)
    )

    assert "hydration" not in all_text(explanation)


def test_no_goal_explanation_skips_goal_evidence():
    result = make_result(
        goal_match_score=0.0,
        intent_score=0.0,
        similarity_score=0.0,
        matched_goals=[],
        matched_ingredients=[],
        review_score=0.92,
    )

    explanation = build_explanation(result, has_goals=False)
    text = all_text(explanation)

    assert "requested goal" not in text
    assert "ingredient" not in text
    assert "Reviewers are very positive" in text


# ---------------------------------------------------------------
# Repository: missing table must not crash
# ---------------------------------------------------------------

class FailingCursor:
    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def execute(self, query, params):
        raise psycopg.errors.UndefinedTable("no such table")


class FakeConnection:
    def __init__(self):
        self.rolled_back = False

    def cursor(self):
        return FailingCursor()

    def rollback(self):
        self.rolled_back = True


def test_get_review_signals_returns_empty_when_table_is_missing():
    # Skip __init__ so no database connection is opened.
    repository = ProductRepository.__new__(ProductRepository)
    repository.connection = FakeConnection()

    assert repository.get_review_signals(["P1"]) == {}
    assert repository.connection.rolled_back


def test_get_review_signals_with_no_ids_returns_empty():
    repository = ProductRepository.__new__(ProductRepository)

    assert repository.get_review_signals([]) == {}


# ---------------------------------------------------------------
# Real database (skipped if Postgres is not reachable)
# ---------------------------------------------------------------

@pytest.fixture
def real_engine():
    try:
        engine = RecommendationEngine()
    except psycopg.OperationalError:
        pytest.skip("Postgres is not reachable")

    yield engine

    engine.repository.close()


def test_real_database_filters_and_determinism(real_engine):
    request = RecommendationRequest(
        category="Skincare",
        max_price=50,
        goals=["hydration"],
        excluded_ingredients=["fragrance"],
        top_k=10,
    )

    first = real_engine.recommend(request)
    second = real_engine.recommend(request)

    assert first
    assert [r.product_id for r in first] == [r.product_id for r in second]

    ingredient_map = real_engine.repository.get_product_ingredient_names(
        [r.product_id for r in first]
    )

    for result in first:
        assert result.category == "Skincare"
        assert result.price <= 50
        assert not any(
            "fragrance" in name or "parfum" in name
            for name in ingredient_map.get(result.product_id, set())
        )
