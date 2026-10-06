import math

from .config import GOAL_SUBCATEGORY_AFFINITY, HYBRID_WEIGHTS, UNLISTED_SUBCATEGORY_INTENT


def saturating_score(match_count: int, k: float = 0.15) -> float:
    """
    Convert the number of unique matching ingredients into
    a bounded score with diminishing returns.
    """
    if match_count <= 0:
        return 0.0

    return 1.0 - math.exp(-k * match_count)


def goal_curve_steepness(goal_ingredient_count: int | None) -> float:
    """
    Pick k for saturating_score from how many ingredients the goal has
    in our ingredient knowledge.

    The curve reaches about 95% when a product has all of the goal's
    ingredients, counting at most 20. A goal with a long ingredient list
    (hydration, soothing ...) therefore keeps the default k of 0.15, while a
    goal with only 5 ingredients (exfoliation) gets a steeper curve, so a
    product with 4 of them is not scored as a weak match.
    """
    if not goal_ingredient_count:
        return 0.15

    return 3.0 / min(goal_ingredient_count, 20)


def rating_score(rating) -> float:
    if rating is None:
        return 0.0

    return max(0.0, min(float(rating) / 5.0, 1.0))


def popularity_score(review_count, loves_count) -> float:
    reviews = float(review_count or 0)
    loves = float(loves_count or 0)

    raw = math.log1p(reviews) + math.log1p(loves)

    return min(raw / 25.0, 1.0)


def product_intent_score(
    subcategory: str | None,
    goals: list[str],
) -> float:
    """
    Estimate how well a product's subcategory matches
    the requested user goals.

    If no explicit affinity exists, use a neutral score.
    """
    if not subcategory or not goals:
        return 0.5

    scores = []

    for goal in goals:
        goal_map = GOAL_SUBCATEGORY_AFFINITY.get(
            goal.strip().lower()
        )

        if not goal_map:
            continue

        # Goal has a type list: a type missing from it is a poor fit.
        scores.append(goal_map.get(subcategory, UNLISTED_SUBCATEGORY_INTENT))

    if not scores:
        return 0.5

    return sum(scores) / len(scores)


def component_scores(
    match_count: int,
    rating,
    review_count,
    loves_count,
    subcategory: str | None = None,
    goals: list[str] | None = None,
    similarity: float | None = None,
    review_score: float | None = None,
    goal_ingredient_count: int | None = None,
) -> dict[str, float | None]:
    """
    Turn one product's raw numbers into the six 0..1 components.

    None means "no data": the component is left out of the final score
    (see hybrid_score). Without goals, goal / similarity / intent mean nothing,
    so they are None. The caller passes similarity=None when the vector index
    cannot score the goals, and review_score=None when the product has no reviews.
    """
    goals = goals or []

    return {
        "goal": (
            saturating_score(
                match_count,
                goal_curve_steepness(goal_ingredient_count),
            )
            if goals
            else None
        ),
        "similarity": similarity if goals else None,
        "intent": product_intent_score(subcategory, goals) if goals else None,
        "review": review_score,
        "rating": rating_score(rating),
        "popularity": popularity_score(review_count, loves_count),
    }


def hybrid_score(
    components: dict[str, float | None],
    weights: dict[str, float] = HYBRID_WEIGHTS,
) -> float:
    """
    Weighted sum of the components.

    A component that is None is dropped and the remaining weights are
    scaled up so they still add to 1. Missing data is never replaced
    by an invented value.
    """
    used = {
        name: weight
        for name, weight in weights.items()
        if components.get(name) is not None
    }

    total_weight = sum(used.values())

    if total_weight == 0:
        return 0.0

    weighted_sum = sum(
        weight * components[name]
        for name, weight in used.items()
    )

    return weighted_sum / total_weight
