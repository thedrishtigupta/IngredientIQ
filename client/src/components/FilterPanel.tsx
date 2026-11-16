import { Spinner } from "./Skeleton";
import type { Category, Goal } from "@/lib/api";
import type { SearchForm } from "@/lib/search-form";
import { fmtBudget } from "@/lib/labels";

type Props = {
  form: SearchForm;
  onChange: (next: SearchForm) => void;
  onSubmit: () => void;
  busy: boolean;
  goals: Goal[] | undefined; // undefined while loading / failed
  categories: Category[] | undefined;
};

const toggle = <T,>(arr: T[], v: T) => (arr.includes(v) ? arr.filter((x) => x !== v) : [...arr, v]);


const input = "field mt-3";

/** The structured search form. "Find products" sends it to POST /recommend (see Explore). */
export function FilterPanel({ form, onChange, onSubmit, busy, goals, categories }: Props) {
  const subcategories =
    categories
      ?.find((c) => c.category === form.category)
      ?.subcategories.filter((s) => s.name !== "NaN") ?? []; // the dataset has a few literal "NaN" subcategories

  return (
    <form
      className="space-y-9"
      onSubmit={(e) => {
        e.preventDefault();
        onSubmit();
      }}
    >
      <fieldset>
        <legend className="eyebrow">Goals</legend>
        <div className="mt-3 flex flex-wrap gap-1.5" aria-busy={!goals}>
          {goals ? (
            goals.map((g) => (
              <button
                key={g.id}
                type="button"
                onClick={() => onChange({ ...form, goals: toggle(form.goals, g.id) })}
                aria-pressed={form.goals.includes(g.id)}
                className="chip"
              >
                {g.label}
              </button>
            ))
          ) : (
            <span className="text-xs text-muted-foreground">Loading goals…</span>
          )}
        </div>
        <p className="mt-2 text-xs text-muted-foreground">
          Pick none to rank on rating, popularity and reviews only.
        </p>
      </fieldset>

      <fieldset>
        <legend className="eyebrow">Category</legend>
        <div className="mt-3 flex flex-wrap gap-1.5" aria-busy={!categories}>
          {categories ? (
            categories.map((c) => (
              <button
                key={c.category}
                type="button"
                onClick={() =>
                  onChange({
                    ...form,
                    category: form.category === c.category ? null : c.category,
                    subcategory: null,
                  })
                }
                aria-pressed={form.category === c.category}
                className="chip"
              >
                {c.category}
              </button>
            ))
          ) : (
            <span className="text-xs text-muted-foreground">Loading categories…</span>
          )}
        </div>
        {subcategories.length ? (
          <select
            aria-label="Subcategory"
            name="subcategory"
            value={form.subcategory ?? ""}
            onChange={(e) => onChange({ ...form, subcategory: e.target.value || null })}
            className={input}
          >
            <option value="">Any subcategory</option>
            {subcategories.map((s) => (
              <option key={s.name} value={s.name}>
                {s.name} ({s.product_count})
              </option>
            ))}
          </select>
        ) : null}
      </fieldset>

      <fieldset>
        <div className="flex items-baseline justify-between">
          <legend className="eyebrow float-left">Budget</legend>
          <p className="numeric text-xs" aria-hidden="true">
            {form.maxPrice ? `Up to ${fmtBudget(form.maxPrice)}` : "Any"}
          </p>
        </div>
        <input
          type="range"
          name="max_price"
          aria-label="Maximum price"
          aria-valuetext={form.maxPrice ? `Up to ${fmtBudget(form.maxPrice)}` : "Any price"}
          min={10}
          max={200}
          step={5}
          value={form.maxPrice ?? 200}
          onChange={(e) => onChange({ ...form, maxPrice: Number(e.target.value) })}
          style={{ "--fill": `${(((form.maxPrice ?? 200) - 10) / 190) * 100}%` } as React.CSSProperties}
          className="mt-4 w-full"
        />
        <button
          type="button"
          onClick={() => onChange({ ...form, maxPrice: null })}
          className="link-underline mt-2 py-1 text-xs text-muted-foreground"
        >
          Clear budget
        </button>
      </fieldset>

      <fieldset>
        <legend className="eyebrow">Ingredients</legend>
        <label className="mt-2 flex min-h-11 cursor-pointer select-none items-center gap-3 text-sm">
          <input
            type="checkbox"
            checked={form.fragranceFree}
            onChange={() => onChange({ ...form, fragranceFree: !form.fragranceFree })}
            className="h-4 w-4 rounded accent-[var(--color-accent)]"
          />
          Fragrance-free
        </label>
        <input
          aria-label="Must contain"
          name="must_contain"
          autoComplete="off"
          spellCheck={false}
          value={form.required}
          onChange={(e) => onChange({ ...form, required: e.target.value })}
          placeholder="Must contain, e.g. niacinamide…"
          className={input}
        />
        <input
          aria-label="Must not contain"
          name="must_not_contain"
          autoComplete="off"
          spellCheck={false}
          value={form.excluded}
          onChange={(e) => onChange({ ...form, excluded: e.target.value })}
          placeholder="Must not contain, e.g. alcohol…"
          className={input}
        />
        <p className="mt-2 text-xs text-muted-foreground">Separate several names with commas.</p>
      </fieldset>

      <button
        type="submit"
        disabled={busy}
        aria-busy={busy}
        className="btn btn-primary w-full"
      >
        {busy ? <Spinner /> : null}
        {busy ? "Finding…" : "Find products"}
      </button>
    </form>
  );
}
