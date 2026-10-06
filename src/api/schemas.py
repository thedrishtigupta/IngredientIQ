"""Request and response shapes of the API (shown in the /docs page)."""
from datetime import date
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from src.recommender.config import GOAL_LABELS


# ---------- POST /recommend ----------

class RecommendBody(BaseModel):
    goals: list[str] = Field(default=[], examples=[["hydration"]])
    category: Optional[str] = Field(default=None, examples=["Skincare"])
    subcategory: Optional[str] = None
    min_price: Optional[float] = Field(default=None, ge=0)
    max_price: Optional[float] = Field(default=None, ge=0, examples=[50])
    required_ingredients: list[str] = []
    excluded_ingredients: list[str] = Field(default=[], examples=[["fragrance"]])
    top_k: int = Field(default=10, ge=1, le=20)
    explain: bool = True  # add a short plain-English summary to every result

    @field_validator("goals")
    @classmethod
    def goals_must_be_known(cls, goals):
        goals = [g.strip().lower() for g in goals]
        unknown = [g for g in goals if g not in GOAL_LABELS]
        if unknown:
            raise ValueError(f"Unknown goals {unknown}. Valid goals: {sorted(GOAL_LABELS)}")
        return goals


class Explanation(BaseModel):
    strengths: list[str] = []
    weaknesses: list[str] = []
    summary: Optional[str] = None  # None when explain=false


class Recommendation(BaseModel):
    # extra="allow": if the engine adds a field later, it still reaches the client.
    model_config = ConfigDict(extra="allow")

    product_id: str
    product_name: str
    brand: Optional[str] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None
    price: Optional[float] = None
    rating: Optional[float] = None
    review_count: Optional[int] = None
    loves_count: Optional[int] = None

    score: float                         # final hybrid score, 0..1 (results are sorted by it)
    goal_match_score: float              # share of the goal's ingredients found in the product
    similarity_score: float              # cosine similarity: goal vector vs product vector
    intent_score: float                  # does the product type fit the goal?
    review_score: Optional[float] = None  # review sentiment, None if the product has no reviews
    rating_score: float
    popularity_score: float

    matched_goals: list[str] = []
    matched_ingredients: list[str] = []
    aspects: dict = {}                   # review sentiment per aspect, e.g. {"scent": {...}}
    explanation: Optional[Explanation] = None


class RecommendResponse(BaseModel):
    count: int
    llm_used: bool  # True only when an LLM key is set AND explain was true
    request: RecommendBody  # the request as the server understood it
    weights: dict[str, float]  # how much each score part counts (goal, similarity, intent, review, rating, popularity)
    results: list[Recommendation]


# ---------- GET /health, /goals, /categories ----------

class Health(BaseModel):
    status: str  # "ok", or "degraded" when the database is unreachable
    db: bool
    llm_enabled: bool
    products: int
    reviewed_products: int = 0  # products that have reviews (review signals exist only for these)
    reviews: int = 0  # total number of reviews


class Goal(BaseModel):
    id: str
    label: str
    supported_by_vectors: bool  # True if the vector similarity signal knows this goal


class Subcategory(BaseModel):
    name: str
    product_count: int


class Category(BaseModel):
    category: str
    product_count: int
    subcategories: list[Subcategory]


# ---------- GET /products, /products/{id}, /products/{id}/similar ----------

class ProductSummary(BaseModel):
    product_id: str
    product_name: str
    brand: Optional[str] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None
    price: Optional[float] = None
    rating: Optional[float] = None
    review_count: Optional[int] = None


class SimilarProduct(ProductSummary):
    similarity: float  # cosine similarity to the requested product, 0..1


class Ingredient(BaseModel):
    ingredient_id: int  # use it with GET /ingredients/{ingredient_id}
    position: int
    name: str
    presence_type: str  # PRIMARY or MAY_CONTAIN
    section: str  # "main", or a shade/variant name for products with several ingredient lists
    concentration: Optional[float] = None
    functional_groups: list[str] = []
    user_goals: list[str] = []


class ReviewSignals(BaseModel):
    review_count: int
    analyzed_count: int
    avg_sentiment: Optional[float] = None  # -1..1
    positive_share: Optional[float] = None
    negative_share: Optional[float] = None
    review_score: Optional[float] = None  # 0..1
    aspects: dict = {}
    method: str


class ReviewSummary(BaseModel):
    review_count: int
    average_review_rating: Optional[float] = None
    recommendation_count: Optional[int] = None
    recommendation_rate: Optional[float] = None
    average_helpfulness: Optional[float] = None
    review_text_count: int
    earliest_review_date: Optional[date] = None
    latest_review_date: Optional[date] = None


class ProductDetail(ProductSummary):
    loves_count: Optional[int] = None
    sale_price_usd: Optional[float] = None
    highlights: Optional[list[str]] = None
    variation_type: Optional[str] = None   # e.g. "Size"
    variation_value: Optional[str] = None  # e.g. "3.4 oz/ 100 mL"
    limited_edition: Optional[bool] = None
    is_new: Optional[bool] = None
    online_only: Optional[bool] = None
    out_of_stock: Optional[bool] = None
    sephora_exclusive: Optional[bool] = None

    ingredients: list[Ingredient]
    functional_profile: Optional[dict] = None  # ingredient-group counts, null if not computed
    review_signals: Optional[ReviewSignals] = None
    review_summary: Optional[ReviewSummary] = None

# ---------- GET /ingredients, /ingredients/{id} ----------

class IngredientListItem(BaseModel):
    ingredient_id: int
    name: str
    product_count: int  # in how many products it appears
    functional_groups: list[str] = []  # [] for ingredients we have no knowledge about


class RelatedIngredient(BaseModel):
    ingredient_id: int
    name: str
    product_count: int  # products that contain both ingredients


class IngredientDetail(IngredientListItem):
    user_goals: list[str] = []
    catalog_share: float  # product_count / all products, 0..1
    avg_rating: Optional[float] = None  # mean rating of the products containing it
    median_price: Optional[float] = None
    related: list[RelatedIngredient]  # most often found together with it
    products: list[ProductSummary]  # most-loved products containing it (up to 12)
