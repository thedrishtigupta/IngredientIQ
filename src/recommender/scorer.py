import math

from .config import SCORING_WEIGHTS


def saturating_score(match_count: int, k: float = 0.15) -> float:
    """
    Convert the number of unique matching ingredients into
    a bounded score with diminishing returns.
    """
    if match_count <= 0:
        return 0.0

    return 1.0 - math.exp(-k * match_count)


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

    from .config import GOAL_SUBCATEGORY_AFFINITY

    scores = []

    for goal in goals:
        goal_map = GOAL_SUBCATEGORY_AFFINITY.get(
            goal.strip().lower()
        )

        if not goal_map:
            continue

        score = goal_map.get(subcategory)

        if score is not None:
            scores.append(score)

    if not scores:
        return 0.5

    return sum(scores) / len(scores)


def calculate_score(
    match_count: int,
    rating,
    review_count,
    loves_count,
    subcategory: str | None = None,
    goals: list[str] | None = None,
):
    goals = goals or []

    goal_component = saturating_score(match_count)
    intent_component = product_intent_score(
        subcategory,
        goals,
    )
    rating_component = rating_score(rating)
    popularity_component = popularity_score(
        review_count,
        loves_count,
    )

    final_score = (
        SCORING_WEIGHTS["goal"] * goal_component
        + SCORING_WEIGHTS["intent"] * intent_component
        + SCORING_WEIGHTS["rating"] * rating_component
        + SCORING_WEIGHTS["popularity"] * popularity_component
    )

    return (
        final_score,
        goal_component,
        intent_component,
        rating_component,
        popularity_component,
    )