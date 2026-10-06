import type { Recommendation } from "@/lib/api";

/** The six parts of the hybrid score. `key` matches the weight names the API sends. */
const PARTS = [
  {
    key: "goal",
    field: "goal_match_score",
    label: "Ingredient match",
    needsGoal: true,
    hint: "Share of the goal's ingredients that the product contains.",
  },
  {
    key: "similarity",
    field: "similarity_score",
    label: "Ingredient similarity",
    needsGoal: true,
    hint: "How close the product's mix of ingredient functions is to the ideal mix for the goal.",
  },
  {
    key: "intent",
    field: "intent_score",
    label: "Product-type fit",
    needsGoal: true,
    hint: "Whether this kind of product (moisturizer, cleanser, ...) suits the goal.",
  },
  {
    key: "review",
    field: "review_score",
    label: "Review sentiment",
    needsGoal: false,
    hint: "From the review text. Only products in the reviewed subset have it.",
  },
  {
    key: "rating",
    field: "rating_score",
    label: "Rating",
    needsGoal: false,
    hint: "Average star rating.",
  },
  {
    key: "popularity",
    field: "popularity_score",
    label: "Popularity",
    needsGoal: false,
    hint: "Reviews and loves, log-scaled.",
  },
] as const;

/**
 * `compact`: just label + bar + value (for result cards).
 * Otherwise each part also shows its weight and a one-line explanation.
 * A part with no data shows "no review data" / "no goal selected" - never a made-up number.
 */
export function ScoreBreakdown({
  result,
  weights,
  hasGoals,
  compact = false,
}: {
  result: Recommendation;
  weights?: Record<string, number>;
  hasGoals: boolean;
  compact?: boolean;
}) {
  return (
    <div>
      {compact ? null : (
        <div className="flex items-baseline justify-between">
          <p className="eyebrow">Computed recommendation score</p>
          <p className="numeric text-2xl">{result.score.toFixed(2)}</p>
        </div>
      )}
      <ul className={compact ? "space-y-2" : "mt-5 space-y-4"}>
        {PARTS.map((part) => {
          const value = part.needsGoal && !hasGoals ? null : result[part.field];
          const missing = part.needsGoal ? "no goal selected" : "no review data";
          const weight = weights?.[part.key];
          return (
            <li key={part.key}>
              <div className="flex items-baseline justify-between gap-3">
                <span className={compact ? "text-xs" : "text-sm"}>{part.label}</span>
                <span className="numeric text-xs text-muted-foreground">
                  {value === null ? missing : value.toFixed(2)}
                  {!compact && weight !== undefined ? ` · w ${weight.toFixed(2)}` : ""}
                </span>
              </div>
              <div className="mt-1 h-[3px] w-full bg-muted">
                {value === null ? (
                  <div className="h-full w-full [background:repeating-linear-gradient(90deg,var(--color-border-strong)_0_4px,transparent_4px_8px)]" />
                ) : (
                  <div
                    className="h-full bg-foreground transition-[width] duration-700 ease-out"
                    style={{ width: `${Math.round(value * 100)}%` }}
                  />
                )}
              </div>
              {compact ? null : (
                <p className="mt-1.5 text-xs leading-relaxed text-muted-foreground">{part.hint}</p>
              )}
            </li>
          );
        })}
      </ul>
      {compact ? null : (
        <p className="mt-5 border-t border-border pt-3 text-xs leading-relaxed text-muted-foreground">
          Parts without data are dropped and the remaining weights are rescaled, so missing data never
          counts as a zero.
        </p>
      )}
    </div>
  );
}
