import product1 from "@/assets/product-1.jpg";
import product2 from "@/assets/product-2.jpg";
import product3 from "@/assets/product-3.jpg";
import product4 from "@/assets/product-4.jpg";
import product5 from "@/assets/product-5.jpg";
import product6 from "@/assets/product-6.jpg";

/**
 * DEMO DATA LAYER
 * ---------------
 * The FastAPI service (products / ingredients / recommend / research endpoints)
 * is not connected to this frontend yet. Everything below is a small, clearly
 * labelled illustrative slice used to build and review the interface.
 * Research metrics, SHAP values and statistical results are intentionally
 * ABSENT (see `researchStatus`) rather than invented.
 */
export const DATA_SOURCE_NOTE =
  "Illustrative demo slice — the full Sephora dataset (8,494 products, 119,317 reviews) is served by the project API once connected.";

export type FunctionGroup =
  | "humectant"
  | "emollient"
  | "occlusive"
  | "antioxidant"
  | "exfoliant"
  | "uv-filter"
  | "soothing"
  | "fragrance";

export const FUNCTION_GROUPS: { id: FunctionGroup; label: string; blurb: string }[] = [
  { id: "humectant", label: "Humectant", blurb: "Draws water into the upper layers of skin." },
  { id: "emollient", label: "Emollient", blurb: "Softens and smooths the skin surface." },
  { id: "occlusive", label: "Occlusive", blurb: "Slows water loss by forming a surface film." },
  { id: "antioxidant", label: "Antioxidant", blurb: "Associated with protection against oxidative stress." },
  { id: "exfoliant", label: "Exfoliant", blurb: "Loosens surface cells; acids and enzymes." },
  { id: "uv-filter", label: "UV filter", blurb: "Absorbs or reflects ultraviolet light." },
  { id: "soothing", label: "Soothing", blurb: "Commonly used in calming formulations." },
  { id: "fragrance", label: "Fragrance-related", blurb: "Perfume, essential oils and fragrance allergens." },
];

export const groupLabel = (g: FunctionGroup) =>
  FUNCTION_GROUPS.find((x) => x.id === g)?.label ?? g;

export type Ingredient = {
  name: string;
  group: FunctionGroup;
  note: string;
};

export const INGREDIENTS: Ingredient[] = [
  { name: "Glycerin", group: "humectant", note: "One of the most frequent humectants in the catalog." },
  { name: "Sodium Hyaluronate", group: "humectant", note: "Salt form of hyaluronic acid, water-binding." },
  { name: "Betaine", group: "humectant", note: "Small humectant often paired with glycerin." },
  { name: "Panthenol", group: "humectant", note: "Provitamin B5; humectant with conditioning use." },
  { name: "Squalane", group: "emollient", note: "Lightweight emollient, common in 'lightweight' claims." },
  { name: "Caprylic/Capric Triglyceride", group: "emollient", note: "Fast-spreading emollient ester." },
  { name: "Cetearyl Alcohol", group: "emollient", note: "Fatty alcohol used for texture and body." },
  { name: "Jojoba Seed Oil", group: "emollient", note: "Wax ester oil, frequent in facial oils." },
  { name: "Shea Butter", group: "occlusive", note: "Rich occlusive-emollient hybrid." },
  { name: "Dimethicone", group: "occlusive", note: "Silicone film former; slows water loss." },
  { name: "Ceramide NP", group: "occlusive", note: "Barrier lipid used in barrier-repair claims." },
  { name: "Niacinamide", group: "antioxidant", note: "Vitamin B3; very frequent multifunctional active." },
  { name: "Ascorbic Acid", group: "antioxidant", note: "Vitamin C; pH-sensitive antioxidant." },
  { name: "Tocopherol", group: "antioxidant", note: "Vitamin E; also stabilises oils." },
  { name: "Green Tea Leaf Extract", group: "antioxidant", note: "Polyphenol-rich botanical extract." },
  { name: "Glycolic Acid", group: "exfoliant", note: "Small AHA; frequent in resurfacing products." },
  { name: "Salicylic Acid", group: "exfoliant", note: "BHA associated with oily/blemish-prone claims." },
  { name: "Lactic Acid", group: "exfoliant", note: "AHA, also mildly humectant." },
  { name: "Zinc Oxide", group: "uv-filter", note: "Mineral UV filter." },
  { name: "Avobenzone", group: "uv-filter", note: "Organic UVA filter." },
  { name: "Homosalate", group: "uv-filter", note: "Organic UVB filter." },
  { name: "Centella Asiatica Extract", group: "soothing", note: "Widely used calming botanical." },
  { name: "Allantoin", group: "soothing", note: "Common soothing agent." },
  { name: "Bisabolol", group: "soothing", note: "Chamomile-derived soothing agent." },
  { name: "Fragrance (Parfum)", group: "fragrance", note: "Undisclosed fragrance blend." },
  { name: "Limonene", group: "fragrance", note: "Declared fragrance allergen." },
  { name: "Linalool", group: "fragrance", note: "Declared fragrance allergen." },
  { name: "Lavender Oil", group: "fragrance", note: "Essential oil with fragrance components." },
];

