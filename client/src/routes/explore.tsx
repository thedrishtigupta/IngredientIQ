import { createFileRoute } from "@tanstack/react-router";
import { useMemo, useState } from "react";
import { SearchBar } from "@/components/SearchBar";
import { FilterPanel } from "@/components/FilterPanel";
import { ProductCard } from "@/components/ProductCard";
import { ExplanationPanel } from "@/components/RecommendationExplanation";
import { EXAMPLE_QUERIES, parseRequirements, recommend, type Requirements } from "@/lib/scoring";
import { groupLabel } from "@/lib/data";

type Search = { q?: string | undefined };

export const Route = createFileRoute("/explore")({
  validateSearch: (s: Record<string, unknown>): Search => ({
    q: typeof s["q"] === "string" ? (s["q"] as string) : undefined,
  }),
  head: () => ({
    meta: [
      { title: "Explore — IngredientIQ" },
      {
        name: "description",
        content:
          "Describe what you need in plain language, filter by category, budget, desired functions and ingredients to avoid, and see why each product ranks where it does.",
      },
      { property: "og:title", content: "Explore products — IngredientIQ" },
      {
        property: "og:description",
        content: "Ingredient-aware search with an evidence breakdown behind every recommendation.",
      },
    ],
  }),
  component: Explore,
});

function Explore() {
  const { q } = Route.useSearch();
  const [req, setReq] = useState<Requirements>(() => parseRequirements(q ?? ""));
  const [sort, setSort] = useState("score");
  const [openId, setOpenId] = useState<string | null>(null);
  const [filtersOpen, setFiltersOpen] = useState(false);

  const results = useMemo(() => {
    const r = recommend(req);
    const sorted = [...r];
    if (sort === "rating") sorted.sort((a, b) => b.product.rating - a.product.rating);
    if (sort === "price-asc") sorted.sort((a, b) => a.product.price - b.product.price);
    if (sort === "price-desc") sorted.sort((a, b) => b.product.price - a.product.price);
    if (sort === "loves") sorted.sort((a, b) => b.product.loves - a.product.loves);
    return sorted;
  }, [req, sort]);

  const open = results.find((r) => r.product.id === openId) ?? null;

  return (
    <div className="mx-auto max-w-[1220px] px-5 py-12 sm:px-8">
      <p className="eyebrow">Recommendation</p>
      <h1 className="display mt-4 max-w-2xl text-4xl sm:text-5xl">
        Describe what you need. See what the evidence supports.
      </h1>

      <div className="mt-10 max-w-3xl">
        <SearchBar
          value={req.text}
          onSubmit={(v) => setReq(parseRequirements(v, { ...req, text: v }))}
        />
        <div className="mt-4 flex flex-wrap items-center gap-x-5 gap-y-2">
          <span className="eyebrow">Try</span>
          {EXAMPLE_QUERIES.slice(0, 3).map((s) => (
            <button
              key={s}
              type="button"
              onClick={() => setReq(parseRequirements(s))}
              className="link-underline text-sm text-muted-foreground hover:text-foreground"
            >
              {s}
            </button>
          ))}
        </div>
      </div>

      {/* Parsed requirements */}
      <div className="mt-8 flex flex-wrap items-center gap-2 border-y border-border py-4">
        <span className="eyebrow mr-2">Parsed as</span>
        {req.category ? <Chip>Category · {req.category}</Chip> : null}
        {req.budget ? <Chip>Budget · ${req.budget}</Chip> : null}
        {req.functions.map((f) => (
          <Chip key={f}>Wants · {groupLabel(f)}</Chip>
        ))}
        {req.avoid.map((f) => (
          <Chip key={f}>Avoids · {groupLabel(f)}</Chip>
        ))}
        {!req.category && !req.budget && !req.functions.length && !req.avoid.length ? (
          <span className="text-sm text-muted-foreground">
            No constraints yet — results are ranked on rating, popularity and review signals only.
          </span>
        ) : null}
      </div>

      <div className="mt-10 gap-12 lg:grid lg:grid-cols-[240px_1fr]">
        <aside className="hidden lg:block">
          <FilterPanel req={req} onChange={setReq} sort={sort} onSortChange={setSort} />
        </aside>

        <div>
          <div className="mb-8 flex items-center justify-between">
            <p className="numeric text-xs text-muted-foreground">
              {results.length} products meet the hard constraints
            </p>
            <button
              type="button"
              onClick={() => setFiltersOpen(true)}
              className="border border-foreground px-4 py-2 text-xs uppercase tracking-[0.14em] lg:hidden"
            >
              Filters
            </button>
          </div>

          <div className="grid grid-cols-2 gap-x-5 gap-y-12 sm:gap-x-8 xl:grid-cols-3">
            {results.map((r, i) => (
              <div key={r.product.id}>
                <ProductCard product={r.product} index={i} />
                <div className="mt-3 flex items-center justify-between border-t border-border pt-3">
                  <span className="numeric text-xs text-muted-foreground">
                    score {r.score.toFixed(2)}
                  </span>
                  <button
                    type="button"
                    onClick={() => setOpenId(r.product.id)}
                    className="link-underline text-xs uppercase tracking-[0.12em]"
                  >
                    Why this product?
                  </button>
                </div>
              </div>
            ))}
          </div>

          {!results.length ? (
            <div className="border border-dashed border-border-strong px-6 py-16 text-center">
              <p className="display text-xl">Nothing satisfies these constraints</p>
              <p className="mt-2 text-sm text-muted-foreground">
                Relax the budget or remove an avoided group rather than accepting a weaker match.
              </p>
            </div>
          ) : null}
        </div>
      </div>

      {/* Mobile filter drawer */}
      {filtersOpen ? (
        <div className="fixed inset-0 z-50 flex items-end lg:hidden">
          <button
            type="button"
            aria-label="Close filters"
            onClick={() => setFiltersOpen(false)}
            className="absolute inset-0 bg-foreground/25"
          />
          <div className="relative max-h-[82vh] w-full overflow-y-auto border-t border-border bg-paper px-5 pb-10 pt-5 rise">
            <div className="mb-6 flex items-center justify-between">
              <p className="eyebrow">Filters</p>
              <button type="button" onClick={() => setFiltersOpen(false)} className="text-sm">
                Done
              </button>
            </div>
            <FilterPanel req={req} onChange={setReq} sort={sort} onSortChange={setSort} />
          </div>
        </div>
      ) : null}

      {open ? <ExplanationPanel result={open} req={req} onClose={() => setOpenId(null)} /> : null}
    </div>
  );
}

function Chip({ children }: { children: React.ReactNode }) {
  return (
    <span className="border border-border-strong px-2.5 py-1 text-[0.68rem] uppercase tracking-[0.1em] text-muted-foreground">
      {children}
    </span>
  );
}
