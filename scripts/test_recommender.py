"""
Sanity run for the hybrid recommender (needs the database).

Run from the project root:
    python -m scripts.test_recommender

It runs a few typical requests, prints the top 5 of each with every
component score, and checks that the request's filters were respected.
"""
import sys

from src.recommender import RecommendationEngine, RecommendationRequest

# Windows consoles use cp1252 by default and cannot print characters like the check mark.
sys.stdout.reconfigure(encoding="utf-8")


def sanity_requests():
    return {
        "a) hydration, Skincare, max $50": RecommendationRequest(
            category="Skincare",
            max_price=50,
            goals=["hydration"],
            top_k=5,
        ),
        "b) exfoliation": RecommendationRequest(
            goals=["exfoliation"],
            top_k=5,
        ),
        "c) hair_conditioning": RecommendationRequest(
            goals=["hair_conditioning"],
            top_k=5,
        ),
        "d) hydration, no fragrance": RecommendationRequest(
            category="Skincare",
            goals=["hydration"],
            excluded_ingredients=["fragrance"],
            top_k=5,
        ),
        "e) no goals": RecommendationRequest(
            category="Skincare",
            top_k=5,
        ),
    }


def check_filters(engine, request, results):
    """Return a list of problems (empty list = every filter was respected)."""
    problems = []

    ingredient_map = engine.repository.get_product_ingredient_names(
        [result.product_id for result in results]
    )

    for result in results:
        ingredients = ingredient_map.get(result.product_id, set())

        if request.category and result.category != request.category:
            problems.append(f"{result.product_id}: wrong category")

        if request.max_price is not None and result.price > request.max_price:
            problems.append(f"{result.product_id}: over budget")

        for name in request.required_ingredients:
            if name.lower() not in ingredients:
                problems.append(f"{result.product_id}: missing {name}")

        for name in request.excluded_ingredients:
            if any(name.lower() in ingredient for ingredient in ingredients):
                problems.append(f"{result.product_id}: contains {name}")

    return problems


def show_result(index, result):
    review = (
        f"{result.review_score:.3f}"
        if result.review_score is not None
        else "none"
    )

    print(f"{index}. {result.product_name} ({result.brand})")
    print(
        f"   {result.category} / {result.subcategory}"
        f" | ${result.price} | rating {result.rating}"
    )
    print(f"   Score: {result.score:.4f}")
    print(
        f"   goal {result.goal_match_score:.3f}"
        f" | similarity {result.similarity_score:.3f}"
        f" | intent {result.intent_score:.3f}"
        f" | review {review}"
        f" | rating {result.rating_score:.3f}"
        f" | popularity {result.popularity_score:.3f}"
    )
    print(
        f"   Matched ingredients ({len(result.matched_ingredients)}): "
        f"{result.matched_ingredients}"
    )

    if result.explanation:
        for reason in result.explanation.strengths:
            print(f"   ✓ {reason}")

        for reason in result.explanation.weaknesses:
            print(f"   ! {reason}")

    print()


def main():
    engine = RecommendationEngine()

    try:
        for title, request in sanity_requests().items():
            results = engine.recommend(request)

            print(f"\n=== {title}: {len(results)} results ===\n")

            for index, result in enumerate(results, start=1):
                show_result(index, result)

            problems = check_filters(engine, request, results)
            print("Filters respected:", "yes" if not problems else problems)

    finally:
        engine.repository.close()


if __name__ == "__main__":
    main()
