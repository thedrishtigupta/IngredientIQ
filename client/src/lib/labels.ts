/** Display helpers: names for the API's ids, and number formatting. */

/** "oil_control" -> "Oil control" */
export const humanize = (s: string) => {
  const t = s.replace(/_/g, " ");
  return t.charAt(0).toUpperCase() + t.slice(1);
};

const GROUP_LABELS: Record<string, string> = {
  uv_filter: "UV filter",
  aha: "AHA",
  bha: "BHA",
  pha: "PHA",
  vitamin_b3: "Vitamin B3",
  ph_adjuster: "pH adjuster",
  fragrance_component: "Fragrance-related",
};

/** Functional group id (from ingredient_knowledge) -> label. */
export const groupLabel = (g: string) => GROUP_LABELS[g] ?? humanize(g);

/** One-line plain-English description for the common groups; others simply have none. */
export const GROUP_BLURBS: Record<string, string> = {
  humectant: "Draws water into the upper layers of skin.",
  emollient: "Softens and smooths the skin surface.",
  occlusive: "Slows water loss by forming a surface film.",
  antioxidant: "Associated with protection against oxidative stress.",
  exfoliant: "Loosens surface cells; acids and enzymes.",
  uv_filter: "Absorbs or reflects ultraviolet light.",
  fragrance_component: "Perfume, essential oils and fragrance allergens.",
  preservative: "Keeps the formula from spoiling.",
  surfactant: "Cleansing and foaming agent.",
  emulsifier: "Holds oil and water together in one formula.",
  botanical: "Plant-derived extract or oil.",
  barrier_lipid: "Skin-identical lipid used in barrier-repair claims.",
};

export const fmtInt = (n: number) => n.toLocaleString("en-US");
export const fmtPrice = (p: number | null) => (p === null ? "—" : `$${p.toFixed(2)}`);
export const fmtRating = (r: number | null) => (r === null ? "—" : r.toFixed(1));
export const pct = (x: number) => `${Math.round(x * 100)}%`;
