from .filters import filter_products
from .models import RecommendationRequest, RecommendationResult
from .repository import ProductRepository
from .scorer import calculate_score
from .explanations import build_explanation

class RecommendationEngine:
    def __init__(self, repository=None):
        self.repository = repository or ProductRepository()

    def recommend(
        self,
        request: RecommendationRequest,
    ) -> list[RecommendationResult]:

        products = self.repository.find_candidates(
            category=request.category,
            subcategory=request.subcategory,
            min_price=request.min_price,
            max_price=request.max_price,
        )

        product_ids = [product[0] for product in products]

        ingredient_map = (
            self.repository.get_product_ingredient_names(product_ids)
        )

        filtered_products = filter_products(
            products,
            request,
            ingredient_map,
        )

        filtered_ids = [product[0] for product in filtered_products]

        goal_matches = self.repository.get_goal_matches(
            filtered_ids,
            request.goals,
        )

        results = []

        for product in filtered_products:
            (
                product_id,
                product_name,
                brand,
                category,
                subcategory,
                price,
                rating,
                review_count,
                loves_count,
            ) = product

            matches = goal_matches.get(
                product_id,
                {
                    "goals": set(),
                    "ingredients": set(),
                },
            )

            score_data = calculate_score(
                match_count=len(matches["ingredients"]),
                rating=rating,
                review_count=review_count,
                loves_count=loves_count,
                subcategory=subcategory,
                goals=request.goals,
            )

            (
                final_score,
                goal_score,
                intent_score,
                rating_component,
                popularity_component,
            ) = score_data

            results.append(
                RecommendationResult(
                    product_id=product_id,
                    product_name=product_name,
                    brand=brand,
                    category=category,
                    subcategory=subcategory,
                    price=float(price) if price is not None else None,
                    rating=float(rating) if rating is not None else None,
                    review_count=review_count,
                    loves_count=loves_count,
                    score=final_score,
                    intent_score=intent_score,
                    goal_match_score=goal_score,
                    rating_score=rating_component,
                    popularity_score=popularity_component,
                    matched_goals=sorted(matches["goals"]),
                    matched_ingredients=sorted(matches["ingredients"]),
                )
            )

        results.sort(
            key=lambda result: result.score,
            reverse=True,
        )
        
        for result in results:
            result.explanation = build_explanation(result)

        return results[:request.top_k]