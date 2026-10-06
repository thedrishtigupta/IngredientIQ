import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { ComparisonTable } from "@/components/ComparisonTable";
import { ErrorNotice } from "@/components/ErrorNotice";
import { SearchBar } from "@/components/SearchBar";
import { ApiError, useProducts, useProductsById, type ProductDetail } from "@/lib/api";
import { useCompare } from "@/lib/compare-store";

export const Route = createFileRoute("/compare")({
  head: () => ({
    meta: [
      { title: "Compare products — IngredientIQ" },
      {
        name: "description",
        content:
          "Compare two or three products side by side on price, rating, popularity, functional ingredient groups and review sentiment.",
      },
      { property: "og:title", content: "Compare products — IngredientIQ" },
      {
        property: "og:description",
        content: "A plain comparison table across ingredient, review and popularity evidence.",
      },
    ],
  }),
  component: Compare,
});

function Compare() {
  const { ids, toggle, clear, max } = useCompare();
  const fetched = useProductsById(ids); // one query per id, same order as ids
  const products = fetched.flatMap((q) => (q.data ? [q.data as ProductDetail] : []));
  const failed = ids.flatMap((id, i) => (fetched[i]?.error ? [{ id, error: fetched[i]!.error }] : []));
  const loading = fetched.some((q) => q.isLoading);

  const [search, setSearch] = useState("");
  const found = useProducts(search, 8, search !== "");

  return (
    <div className="mx-auto max-w-[1220px] px-5 py-12 sm:px-8">
      <div className="flex flex-wrap items-baseline justify-between gap-4">
        <div>
          <p className="eyebrow">Comparison</p>
          <h1 className="display mt-4 text-4xl sm:text-5xl">Side by side</h1>
        </div>
        {ids.length ? (
          <button type="button" onClick={clear} className="link-underline text-sm text-muted-foreground">
            Clear all
          </button>
        ) : null}
      </div>
      <p className="mt-4 max-w-xl text-sm leading-relaxed text-muted-foreground">
        Up to {max} products. Differences are marked with a thin accent underline on the strongest
        value for numeric rows only — text rows are left for you to read.
      </p>

      {failed.map(({ id, error }) => (
        <div key={id} className="mt-8">
          <ErrorNotice error={error} />
          <p className="mt-3 text-sm text-muted-foreground">
            {error instanceof ApiError && error.status === 404 ? `Product ${id} is not in the dataset.` : `Product ${id} could not be loaded.`}{" "}
            <button type="button" onClick={() => toggle(id)} className="link-underline text-foreground">
              Remove it from the comparison
            </button>
          </p>
        </div>
      ))}

      {products.length ? (
        <div className="mt-12">
          <ComparisonTable products={products} onRemove={toggle} />
        </div>
      ) : loading ? (
        <p className="mt-12 text-sm text-muted-foreground">Loading products…</p>
      ) : !failed.length ? (
        <div className="mt-12 border border-dashed border-border-strong px-6 py-16 text-center">
          <p className="display text-2xl">Nothing selected yet</p>
          <p className="mx-auto mt-3 max-w-md text-sm text-muted-foreground">
            Search for a product below, or hover any product card in Explore and choose Compare.
          </p>
        </div>
      ) : null}

      {ids.length < max ? (
        <div className="mt-14 max-w-xl">
          <p className="eyebrow">Add a product</p>
          <div className="mt-4">
            <SearchBar
              size="md"
              placeholder="Search by product name or brand"
              buttonLabel="Search"
              onSubmit={setSearch}
            />
          </div>
          {found.isLoading ? <p className="mt-4 text-sm text-muted-foreground">Searching…</p> : null}
          {found.error ? (
            <div className="mt-4">
              <ErrorNotice error={found.error} />
            </div>
          ) : null}
          {found.data ? (
            found.data.length ? (
              <div className="mt-4 flex flex-wrap gap-2">
                {found.data
                  .filter((p) => !ids.includes(p.product_id))
                  .map((p) => (
                    <button
                      key={p.product_id}
                      type="button"
                      onClick={() => toggle(p.product_id)}
                      className="border border-border px-3 py-2 text-xs text-muted-foreground transition-colors hover:border-foreground hover:text-foreground"
                    >
                      {p.brand} · {p.product_name}
                    </button>
                  ))}
              </div>
            ) : (
              <p className="mt-4 text-sm text-muted-foreground">No product matches “{search}”.</p>
            )
          ) : null}
        </div>
      ) : null}
    </div>
  );
}
