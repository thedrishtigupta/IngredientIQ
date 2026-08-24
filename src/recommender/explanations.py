from .models import RecommendationExplanation, RecommendationResult


def build_explanation(
    result: RecommendationResult,
) -> RecommendationExplanation:
    """
    Build an evidence-backed explanation from an existing
    recommendation result.

    This function does not query the database and does not
    introduce any new product claims.
    """

    strengths: list[str] = []
    weaknesses: list[str] = []

    # ---------------------------------------------------------
    # Goal / ingredient evidence
    # ---------------------------------------------------------

    matched_ingredient_count = len(result.matched_ingredients)

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
    # Product intent evidence
    # ---------------------------------------------------------

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
    # Return structured explanation
    # ---------------------------------------------------------

    return RecommendationExplanation(
        strengths=strengths,
        weaknesses=weaknesses
    )