export const ingredientByName = (name: string) =>
  INGREDIENTS.find((i) => i.name.toLowerCase() === name.toLowerCase());

export type ReviewAspect = { aspect: string; positiveShare: number; mentions: number };

export type Product = {
  id: string;
  brand: string;
  name: string;
  category: Category;
  price: number;
  rating: number;
  reviewCount: number;
  loves: number;
  image: string;
  blurb: string;
  ingredients: string[];
  /** Aspect signals exist only for the ~499 products with review coverage. */
  reviewAspects: ReviewAspect[] | null;
};

export type Category =
  | "Moisturizer"
  | "Serum"
  | "Cleanser"
  | "Sunscreen"
  | "Face Oil"
  | "Exfoliator";

export const CATEGORIES: Category[] = [
  "Moisturizer",
  "Serum",
  "Cleanser",
  "Sunscreen",
  "Face Oil",
  "Exfoliator",
];

export const PRODUCTS: Product[] = [
  {
    id: "p-101",
    brand: "Maison Clair",
    name: "Weightless Hydration Cream",
    category: "Moisturizer",
    price: 38,
    rating: 4.6,
    reviewCount: 2841,
    loves: 184300,
    image: product1,
    blurb: "A gel-cream built on humectants with a light emollient phase.",
    ingredients: [
      "Glycerin",
      "Sodium Hyaluronate",
      "Betaine",
      "Squalane",
      "Caprylic/Capric Triglyceride",
      "Panthenol",
      "Allantoin",
      "Tocopherol",
    ],
    reviewAspects: [
      { aspect: "Absorption", positiveShare: 0.91, mentions: 1204 },
      { aspect: "Texture", positiveShare: 0.86, mentions: 976 },
      { aspect: "Hydration", positiveShare: 0.88, mentions: 1533 },
      { aspect: "Packaging", positiveShare: 0.62, mentions: 288 },
    ],
  },
  {
    id: "p-102",
    brand: "Objet Skin",
    name: "Barrier Repair Balm",
    category: "Moisturizer",
    price: 62,
    rating: 4.4,
    reviewCount: 1190,
    loves: 96200,
    image: product5,
    blurb: "Ceramide and shea rich balm for a heavier occlusive finish.",
    ingredients: [
      "Ceramide NP",
      "Shea Butter",
      "Dimethicone",
      "Glycerin",
      "Cetearyl Alcohol",
      "Bisabolol",
      "Tocopherol",
    ],
    reviewAspects: [
      { aspect: "Absorption", positiveShare: 0.58, mentions: 402 },
      { aspect: "Texture", positiveShare: 0.79, mentions: 611 },
      { aspect: "Hydration", positiveShare: 0.93, mentions: 720 },
    ],
  },
  {
    id: "p-103",
    brand: "Rue Neuf",
    name: "Everyday Ceramide Lotion",
    category: "Moisturizer",
    price: 29,
    rating: 4.2,
    reviewCount: 640,
    loves: 41800,
    image: product1,
    blurb: "Fragranced daily lotion with a balanced humectant/emollient split.",
    ingredients: [
      "Glycerin",
      "Ceramide NP",
      "Caprylic/Capric Triglyceride",
      "Cetearyl Alcohol",
      "Fragrance (Parfum)",
      "Limonene",
    ],
    reviewAspects: null,
  },
  {
    id: "p-104",
    brand: "Atelier Onze",
    name: "10% Niacinamide Concentrate",
    category: "Serum",
    price: 44,
    rating: 4.5,
    reviewCount: 3320,
    loves: 221400,
    image: product2,
    blurb: "High-percentage niacinamide in a fragrance-free base.",
    ingredients: ["Niacinamide", "Glycerin", "Panthenol", "Betaine", "Allantoin"],
    reviewAspects: [
      { aspect: "Absorption", positiveShare: 0.84, mentions: 1502 },
      { aspect: "Texture", positiveShare: 0.71, mentions: 1109 },
      { aspect: "Irritation", positiveShare: 0.68, mentions: 803 },
    ],
  },
  {
    id: "p-105",
    brand: "Atelier Onze",
    name: "Vitamin C Morning Serum",
    category: "Serum",
    price: 78,
    rating: 4.3,
    reviewCount: 1502,
    loves: 132900,
    image: product2,
    blurb: "Ascorbic acid with tocopherol as a stabilising partner.",
    ingredients: [
      "Ascorbic Acid",
      "Tocopherol",
      "Glycerin",
      "Green Tea Leaf Extract",
      "Squalane",
    ],
    reviewAspects: [
      { aspect: "Absorption", positiveShare: 0.74, mentions: 640 },
      { aspect: "Scent", positiveShare: 0.41, mentions: 512 },
      { aspect: "Brightening", positiveShare: 0.77, mentions: 889 },
    ],
  },
  {
    id: "p-106",
    brand: "Field & Form",
    name: "Calm Centella Serum",
    category: "Serum",
    price: 34,
    rating: 4.7,
    reviewCount: 2210,
    loves: 176500,
    image: product2,
    blurb: "Soothing-led formula with no fragrance components declared.",
    ingredients: [
      "Centella Asiatica Extract",
      "Allantoin",
      "Bisabolol",
      "Glycerin",
      "Sodium Hyaluronate",
      "Panthenol",
    ],
    reviewAspects: [
      { aspect: "Irritation", positiveShare: 0.9, mentions: 1002 },
      { aspect: "Absorption", positiveShare: 0.85, mentions: 764 },
      { aspect: "Hydration", positiveShare: 0.81, mentions: 690 },
    ],
  },
  {
    id: "p-107",
    brand: "Maison Clair",
    name: "Milky Gel Cleanser",
    category: "Cleanser",
    price: 26,
    rating: 4.4,
    reviewCount: 980,
    loves: 68400,
    image: product3,
    blurb: "Low-stripping daily cleanser with humectants retained in the base.",
    ingredients: ["Glycerin", "Betaine", "Panthenol", "Allantoin", "Squalane"],
    reviewAspects: [
      { aspect: "Tightness after use", positiveShare: 0.83, mentions: 421 },
      { aspect: "Texture", positiveShare: 0.8, mentions: 388 },
    ],
  },
  {
    id: "p-108",
    brand: "Rue Neuf",
    name: "Clarifying BHA Wash",
    category: "Cleanser",
    price: 22,
    rating: 4.0,
    reviewCount: 1440,
    loves: 52300,
    image: product3,
    blurb: "Salicylic acid wash with a light fragrance blend.",
    ingredients: ["Salicylic Acid", "Glycerin", "Fragrance (Parfum)", "Linalool", "Allantoin"],
    reviewAspects: null,
  },
  {
    id: "p-109",
    brand: "Solaire Neuf",
    name: "Mineral Daily Fluid SPF 40",
    category: "Sunscreen",
    price: 42,
    rating: 4.1,
    reviewCount: 1105,
    loves: 88700,
    image: product4,
    blurb: "Zinc-led mineral filter system, fragrance free.",
    ingredients: ["Zinc Oxide", "Squalane", "Glycerin", "Tocopherol", "Bisabolol"],
    reviewAspects: [
      { aspect: "White cast", positiveShare: 0.52, mentions: 610 },
      { aspect: "Texture", positiveShare: 0.69, mentions: 540 },
    ],
  },
  {
    id: "p-110",
    brand: "Solaire Neuf",
    name: "Invisible Screen SPF 50",
    category: "Sunscreen",
    price: 36,
    rating: 4.5,
    reviewCount: 2010,
    loves: 143200,
    image: product4,
    blurb: "Organic filter blend with a dry-touch finish.",
    ingredients: [
      "Avobenzone",
      "Homosalate",
      "Glycerin",
      "Dimethicone",
      "Fragrance (Parfum)",
    ],
    reviewAspects: [
      { aspect: "Finish", positiveShare: 0.88, mentions: 902 },
      { aspect: "Scent", positiveShare: 0.55, mentions: 431 },
    ],
  },
  {
    id: "p-111",
    brand: "Field & Form",
    name: "Restorative Night Oil",
    category: "Face Oil",
    price: 54,
    rating: 4.6,
    reviewCount: 720,
    loves: 61500,
    image: product6,
    blurb: "Jojoba-based oil with antioxidant botanicals and lavender.",
    ingredients: [
      "Jojoba Seed Oil",
      "Squalane",
      "Tocopherol",
      "Green Tea Leaf Extract",
      "Lavender Oil",
      "Limonene",
    ],
    reviewAspects: null,
  },
  {
    id: "p-112",
    brand: "Objet Skin",
    name: "Resurfacing Acid Solution",
    category: "Exfoliator",
    price: 48,
    rating: 4.2,
    reviewCount: 1680,
    loves: 119800,
    image: product2,
    blurb: "Glycolic and lactic acid blend with soothing support.",
    ingredients: [
      "Glycolic Acid",
      "Lactic Acid",
      "Centella Asiatica Extract",
      "Glycerin",
      "Panthenol",
    ],
    reviewAspects: [
      { aspect: "Irritation", positiveShare: 0.61, mentions: 704 },
      { aspect: "Texture change", positiveShare: 0.86, mentions: 812 },
    ],
  },
];

