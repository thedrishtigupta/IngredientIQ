import { groupLabel } from "@/lib/labels";

/**
 * Functional profile from product_functional_profiles: `fg_<group>` = how many of the product's
 * ingredient occurrences belong to that functional group. (An ingredient can have several groups.)
 */
export function IngredientProfile({ profile }: { profile: Record<string, number> | null }) {
  if (!profile) {
    return (
      <div className="border border-dashed border-border-strong p-5">
        <p className="eyebrow">Ingredient profile</p>
        <p className="mt-2 text-sm text-muted-foreground">
          No functional profile has been computed for this product.
        </p>
      </div>
    );
  }

  const mapped = profile["mapped_ingredient_occurrences"] ?? 0;
  const total = profile["total_ingredient_occurrences"] ?? 0;
  const rows = Object.entries(profile)
    .filter(([key, count]) => key.startsWith("fg_") && !key.startsWith("fg_primary_") && count > 0)
    .map(([key, count]) => ({
      group: key.slice(3),
      count,
      share: mapped ? Math.min(1, count / mapped) : 0,
    }))
    .sort((a, b) => b.count - a.count)
    .slice(0, 8);

  return (
    <div>
      <div className="flex items-baseline justify-between">
        <p className="eyebrow">Ingredient profile</p>
        <p className="numeric text-xs text-muted-foreground">
          {mapped}/{total} ingredients mapped
        </p>
      </div>
      <ul className="mt-5 space-y-3.5">
        {rows.map((r) => (
          <li key={r.group} className="grid grid-cols-[9rem_1fr_2.5rem] items-center gap-3">
            <span className="text-sm">{groupLabel(r.group)}</span>
            <span className="flex gap-[2px]" aria-hidden>
              {Array.from({ length: 10 }).map((_, i) => (
                <span
                  key={i}
                  className={`h-2.5 flex-1 ${i < Math.round(r.share * 10) ? "bg-foreground" : "bg-muted"}`}
                />
              ))}
            </span>
            <span className="numeric text-right text-xs text-muted-foreground">
              {Math.round(r.share * 100)}%
            </span>
          </li>
        ))}
      </ul>
      <p className="mt-4 text-xs leading-relaxed text-muted-foreground">
        Each bar is the share of this product's mapped ingredients that belong to the functional group
        (top 8 shown). It is a composition read-out, not a strength or efficacy claim.
      </p>
    </div>
  );
}
