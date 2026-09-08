import {
  PRODUCTS,
  type Category,
  type FunctionGroup,
  type Product,
  groupsOf,
  ingredientByName,
} from "./data";

export type Requirements = {
  text: string;
  category: Category | null;
  budget: number | null;
  avoid: FunctionGroup[];
  functions: FunctionGroup[];
};

export const emptyRequirements: Requirements = {
  text: "",
  category: null,
  budget: null,
  avoid: [],
  functions: [],
};

/**
 * Deterministic keyword parse of a free-text requirement.
 * In production this step is performed by the LLM query parser in the API;
 * the parser only produces STRUCTURED FILTERS, never a product choice.
 */
export function parseRequirements(text: string, base = emptyRequirements): Requirements {
  const t = text.toLowerCase();
  const budgetMatch = t.match(/(?:under|below|less than|max|<)\s*\$?\s*(\d+)/) ?? t.match(/\$\s*(\d+)/);
  const category =
    (["Moisturizer", "Serum", "Cleanser", "Sunscreen", "Face Oil", "Exfoliator"] as Category[]).find(
      (c) => t.includes(c.toLowerCase()) || t.includes(c.toLowerCase().replace(" ", "")),
    ) ?? (t.includes("spf") ? ("Sunscreen" as Category) : null);

  const functions: FunctionGroup[] = [];
  if (/hydrat|moistur|dewy|plump/.test(t)) functions.push("humectant");
  if (/lightweight|soften|smooth|emollient/.test(t)) functions.push("emollient");
  if (/barrier|rich|occlusive|dry skin/.test(t)) functions.push("occlusive");
  if (/antioxidant|vitamin c|brighten/.test(t)) functions.push("antioxidant");
  if (/exfoliat|acid|aha|bha|texture/.test(t)) functions.push("exfoliant");
  if (/spf|sun|uv/.test(t)) functions.push("uv-filter");
  if (/calm|sooth|sensitive|redness/.test(t)) functions.push("soothing");

  const avoid: FunctionGroup[] = [];
  if (/no fragrance|without fragrance|fragrance[- ]free|unscented/.test(t)) avoid.push("fragrance");
  if (/no acid|without acid/.test(t)) avoid.push("exfoliant");

  return {
    text,
    category: category ?? base.category,
    budget: budgetMatch ? Number(budgetMatch[1]) : base.budget,
    functions: [...new Set([...base.functions, ...functions])],
    avoid: [...new Set([...base.avoid, ...avoid])],
  };
}

export const WEIGHTS = {
  ingredient: 0.32,
  review: 0.18,
  rating: 0.2,
  popularity: 0.15,
  price: 0.15,
} as const;

export type SignalKey = keyof typeof WEIGHTS;

export type Signal = {
  key: SignalKey;
  label: string;
  value: number | null;
  weight: number;
  detail: string;
};

export type ScoredProduct = {
  product: Product;
  score: number;
  signals: Signal[];
  matched: FunctionGroup[];
  avoidedHits: string[];
  excluded: boolean;
};

const MAX_LOVES = Math.max(...PRODUCTS.map((p) => p.loves));

export function scoreProduct(p: Product, req: Requirements): ScoredProduct {
  const groups = groupsOf(p);
  const matched = req.functions.filter((f) => groups.includes(f));
  const avoidedHits = p.ingredients.filter((name) => {
    const ing = ingredientByName(name);
    return ing ? req.avoid.includes(ing.group) : false;
  });

  const ingredient = req.functions.length ? matched.length / req.functions.length : null;
  const review = p.reviewAspects
    ? p.reviewAspects.reduce((s, a) => s + a.positiveShare * a.mentions, 0) /
      p.reviewAspects.reduce((s, a) => s + a.mentions, 0)
    : null;
  const rating = p.rating / 5;
  const popularity = Math.log10(p.loves) / Math.log10(MAX_LOVES);
  const price = req.budget
    ? Math.max(0, Math.min(1, 1 - Math.max(0, p.price - req.budget) / req.budget))
    : null;

  const signals: Signal[] = [
    {
      key: "ingredient",
      label: "Ingredient match",
      value: ingredient,
      weight: WEIGHTS.ingredient,
      detail: req.functions.length
        ? `${matched.length} of ${req.functions.length} requested functional groups present`
        : "No functional requirement given",
    },
    {
      key: "review",
      label: "Review match",
      value: review,
      weight: WEIGHTS.review,
      detail: p.reviewAspects
        ? `Aspect sentiment across ${p.reviewAspects.reduce((s, a) => s + a.mentions, 0).toLocaleString()} aspect mentions`
        : "No review coverage in the reviewed subset",
    },
    {
      key: "rating",
      label: "Rating",
      value: rating,
      weight: WEIGHTS.rating,
      detail: `${p.rating.toFixed(1)} of 5 from ${p.reviewCount.toLocaleString()} ratings`,
    },
    {
      key: "popularity",
      label: "Popularity",
      value: popularity,
      weight: WEIGHTS.popularity,
      detail: `${p.loves.toLocaleString()} loves, log-scaled against the catalog maximum`,
    },
    {
      key: "price",
      label: "Price match",
      value: price,
      weight: WEIGHTS.price,
      detail: req.budget
        ? p.price <= req.budget
          ? `$${p.price} is within a $${req.budget} budget`
          : `$${p.price} exceeds the $${req.budget} budget`
        : "No budget given",
    },
  ];

  // Signals without data are dropped and the remaining weights renormalised.
  const usable = signals.filter((s) => s.value !== null);
  const wSum = usable.reduce((s, x) => s + x.weight, 0);
  const score = wSum ? usable.reduce((s, x) => s + (x.value as number) * x.weight, 0) / wSum : 0;

  return {
    product: p,
    score,
    signals,
    matched,
    avoidedHits,
    excluded:
      avoidedHits.length > 0 ||
      (req.category ? p.category !== req.category : false) ||
      (req.budget ? p.price > req.budget * 1.5 : false),
  };
}

export function recommend(req: Requirements, products: Product[] = PRODUCTS) {
  return products
    .map((p) => scoreProduct(p, req))
    .filter((r) => !r.excluded)
    .sort((a, b) => b.score - a.score);
}

export const EXAMPLE_QUERIES = [
  "A lightweight moisturizer under $50 without fragrance",
  "Hydrating serum for sensitive skin, no fragrance",
  "Fragrance-free sunscreen under $45",
  "Something with antioxidants under $60",
];
