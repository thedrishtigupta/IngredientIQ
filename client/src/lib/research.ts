/**
 * Research track results, produced offline by `python scripts/run_research.py`
 * (steps 1-6 of synopsis section 2.6) and written to research-results.json.
 * This file only types that output; it never computes or invents numbers.
 */
import type { MetricRow } from "@/components/ResearchChart";
import type { ShapRow } from "@/components/SHAPChart";
import raw from "./research-results.json";

export type TargetKey = "rating" | "log_loves" | "log_reviews" | "rec_rate" | "high_performer";

export type Comparison = {
  model: string;
  cv: "random" | "unseen_brand";
  metric: string;
  a: number;
  b: number;
  gain: number;
  pCorrected: number | null;
  bWins: number;
  folds: number;
  verdict: "B better" | "A better" | "no significant difference";
};

export type Association = {
  label: string;
  kind: "ingredient" | "combination";
  effect: number;
  rawEffect: number;
  adjustedP: number;
  nWith: number;
};

export type IngredientShapRow = ShapRow & {
  group: string;
  statsQ: number | null;
  confirmed: boolean | null;
};

export type TargetResult = {
  label: string;
  task: "regression" | "classification";
  n: number;
  modelComparison: MetricRow[];
  comparisons: Comparison[];
  tests: { total: number; significantRaw: number; significantAdjusted: number; robust: number };
  associations: Association[];
  shap: (ShapRow & { group: string })[];
  ingredientShap: IngredientShapRow[];
  shapShares: Partial<
    Record<"baseline" | "ingredient" | "functional_group" | "combination", number>
  >;
};

export type ResearchResults = {
  state: "ready";
  generatedOn: string;
  dataset: {
    catalogue_products: number;
    analysis_products: number;
    ingredientFeatures: number;
    combinations: number;
    targetsAvailable: Record<TargetKey, number>;
    categories: Record<string, number>;
  };
  prespecified: {
    label: string;
    scope: string;
    target: TargetKey;
    effect: number | null;
    adjustedP: number | null;
    rawP: number | null;
  }[];
  untestable: string[];
  scopes: Record<string, Partial<Record<TargetKey, TargetResult>>>;
};

export const research = raw as unknown as ResearchResults;

export const scopeNames = Object.keys(research.scopes);

export function targetsFor(scope: string): [TargetKey, TargetResult][] {
  return Object.entries(research.scopes[scope] ?? {}) as [TargetKey, TargetResult][];
}
