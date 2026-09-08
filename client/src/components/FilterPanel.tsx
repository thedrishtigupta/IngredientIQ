import { CATEGORIES, FUNCTION_GROUPS, type Category, type FunctionGroup } from "@/lib/data";
import type { Requirements } from "@/lib/scoring";

type Props = {
  req: Requirements;
  onChange: (next: Requirements) => void;
  sort: string;
  onSortChange: (s: string) => void;
};

const toggle = <T,>(arr: T[], v: T) => (arr.includes(v) ? arr.filter((x) => x !== v) : [...arr, v]);

export function FilterPanel({ req, onChange, sort, onSortChange }: Props) {
  return (
    <div className="space-y-9">
      <section>
        <p className="eyebrow">Category</p>
        <div className="mt-3 flex flex-wrap gap-1.5">
          {CATEGORIES.map((c: Category) => (
            <button
              key={c}
              type="button"
              onClick={() => onChange({ ...req, category: req.category === c ? null : c })}
              className={`border px-3 py-1.5 text-xs transition-colors ${
                req.category === c
                  ? "border-foreground bg-foreground text-background"
                  : "border-border text-muted-foreground hover:border-foreground hover:text-foreground"
              }`}
            >
              {c}
            </button>
          ))}
        </div>
      </section>

      <section>
        <div className="flex items-baseline justify-between">
          <p className="eyebrow">Budget</p>
          <p className="numeric text-xs">{req.budget ? `$${req.budget}` : "Any"}</p>
        </div>
        <input
          type="range"
          min={15}
          max={100}
          step={1}
          value={req.budget ?? 100}
          onChange={(e) => onChange({ ...req, budget: Number(e.target.value) })}
          className="mt-3 w-full accent-[var(--color-accent)]"
        />
        <button
          type="button"
          onClick={() => onChange({ ...req, budget: null })}
          className="mt-2 text-xs text-muted-foreground link-underline"
        >
          Clear budget
        </button>
      </section>

      <section>
        <p className="eyebrow">Desired functions</p>
        <div className="mt-3 space-y-2">
          {FUNCTION_GROUPS.filter((g) => g.id !== "fragrance").map((g) => (
            <label key={g.id} className="flex cursor-pointer items-start gap-3 text-sm">
              <input
                type="checkbox"
                checked={req.functions.includes(g.id)}
                onChange={() => onChange({ ...req, functions: toggle(req.functions, g.id) })}
                className="mt-1 h-3.5 w-3.5 accent-[var(--color-accent)]"
              />
              <span>
                {g.label}
                <span className="block text-xs text-muted-foreground">{g.blurb}</span>
              </span>
            </label>
          ))}
        </div>
      </section>

      <section>
        <p className="eyebrow">Avoid</p>
        <div className="mt-3 space-y-2">
          {(["fragrance", "exfoliant", "occlusive"] as FunctionGroup[]).map((g) => (
            <label key={g} className="flex cursor-pointer items-center gap-3 text-sm">
              <input
                type="checkbox"
                checked={req.avoid.includes(g)}
                onChange={() => onChange({ ...req, avoid: toggle(req.avoid, g) })}
                className="h-3.5 w-3.5 accent-[var(--color-accent)]"
              />
              {FUNCTION_GROUPS.find((f) => f.id === g)?.label}
            </label>
          ))}
        </div>
      </section>

      <section>
        <p className="eyebrow">Sort</p>
        <select
          value={sort}
          onChange={(e) => onSortChange(e.target.value)}
          className="mt-3 w-full border border-border bg-transparent px-3 py-2 text-sm focus:border-foreground focus:outline-none"
        >
          <option value="score">Recommendation score</option>
          <option value="rating">Rating</option>
          <option value="price-asc">Price, low to high</option>
          <option value="price-desc">Price, high to low</option>
          <option value="loves">Popularity</option>
        </select>
      </section>
    </div>
  );
}
