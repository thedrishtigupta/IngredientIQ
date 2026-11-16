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

// Pinned to en-US (the dataset is US Sephora, in USD) so server and client render the same string.
const LOCALE = "en-US";
const intFmt = new Intl.NumberFormat(LOCALE, { maximumFractionDigits: 0 });
const priceFmt = new Intl.NumberFormat(LOCALE, { style: "currency", currency: "USD", minimumFractionDigits: 2 });
const wholePriceFmt = new Intl.NumberFormat(LOCALE, { style: "currency", currency: "USD", maximumFractionDigits: 0 });
const ratingFmt = new Intl.NumberFormat(LOCALE, { minimumFractionDigits: 1, maximumFractionDigits: 1 });
const pctFmt = new Intl.NumberFormat(LOCALE, { style: "percent", maximumFractionDigits: 0 });
const dateFmt = new Intl.DateTimeFormat(LOCALE, { year: "numeric", month: "short", day: "numeric", timeZone: "UTC" });
const relFmt = new Intl.RelativeTimeFormat(LOCALE, { numeric: "auto" });

export const fmtInt = (n: number) => intFmt.format(n);
export const fmtPrice = (p: number | null) => (p === null ? "—" : priceFmt.format(p));
/** A budget cap such as "$45" (whole dollars, as the slider sets them). */
export const fmtBudget = (p: number) => wholePriceFmt.format(p);
export const fmtRating = (r: number | null) => (r === null ? "—" : ratingFmt.format(r));
export const pct = (x: number) => pctFmt.format(x);

/** An ISO date ("2023-03-14") as "Mar 14, 2023"; anything unparseable comes back unchanged. */
export const fmtDate = (iso: string | null | undefined) => {
  if (!iso) return "?";
  const d = new Date(iso);
  return Number.isNaN(d.getTime()) ? iso : dateFmt.format(d);
};

/** "3 hours ago", "yesterday", ... from an ISO timestamp. */
export const fmtRelative = (iso: string, now = Date.now()) => {
  let value = (new Date(iso).getTime() - now) / 1000;
  const steps: [Intl.RelativeTimeFormatUnit, number][] = [
    ["second", 60],
    ["minute", 60],
    ["hour", 24],
    ["day", 7],
    ["week", 4.345],
    ["month", 12],
  ];
  for (const [unit, size] of steps) {
    if (Math.abs(value) < size) return relFmt.format(Math.round(value), unit);
    value /= size;
  }
  return relFmt.format(Math.round(value), "year");
};
