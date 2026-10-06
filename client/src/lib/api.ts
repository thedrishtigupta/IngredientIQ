/**
 * The only place that talks to the IngredientIQ API (see docs/API.md in the project root).
 * Types mirror src/api/schemas.py; hooks are thin react-query wrappers around one fetch helper.
 */
import { keepPreviousData, useQueries, useQuery } from "@tanstack/react-query";

export const API_URL: string = (
  (import.meta.env["VITE_API_URL"] as string | undefined) || "http://localhost:8000"
).replace(/\/$/, "");

/** `status` is null when the API could not be reached at all (not running, wrong URL, CORS). */
export class ApiError extends Error {
  status: number | null;
  constructor(message: string, status: number | null) {
    super(message);
    this.status = status;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(API_URL + path, init);
  } catch {
    throw new ApiError(`Could not connect to ${API_URL}.`, null);
  }
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = (await res.json()) as { detail?: unknown };
      detail = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail);
    } catch {
      /* body was not JSON; keep the status text */
    }
    throw new ApiError(detail, res.status);
  }
  return (await res.json()) as T;
}

// ---------- types ----------

export type Health = {
  status: string;
  db: boolean;
  llm_enabled: boolean;
  products: number;
  reviewed_products: number;
  reviews: number;
};

export type Goal = { id: string; label: string; supported_by_vectors: boolean };

export type Category = {
  category: string;
  product_count: number;
  subcategories: { name: string; product_count: number }[];
};

export type ProductSummary = {
  product_id: string;
  product_name: string;
  brand: string | null;
  category: string | null;
  subcategory: string | null;
  price: number | null;
  rating: number | null;
  review_count: number | null;
};

export type Aspects = Record<string, { mentions: number; positive_share: number }>;

export type RecommendBody = {
  goals: string[];
  category: string | null;
  subcategory: string | null;
  min_price: number | null;
  max_price: number | null;
  required_ingredients: string[];
  excluded_ingredients: string[];
  top_k: number;
  explain: boolean;
};

export type Recommendation = ProductSummary & {
  loves_count: number | null;
  score: number;
  goal_match_score: number;
  similarity_score: number;
  intent_score: number;
  review_score: number | null; // null = no review data for this product
  rating_score: number;
  popularity_score: number;
  matched_goals: string[];
  matched_ingredients: string[];
  aspects: Aspects;
  explanation: { strengths: string[]; weaknesses: string[]; summary: string | null } | null;
};

export type RecommendResponse = {
  count: number;
  llm_used: boolean; // true: the summary text was written by a language model; false: template text
  weights: Record<string, number>; // score part -> weight (sums to 1)
  request: RecommendBody;
  results: Recommendation[];
};

export type SimilarProduct = ProductSummary & { similarity: number };

export type ProductIngredient = {
  ingredient_id: number;
  position: number;
  name: string;
  presence_type: string; // PRIMARY or MAY_CONTAIN
  section: string; // "main", or a shade/variant name
  concentration: number | null;
  functional_groups: string[];
  user_goals: string[];
};

export type ReviewSignals = {
  review_count: number;
  analyzed_count: number;
  avg_sentiment: number | null;
  positive_share: number | null;
  negative_share: number | null;
  review_score: number | null;
  aspects: Aspects;
  method: string;
};

export type ReviewSummary = {
  review_count: number;
  average_review_rating: number | null;
  recommendation_count: number | null;
  recommendation_rate: number | null;
  average_helpfulness: number | null;
  review_text_count: number;
  earliest_review_date: string | null;
  latest_review_date: string | null;
};

export type ProductDetail = ProductSummary & {
  loves_count: number | null;
  sale_price_usd: number | null;
  highlights: string[] | null;
  variation_type: string | null;
  variation_value: string | null;
  limited_edition: boolean | null;
  is_new: boolean | null;
  online_only: boolean | null;
  out_of_stock: boolean | null;
  sephora_exclusive: boolean | null;
  ingredients: ProductIngredient[];
  functional_profile: Record<string, number> | null;
  review_signals: ReviewSignals | null;
  review_summary: ReviewSummary | null;
};

export type IngredientListItem = {
  ingredient_id: number;
  name: string;
  product_count: number;
  functional_groups: string[];
};

export type IngredientDetail = IngredientListItem & {
  user_goals: string[];
  catalog_share: number;
  avg_rating: number | null;
  median_price: number | null;
  related: { ingredient_id: number; name: string; product_count: number }[];
  products: ProductSummary[];
};

/** The normal ingredient list (products with shade/variant lists have extra sections). */
export const mainIngredients = (p: ProductDetail) => p.ingredients.filter((i) => i.section === "main");

// ---------- hooks ----------

export const useHealth = () =>
  useQuery({ queryKey: ["health"], queryFn: () => request<Health>("/health") });

export const useGoals = () =>
  useQuery({ queryKey: ["goals"], queryFn: () => request<Goal[]>("/goals") });

export const useCategories = () =>
  useQuery({ queryKey: ["categories"], queryFn: () => request<Category[]>("/categories") });

/** Pass null to do nothing yet (nothing has been submitted). */
export const useRecommend = (body: RecommendBody | null) =>
  useQuery({
    queryKey: ["recommend", body],
    queryFn: () =>
      request<RecommendResponse>("/recommend", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      }),
    enabled: body !== null,
  });

export const useProducts = (q: string, limit = 20, enabled = true) =>
  useQuery({
    queryKey: ["products", q, limit],
    queryFn: () =>
      request<ProductSummary[]>(`/products?q=${encodeURIComponent(q)}&limit=${limit}`),
    enabled,
  });

const productQuery = (id: string) => ({
  queryKey: ["product", id],
  queryFn: () => request<ProductDetail>(`/products/${encodeURIComponent(id)}`),
});

export const useProduct = (id: string) => useQuery(productQuery(id));

/** One result per id, in the same order (used by the compare page). */
export const useProductsById = (ids: string[]) => useQueries({ queries: ids.map(productQuery) });

export const useSimilar = (id: string, k = 4) =>
  useQuery({
    queryKey: ["similar", id, k],
    queryFn: () => request<SimilarProduct[]>(`/products/${encodeURIComponent(id)}/similar?k=${k}`),
  });

export const useIngredients = (q: string, limit = 60) =>
  useQuery({
    queryKey: ["ingredients", q, limit],
    queryFn: () =>
      request<IngredientListItem[]>(`/ingredients?q=${encodeURIComponent(q)}&limit=${limit}`),
    placeholderData: keepPreviousData, // keep the old list on screen while typing
  });

export const useIngredient = (id: number | null) =>
  useQuery({
    queryKey: ["ingredient", id],
    queryFn: () => request<IngredientDetail>(`/ingredients/${id}`),
    enabled: id !== null,
  });
