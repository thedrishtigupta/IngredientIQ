from .config import MIN_ASPECT_MENTIONS, UNRELIABLE_ASPECTS
from .models import RecommendationExplanation, RecommendationResult


def best_and_worst_aspect(aspects: dict):
    """
    Pick the review aspect people like most and the one they like least.

    aspects looks like {"hydration": {"mentions": 120, "positive_share": 0.91}}.
    Aspects with too few mentions are ignored. Returns
    ((name, data), (name, data)), or None if no aspect is usable.
    """
    usable = [
        (name, data)
        for name, data in aspects.items()
        if name not in UNRELIABLE_ASPECTS
        and data.get("mentions", 0) >= MIN_ASPECT_MENTIONS
        and data.get("positive_share") is not None
    ]

    if not usable:
        return None

    # Sorting by (share, name) makes ties come out the same every time.
    usable.sort(key=lambda item: (item[1]["positive_share"], item[0]))

    return usable[-1], usable[0]


def build_explanation(
    result: RecommendationResult,
    has_goals: bool = True,
) -> RecommendationExplanation:
    """
    Build an evidence-backed explanation from an existing
    recommendation result.

    This function does not query the database and does not
    introduce any new product claims.

    has_goals=False means the request had no goals, so the
    goal / similarity / intent evidence is skipped.
    """

    strengths: list[str] = []
    weaknesses: list[str] = []

    # ---------------------------------------------------------
    # Goal / ingredient evidence
    # ---------------------------------------------------------

    matched_ingredient_count = len(result.matched_ingredients)

    if has_goals:
        if result.goal_match_score >= 0.75:
            strengths.append(
                f"Strong match for the requested goal "
                f"(goal score: {result.goal_match_score:.2f}). "
                f"{matched_ingredient_count} matching ingredients."
            )
        elif result.goal_match_score >= 0.50:
            strengths.append(
                f"Moderate match for the requested goal "
                f"(goal score: {result.goal_match_score:.2f}). "
                f"{matched_ingredient_count} matching ingredients."
            )
        else:
            weaknesses.append(
                f"Limited ingredient evidence for the requested goal "
                f"({matched_ingredient_count} matching ingredients)."
            )

    # ---------------------------------------------------------
    # Vector similarity evidence
    # ---------------------------------------------------------
    # 0.0 means "no similarity signal" (no goals, or the goal is unknown
    # to the vector index), so we say nothing in that case.
    # Cosine values are small in practice (the best hydration products are
    # about 0.6, the best exfoliants about 0.3), so the cut-offs are low.

    if has_goals and result.similarity_score > 0:
        if result.similarity_score >= 0.50:
            strengths.append(
                f"Its ingredient mix is a good fit for the goal "
                f"(similarity: {result.similarity_score:.2f})."
            )
        elif result.similarity_score < 0.10:
            weaknesses.append(
                f"Its ingredient mix is only weakly similar to the ideal "
                f"mix for the goal (similarity: {result.similarity_score:.2f})."
            )

    # ---------------------------------------------------------
    # Product intent evidence
    # ---------------------------------------------------------

    if has_goals:
        if result.intent_score >= 0.90:
            strengths.append(
                f"The product type strongly matches the requested goal "
                f"({result.subcategory}, intent score: {result.intent_score:.2f})."
            )
        elif result.intent_score >= 0.70:
            strengths.append(
                f"The product type is reasonably aligned with the requested goal "
                f"({result.subcategory}, intent score: {result.intent_score:.2f})."
            )
        elif result.intent_score < 0.50:
            weaknesses.append(
                f"The product type is less aligned with the requested goal "
                f"({result.subcategory})."
            )

    # ---------------------------------------------------------
    # Rating evidence
    # ---------------------------------------------------------

    if result.rating is not None:
        if result.rating >= 4.5:
            strengths.append(
                f"Highly rated at {result.rating:.2f}/5."
            )
        elif result.rating >= 4.0:
            strengths.append(
                f"Well rated at {result.rating:.2f}/5."
            )
        elif result.rating < 3.5:
            weaknesses.append(
                f"Lower rating of {result.rating:.2f}/5."
            )

    # ---------------------------------------------------------
    # Popularity evidence
    # ---------------------------------------------------------

    if result.popularity_score >= 0.75:
        strengths.append("Strong popularity signal.")
    elif result.popularity_score < 0.30:
        weaknesses.append("Limited popularity signal.")

    # ---------------------------------------------------------
    # Review sentiment evidence
    # ---------------------------------------------------------
    # Only when the product has a review score. No score, no claim.
    # Review scores are high for almost every product (half are above 0.84,
    # nine in ten above 0.77), so the cut-offs are high too.

    if result.review_score is not None:
        if result.review_score >= 0.88:
            strengths.append(
                f"Reviewers are very positive "
                f"(review score: {result.review_score:.2f})."
            )
        elif result.review_score >= 0.80:
            strengths.append(
                f"Reviewers are mostly positive "
                f"(review score: {result.review_score:.2f})."
            )
        elif result.review_score < 0.75:
            weaknesses.append(
                f"Reviewers are less positive than for most products "
                f"(review score: {result.review_score:.2f})."
            )

        aspect_pair = best_and_worst_aspect(result.aspects)

        if aspect_pair:
            (best_name, best), (worst_name, worst) = aspect_pair

            if best["positive_share"] >= 0.80:
                strengths.append(
                    f"Reviews that mention {best_name} are "
                    f"{best['positive_share']:.0%} positive "
                    f"({best['mentions']} mentions)."
                )

            if worst_name != best_name and worst["positive_share"] < 0.50:
                weaknesses.append(
                    f"Reviews that mention {worst_name} are only "
                    f"{worst['positive_share']:.0%} positive "
                    f"({worst['mentions']} mentions)."
                )

    # ---------------------------------------------------------
    # Return structured explanation
    # ---------------------------------------------------------

    return RecommendationExplanation(
        strengths=strengths,
        weaknesses=weaknesses
    )