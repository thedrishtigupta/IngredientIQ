import type { Category, Goal } from "@/lib/api";
import type { SearchForm } from "@/lib/search-form";

type Props = {
  form: SearchForm;
  onChange: (next: SearchForm) => void;
  onSubmit: () => void;
  busy: boolean;
  goals: Goal[] | undefined; // undefined while loading / failed
  categories: Category[] | undefined;
};

const toggle = <T,>(arr: T[], v: T) => (arr.includes(v) ? arr.filter((x) => x !== v) : [...arr, v]);

const chip = (active: boolean) =>
  `border px-3 py-1.5 text-xs transition-colors ${
    active
      ? "border-foreground bg-foreground text-background"
      : "border-border text-muted-foreground hover:border-foreground hover:text-foreground"
  }`;

const input =
  "mt-3 w-full border border-border bg-transparent px-3 py-2 text-sm focus:border-foreground focus:outline-none";

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
      <section>
        <p className="eyebrow">Goals</p>
        <div className="mt-3 flex flex-wrap gap-1.5">
          {goals ? (
            goals.map((g) => (
              <button
                key={g.id}
                type="button"
                onClick={() => onChange({ ...form, goals: toggle(form.goals, g.id) })}
                aria-pressed={form.goals.includes(g.id)}
                className={chip(form.goals.includes(g.id))}
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
      </section>

      <section>
        <p className="eyebrow">Category</p>
        <div className="mt-3 flex flex-wrap gap-1.5">
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
                className={chip(form.category === c.category)}
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
      </section>

      <section>
        <div className="flex items-baseline justify-between">
          <p className="eyebrow">Budget</p>
          <p className="numeric text-xs">{form.maxPrice ? `Up to $${form.maxPrice}` : "Any"}</p>
        </div>
        <input
          type="range"
          aria-label="Maximum price"
          min={10}
          max={200}
          step={5}
          value={form.maxPrice ?? 200}
          onChange={(e) => onChange({ ...form, maxPrice: Number(e.target.value) })}
          className="mt-3 w-full accent-[var(--color-accent)]"
        />
        <button
          type="button"
          onClick={() => onChange({ ...form, maxPrice: null })}
          className="mt-2 text-xs text-muted-foreground link-underline"
        >
          Clear budget
        </button>
      </section>

      <section>
        <p className="eyebrow">Ingredients</p>
        <label className="mt-3 flex cursor-pointer items-center gap-3 text-sm">
          <input
            type="checkbox"
            checked={form.fragranceFree}
            onChange={() => onChange({ ...form, fragranceFree: !form.fragranceFree })}
            className="h-3.5 w-3.5 accent-[var(--color-accent)]"
          />
          Fragrance-free
        </label>
        <input
          aria-label="Must contain"
          value={form.required}
          onChange={(e) => onChange({ ...form, required: e.target.value })}
          placeholder="Must contain, e.g. niacinamide"
          className={input}
        />
        <input
          aria-label="Must not contain"
          value={form.excluded}
          onChange={(e) => onChange({ ...form, excluded: e.target.value })}
          placeholder="Must not contain, e.g. alcohol"
          className={input}
        />
        <p className="mt-2 text-xs text-muted-foreground">Separate several names with commas.</p>
      </section>

      <button
        type="submit"
        disabled={busy}
        className="w-full border border-foreground px-5 py-3 text-xs uppercase tracking-[0.14em] transition-colors hover:bg-foreground hover:text-background disabled:opacity-50"
      >
        {busy ? "Finding…" : "Find products"}
      </button>
    </form>
  );
}