export const productById = (id: string) => PRODUCTS.find((p) => p.id === id);

export const groupsOf = (p: Product): FunctionGroup[] => {
  const set = new Set<FunctionGroup>();
  for (const name of p.ingredients) {
    const ing = ingredientByName(name);
    if (ing) set.add(ing.group);
  }
  return [...set];
};

/** Share of a product's mapped ingredients belonging to each functional group. */
export const ingredientProfile = (p: Product) => {
  const mapped = p.ingredients.map(ingredientByName).filter(Boolean) as Ingredient[];
  return FUNCTION_GROUPS.map((g) => {
    const count = mapped.filter((i) => i.group === g.id).length;
    return { group: g.id, label: g.label, count, share: mapped.length ? count / mapped.length : 0 };
  }).filter((r) => r.count > 0);
};

export const productsWithIngredient = (name: string) =>
  PRODUCTS.filter((p) => p.ingredients.some((i) => i.toLowerCase() === name.toLowerCase()));

export const relatedIngredients = (name: string) => {
  const counts = new Map<string, number>();
  for (const p of productsWithIngredient(name)) {
    for (const other of p.ingredients) {
      if (other.toLowerCase() === name.toLowerCase()) continue;
      counts.set(other, (counts.get(other) ?? 0) + 1);
    }
  }
  return [...counts.entries()]
    .sort((a, b) => b[1] - a[1])
    .slice(0, 6)
    .map(([n, c]) => ({ name: n, coOccurrence: c }));
};

/**
 * Research track results are produced offline by the modelling pipeline
 * (Model A vs Model B, SHAP). Nothing is displayed until those artefacts are
 * loaded — no placeholder numbers.
 */
export const researchStatus: {
  state: "pending" | "ready";
  modelComparison: null;
  associations: null;
  shap: null;
} = { state: "pending", modelComparison: null, associations: null, shap: null };
