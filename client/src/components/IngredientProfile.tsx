import { ingredientProfile, type Product } from "@/lib/data";

export function IngredientProfile({ product }: { product: Product }) {
  const rows = ingredientProfile(product);
  const mapped = rows.reduce((s, r) => s + r.count, 0);

  return (
    <div>
      <div className="flex items-baseline justify-between">
        <p className="eyebrow">Ingredient profile</p>
        <p className="numeric text-xs text-muted-foreground">
          {mapped}/{product.ingredients.length} ingredients mapped
        </p>
      </div>
      <ul className="mt-5 space-y-3.5">
        {rows.map((r) => (
          <li key={r.group} className="grid grid-cols-[9rem_1fr_2.5rem] items-center gap-3">
            <span className="text-sm">{r.label}</span>
            <span className="flex gap-[2px]" aria-hidden>
              {Array.from({ length: 10 }).map((_, i) => (
                <span
                  key={i}
                  className={`h-2.5 flex-1 ${
                    i < Math.round(r.share * 10) ? "bg-foreground" : "bg-muted"
                  }`}
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
        Each bar is the share of this product's mapped ingredients belonging to that functional
        group. It is a composition read-out, not a strength or efficacy claim.
      </p>
    </div>
  );
}
