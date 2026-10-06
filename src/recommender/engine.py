from .config import NEUTRAL_REVIEW_SCORE
from .filters import filter_products
from .models import RecommendationRequest, RecommendationResult
from .repository import ProductRepository
from .scorer import component_scores, hybrid_score
from .explanations import build_explanation

class RecommendationEngine:
    def __init__(self, repository=None, vector_index=None):
        self.repository = repository or ProductRepository()

        # The vector index is only needed when a request has goals.
        # If none was given, it is built the first time it is needed and kept.
        self.vector_index = vector_index

    def _get_vector_index(self):
        if self.vector_index is None:
            from .vectors import VectorIndex

            self.vector_index = VectorIndex.from_db(
                self.repository.connection
            )

        return self.vector_index

    def _get_similarities(self, goals, product_ids):
        """
        Cosine similarity between the goals and each product.

        Returns {} when there are no goals, or when the index does not
        know any of the goals. Then similarity is left out of the score.
        """
        if not goals or not product_ids:
            return {}

        vector_index = self._get_vector_index()

        if vector_index.goal_vector(goals) is None:
            return {}

        return vector_index.similarity(goals, product_ids)

    def recommend(
        self,
        request: RecommendationRequest,
    ) -> list[RecommendationResult]:

        goals = [
            goal.strip().lower()
            for goal in request.goals
            if goal and goal.strip()
        ]

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
            goals,
        )

        goal_ingredient_count = self.repository.count_goal_ingredients(goals)

        similarities = self._get_similarities(goals, filtered_ids)

        review_signals = self.repository.get_review_signals(filtered_ids)

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

            # A product with no review row has no review score (None).
            signal = review_signals.get(product_id)

            components = component_scores(
                match_count=len(matches["ingredients"]),
                rating=rating,
                review_count=review_count,
                loves_count=loves_count,
                subcategory=subcategory,
                goals=goals,
                similarity=similarities.get(product_id),
                review_score=signal["review_score"] if signal else None,
                goal_ingredient_count=goal_ingredient_count,
            )

            # A component that was not used (None) is shown as 0.0 in the
            # result, but hybrid_score() has already left it out of the score.
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
                    # No reviews -> neutral review score (see NEUTRAL_REVIEW_SCORE).
                    score=hybrid_score(
                        {**components, "review": components["review"] if components["review"] is not None else NEUTRAL_REVIEW_SCORE}
                    ),
                    intent_score=components["intent"] or 0.0,
                    goal_match_score=components["goal"] or 0.0,
                    rating_score=components["rating"],
                    popularity_score=components["popularity"],
                    matched_goals=sorted(matches["goals"]),
                    matched_ingredients=sorted(matches["ingredients"]),
                    similarity_score=components["similarity"] or 0.0,
                    review_score=components["review"],
                    aspects=signal["aspects"] if signal else {},
                )
            )

        # Best score first. Equal scores are ordered by product_id,
        # so the same request always gives the same list.
        results.sort(
            key=lambda result: (-result.score, result.product_id),
        )

        top_results = results[:request.top_k]

        for result in top_results:
            result.explanation = build_explanation(
                result,
                has_goals=bool(goals),
            )

        return top_results
