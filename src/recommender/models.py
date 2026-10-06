from dataclasses import dataclass, field
from typing import Optional


@dataclass
class RecommendationRequest:
    category: Optional[str] = None
    subcategory: Optional[str] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None

    goals: list[str] = field(default_factory=list)
    required_ingredients: list[str] = field(default_factory=list)
    excluded_ingredients: list[str] = field(default_factory=list)

    top_k: int = 10

@dataclass
class RecommendationExplanation:
    strengths: list[str] = field(default_factory=list)
    weaknesses: list[str] = field(default_factory=list)
    matched_goals: list[str] = field(default_factory=list)
    matched_ingredients: list[str] = field(default_factory=list)
    # Plain-English paragraph written by the LLM (or a template fallback).
    summary: Optional[str] = None

@dataclass
class RecommendationResult:
    product_id: str
    product_name: str
    brand: Optional[str]
    category: Optional[str]
    subcategory: Optional[str]

    price: Optional[float]
    rating: Optional[float]
    review_count: Optional[int]
    loves_count: Optional[int]

    score: float
    goal_match_score: float
    intent_score: float
    rating_score: float
    popularity_score: float

    matched_goals: list[str] = field(default_factory=list)
    matched_ingredients: list[str] = field(default_factory=list)

    # Hybrid signals. similarity_score: cosine(goal vector, product vector), 0..1.
    # review_score: 0..1 from product_review_signals, None if the product has no reviews.
    similarity_score: float = 0.0
    review_score: Optional[float] = None
    aspects: dict = field(default_factory=dict)  # per-aspect review sentiment

    explanation: RecommendationExplanation | None = None

    def to_dict(self) -> dict:
        return {
            "product_id": self.product_id,
            "product_name": self.product_name,
            "brand": self.brand,
            "category": self.category,
            "subcategory": self.subcategory,
            "price": self.price,
            "rating": self.rating,
            "review_count": self.review_count,
            "loves_count": self.loves_count,
            "score": self.score,
            "goal_match_score": self.goal_match_score,
            "similarity_score": self.similarity_score,
            "intent_score": self.intent_score,
            "review_score": self.review_score,
            "rating_score": self.rating_score,
            "popularity_score": self.popularity_score,
            "matched_goals": list(self.matched_goals),
            "matched_ingredients": list(self.matched_ingredients),
            "aspects": dict(self.aspects),
            "explanation": (
                {
                    "strengths": list(self.explanation.strengths),
                    "weaknesses": list(self.explanation.weaknesses),
                    "summary": self.explanation.summary,
                }
                if self.explanation
                else None
            ),
        }