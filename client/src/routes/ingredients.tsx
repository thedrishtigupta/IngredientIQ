import { createFileRoute, Link } from "@tanstack/react-router";
import { useState } from "react";
import {
  FUNCTION_GROUPS,
  INGREDIENTS,
  PRODUCTS,
  groupLabel,
  productsWithIngredient,
  relatedIngredients,
} from "@/lib/data";

type Search = { i?: string | undefined };

export const Route = createFileRoute("/ingredients")({
  validateSearch: (s: Record<string, unknown>): Search => ({
    i: typeof s["i"] === "string" ? (s["i"] as string) : undefined,
  }),
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

const FIRST = INGREDIENTS[0]!;

function Ingredients() {
  const { i } = Route.useSearch();
  const [query, setQuery] = useState("");
  const [selectedName, setSelectedName] = useState(i ?? FIRST.name);

  const list = INGREDIENTS.filter((ing) =>
    ing.name.toLowerCase().includes(query.trim().toLowerCase()),
  );
  const selected = INGREDIENTS.find((x) => x.name === selectedName) ?? FIRST;
  const products = productsWithIngredient(selected.name);
  const related = relatedIngredients(selected.name);
  const frequency = products.length / PRODUCTS.length;
  const avgRating = products.length
    ? products.reduce((s, p) => s + p.rating, 0) / products.length
    : null;
  const medianPrice = products.length
    ? [...products].sort((a, b) => a.price - b.price)[Math.floor(products.length / 2)]!.price
    : null;

  return (
    <div className="mx-auto max-w-[1220px] px-5 py-12 sm:px-8">
      <p className="eyebrow">Ingredient explorer</p>
      <h1 className="display mt-4 max-w-2xl text-4xl sm:text-5xl">
        Every ingredient, read as a function.
      </h1>
      <p className="mt-4 max-w-xl text-sm leading-relaxed text-muted-foreground">
        Ingredient names are normalised and mapped to functional groups, then counted across the
        catalog. Metrics below are descriptive statistics of the products containing an ingredient —
        not claims about the ingredient itself.
      </p>

      <div className="mt-12 grid gap-12 lg:grid-cols-[300px_1fr] lg:gap-16">
        <aside>
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search ingredients"
            className="w-full border-b border-border-strong bg-transparent pb-2 text-sm focus:border-foreground focus:outline-none"
          />
          <ul className="mt-6 max-h-[520px] space-y-px overflow-y-auto pr-1">
            {list.map((ing) => (
              <li key={ing.name}>
                <button
                  type="button"
                  onClick={() => setSelectedName(ing.name)}
                  className={`flex w-full items-baseline justify-between gap-3 border-b border-border py-2.5 text-left text-sm transition-colors ${
                    ing.name === selected.name ? "text-foreground" : "text-muted-foreground hover:text-foreground"
                  }`}
                >
                  <span>{ing.name}</span>
                  <span className="numeric shrink-0 text-[0.68rem]">
                    {productsWithIngredient(ing.name).length}
                  </span>
                </button>
              </li>
            ))}
            {!list.length ? (
              <li className="py-6 text-sm text-muted-foreground">No ingredient matches that name.</li>
            ) : null}
          </ul>
        </aside>

        <section>
          <p className="eyebrow">{groupLabel(selected.group)}</p>
          <h2 className="display mt-3 text-4xl">{selected.name}</h2>
          <p className="mt-3 max-w-xl text-sm leading-relaxed text-muted-foreground">
            {selected.note} {FUNCTION_GROUPS.find((g) => g.id === selected.group)?.blurb}
          </p>

          <dl className="mt-10 grid grid-cols-2 gap-y-6 border-y border-border py-6 sm:grid-cols-4">
            <Stat label="Products" value={products.length.toString()} />
            <Stat label="Catalog frequency" value={`${Math.round(frequency * 100)}%`} />
            <Stat label="Mean rating" value={avgRating ? avgRating.toFixed(2) : "—"} />
            <Stat label="Median price" value={medianPrice ? `$${medianPrice}` : "—"} />
          </dl>

          <div className="mt-12">
            <p className="eyebrow">Appears alongside</p>
            {related.length ? (
              <ul className="mt-4 space-y-2.5">
                {related.map((r) => (
                  <li key={r.name} className="grid grid-cols-[12rem_1fr_2rem] items-center gap-3">
                    <button
                      type="button"
                      onClick={() => setSelectedName(r.name)}
                      className="link-underline truncate text-left text-sm"
                    >
                      {r.name}
                    </button>
                    <span className="h-2 w-full bg-muted">
                      <span
                        className="block h-full bg-foreground"
                        style={{ width: `${(r.coOccurrence / products.length) * 100}%` }}
                      />
                    </span>
                    <span className="numeric text-right text-xs text-muted-foreground">
                      {r.coOccurrence}
                    </span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="mt-3 text-sm text-muted-foreground">
                No co-occurring ingredients in the current slice.
              </p>
            )}
          </div>

          <div className="mt-12">
            <p className="eyebrow">Products containing {selected.name}</p>
            <ul className="mt-4 divide-y divide-border border-y border-border">
              {products.map((p) => (
                <li key={p.id} className="flex items-center gap-4 py-3">
                  <img
                    src={p.image}
                    alt={p.name}
                    width={900}
                    height={1100}
                    loading="lazy"
                    className="aspect-square w-12 object-cover"
                  />
                  <div className="min-w-0 flex-1">
                    <p className="text-[0.66rem] uppercase tracking-[0.12em] text-muted-foreground">
                      {p.brand}
                    </p>
                    <Link
                      to="/product/$productId"
                      params={{ productId: p.id }}
                      className="link-underline text-sm"
                    >
                      {p.name}
                    </Link>
                  </div>
                  <span className="numeric text-xs text-muted-foreground">
                    ${p.price} · {p.rating.toFixed(1)} ★
                  </span>
                </li>
              ))}
            </ul>
          </div>
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
