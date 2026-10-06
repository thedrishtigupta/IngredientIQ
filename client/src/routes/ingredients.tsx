import { createFileRoute, Link } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { ErrorNotice } from "@/components/ErrorNotice";
import { useIngredient, useIngredients } from "@/lib/api";
import { fmtInt, fmtPrice, fmtRating, GROUP_BLURBS, groupLabel, humanize } from "@/lib/labels";

type Search = { i?: number | undefined };

export const Route = createFileRoute("/ingredients")({
  // `i` is an ingredient id (the product page links here with it)
  validateSearch: (s: Record<string, unknown>): Search => {
    const n = Number(s["i"]);
    return { i: s["i"] !== undefined && Number.isInteger(n) ? n : undefined };
  },
  head: () => ({
    meta: [
      { title: "Ingredient Explorer — IngredientIQ" },
      {
        name: "description",
        content:
          "Search an ingredient to see its functional category, how often it appears in the catalog, the products containing it and what it commonly appears alongside.",
      },
      { property: "og:title", content: "Ingredient Explorer — IngredientIQ" },
      {
        property: "og:description",
        content: "A visual knowledge base of ingredients, functional groups and co-occurrence.",
      },
    ],
  }),
  component: Ingredients,
});

/** The value, but only after it has stopped changing for `ms` (so we do not search on every keystroke). */
function useDebounced<T>(value: T, ms: number) {
  const [v, setV] = useState(value);
  useEffect(() => {
    const t = setTimeout(() => setV(value), ms);
    return () => clearTimeout(t);
  }, [value, ms]);
  return v;
}

function Ingredients() {
  const { i } = Route.useSearch();
  const [text, setText] = useState("");
  const list = useIngredients(useDebounced(text.trim(), 300));
  const [selectedId, setSelectedId] = useState<number | null>(i ?? null);
  const activeId = selectedId ?? list.data?.[0]?.ingredient_id ?? null; // default: the most common ingredient
  const detail = useIngredient(activeId);
  const sel = detail.data;
  const groups = sel?.functional_groups ?? [];

  return (
    <div className="mx-auto max-w-[1220px] px-5 py-12 sm:px-8">
      <p className="eyebrow">Ingredient explorer</p>
      <h1 className="display mt-4 max-w-2xl text-4xl sm:text-5xl">Every ingredient, read as a function.</h1>
      <p className="mt-4 max-w-xl text-sm leading-relaxed text-muted-foreground">
        Ingredient names are normalised and, where we have curated knowledge, mapped to functional
        groups, then counted across the catalog. Metrics below are descriptive statistics of the
        products containing an ingredient — not claims about the ingredient itself.
      </p>

      <div className="mt-12 grid gap-12 lg:grid-cols-[300px_1fr] lg:gap-16">
        <aside>
          <input
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="Search ingredients"
            aria-label="Search ingredients"
            className="w-full border-b border-border-strong bg-transparent pb-2 text-sm focus:border-foreground focus:outline-none"
          />
          <ul className="mt-6 max-h-[520px] space-y-px overflow-y-auto pr-1">
            {list.data?.map((ing) => (
              <li key={ing.ingredient_id}>
                <button
                  type="button"
                  onClick={() => setSelectedId(ing.ingredient_id)}
                  className={`flex w-full items-baseline justify-between gap-3 border-b border-border py-2.5 text-left text-sm transition-colors ${
                    ing.ingredient_id === activeId
                      ? "text-foreground"
                      : "text-muted-foreground hover:text-foreground"
                  }`}
                >
                  <span>{ing.name}</span>
                  <span className="numeric shrink-0 text-[0.68rem]">{fmtInt(ing.product_count)}</span>
                </button>
              </li>
            ))}
            {list.isLoading ? <li className="py-6 text-sm text-muted-foreground">Loading…</li> : null}
            {list.data && !list.data.length ? (
              <li className="py-6 text-sm text-muted-foreground">No ingredient matches that name.</li>
            ) : null}
          </ul>
          <p className="mt-3 text-xs text-muted-foreground">Number = products containing it. Top 60 shown.</p>
        </aside>

        <section>
          {list.error || detail.error ? (
            <ErrorNotice error={list.error ?? detail.error} />
          ) : !sel ? (
            <p className="text-sm text-muted-foreground">Loading…</p>
          ) : (
            <>
              <p className="eyebrow">{groups.length ? groups.map(groupLabel).join(" · ") : "No functional group on record"}</p>
              <h2 className="display mt-3 text-4xl">{sel.name}</h2>
              <p className="mt-3 max-w-xl text-sm leading-relaxed text-muted-foreground">
                {groups.map((g) => GROUP_BLURBS[g]).filter(Boolean).join(" ") ||
                  "We have no curated function for this ingredient, so only its catalog statistics are shown."}
                {sel.user_goals.length
                  ? ` Linked to: ${sel.user_goals.map((g) => humanize(g).toLowerCase()).join(", ")}.`
                  : ""}
              </p>

              <dl className="mt-10 grid grid-cols-2 gap-y-6 border-y border-border py-6 sm:grid-cols-4">
                <Stat label="Products" value={fmtInt(sel.product_count)} />
                <Stat
                  label="Catalog frequency"
                  value={`${(sel.catalog_share * 100).toFixed(sel.catalog_share < 0.1 ? 1 : 0)}%`}
                />
                <Stat label="Mean rating" value={fmtRating(sel.avg_rating)} />
                <Stat label="Median price" value={fmtPrice(sel.median_price)} />
              </dl>

              <div className="mt-12">
                <p className="eyebrow">Appears alongside</p>
                {sel.related.length ? (
                  <ul className="mt-4 space-y-2.5">
                    {sel.related.map((r) => (
                      <li key={r.ingredient_id} className="grid grid-cols-[12rem_1fr_3rem] items-center gap-3">
                        <button
                          type="button"
                          onClick={() => setSelectedId(r.ingredient_id)}
                          className="link-underline truncate text-left text-sm"
                        >
                          {r.name}
                        </button>
                        <span className="h-2 w-full bg-muted">
                          <span
                            className="block h-full bg-foreground"
                            style={{ width: `${(r.product_count / sel.product_count) * 100}%` }}
                          />
                        </span>
                        <span className="numeric text-right text-xs text-muted-foreground">
                          {fmtInt(r.product_count)}
                        </span>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="mt-3 text-sm text-muted-foreground">No co-occurring ingredients.</p>
                )}
              </div>

              <div className="mt-12">
                <p className="eyebrow">
                  Most-loved products containing {sel.name} · {sel.products.length} of {fmtInt(sel.product_count)}
                </p>
                <ul className="mt-4 divide-y divide-border border-y border-border">
                  {sel.products.map((p) => (
                    <li key={p.product_id} className="flex items-center gap-4 py-3">
                      <div className="min-w-0 flex-1">
                        <p className="text-[0.66rem] uppercase tracking-[0.12em] text-muted-foreground">{p.brand}</p>
                        <Link
                          to="/product/$productId"
                          params={{ productId: p.product_id }}
                          className="link-underline text-sm"
                        >
                          {p.product_name}
                        </Link>
                      </div>
                      <span className="numeric text-xs text-muted-foreground">
                        {fmtPrice(p.price)} · {fmtRating(p.rating)} ★
                      </span>
                    </li>
                  ))}
                </ul>
              </div>
            </>
          )}
        </section>
      </div>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="eyebrow">{label}</dt>
      <dd className="numeric mt-1.5 text-lg">{value}</dd>
    </div>
  );
}
