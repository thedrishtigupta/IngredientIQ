from src.recommender import RecommendationEngine, RecommendationRequest

def main():
    request = RecommendationRequest(
        category="Skincare",
        max_price=50,
        goals=["hydration"],
        top_k=10,
    )

    engine = RecommendationEngine()

    try:
        results = engine.recommend(request)

        print(f"\nFound {len(results)} recommendations:\n")

        for index, result in enumerate(results, start=1):
            print(f"{index}. {result.product_name}")
            print(f"   Product ID: {result.product_id}")
            print(f"   Brand: {result.brand}")
            print(f"   Price: ${result.price}")
            print(f"   Rating: {result.rating}")
            print(f"   Score: {result.score:.4f}")
            print(f"   Goal score: {result.goal_match_score:.4f}")
            print(f"   Intent score: {result.intent_score:.4f}")
            print(f"   Rating score: {result.rating_score:.4f}")
            print(f"   Popularity score: {result.popularity_score:.4f}")
            print(f"   Matched goals: {result.matched_goals}")
            print(
                f"   Matched ingredients ({len(result.matched_ingredients)}): "
                f"{result.matched_ingredients}"
            )
            if result.explanation:
                print("   Strengths:")
                for reason in result.explanation.strengths:
                    print(f"   ✓ {reason}")

                if result.explanation.weaknesses:
                    print("   Weaknesses:")
                    for reason in result.explanation.weaknesses:
                        print(f"   ! {reason}")
            print()

    finally:
        engine.repository.close()


if __name__ == "__main__":
    main()
    