import type { RecommendBody } from "./api";

/** What the user fills in on the Explore page. `toBody` turns it into the POST /recommend body. */
export type SearchForm = {
  goals: string[];
  category: string | null;
  subcategory: string | null;
  maxPrice: number | null;
  fragranceFree: boolean;
  required: string; // comma-separated ingredient names
  excluded: string;
};

export const emptyForm: SearchForm = {
  goals: [],
  category: null,
  subcategory: null,
  maxPrice: null,
  fragranceFree: false,
  required: "",
  excluded: "",
};

const list = (s: string) =>
  s
    .split(",")
    .map((x) => x.trim())
    .filter(Boolean);

export function toBody(form: SearchForm, topK = 10): RecommendBody {
  return {
    goals: form.goals,
    category: form.category,
    subcategory: form.subcategory,
    min_price: null,
    max_price: form.maxPrice,
    required_ingredients: list(form.required),
    // "fragrance" is matched by the API like any ingredient name
    excluded_ingredients: [...new Set([...(form.fragranceFree ? ["fragrance"] : []), ...list(form.excluded)])],
    top_k: topK,
    explain: true,
  };
}

/** Example searches: buttons that fill the form (Explore) or open Explore with it filled (Home). */
export const PRESETS: { id: string; label: string; form: SearchForm }[] = [
  {
    id: "moisturizer",
    label: "Hydrating moisturizer under $50, fragrance-free",
    form: { ...emptyForm, goals: ["hydration"], category: "Skincare", subcategory: "Moisturizers", maxPrice: 50, fragranceFree: true },
  },
  {
    id: "vitamin-c",
    label: "Brightening, antioxidant skincare under $60",
    form: { ...emptyForm, goals: ["brightening", "antioxidant"], category: "Skincare", maxPrice: 60 },
  },
  {
    id: "sunscreen",
    label: "Fragrance-free sun protection under $45",
    form: { ...emptyForm, goals: ["uv_protection"], category: "Skincare", subcategory: "Sunscreen", maxPrice: 45, fragranceFree: true },
  },
  {
    id: "calming",
    label: "Soothing care that supports the skin barrier",
    form: { ...emptyForm, goals: ["soothing", "barrier_support"], category: "Skincare" },
  },
  {
    id: "hair",
    label: "Conditioning hair care",
    form: { ...emptyForm, goals: ["hair_conditioning"], category: "Hair" },
  },
];
