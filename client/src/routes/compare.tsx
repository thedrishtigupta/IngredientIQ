import { createFileRoute, Link } from "@tanstack/react-router";
import { ComparisonTable } from "@/components/ComparisonTable";
import { useCompare } from "@/lib/compare-store";
import { PRODUCTS, productById } from "@/lib/data";
import { emptyRequirements } from "@/lib/scoring";

export const Route = createFileRoute("/compare")({
  head: () => ({
    meta: [
      { title: "Compare products — IngredientIQ" },
      {
        name: "description",
        content:
          "Compare two or three products side by side on price, rating, popularity, functional ingredient groups, review sentiment and computed recommendation score.",
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
  const products = ids.map(productById).filter(Boolean) as typeof PRODUCTS;

  return (
    <div className="mx-auto max-w-[1220px] px-5 py-12 sm:px-8">
      <div className="flex flex-wrap items-baseline justify-between gap-4">
        <div>
          <p className="eyebrow">Comparison</p>
          <h1 className="display mt-4 text-4xl sm:text-5xl">Side by side</h1>
        </div>
        {products.length ? (
          <button type="button" onClick={clear} className="link-underline text-sm text-muted-foreground">
            Clear all
          </button>
        ) : null}
      </div>
      <p className="mt-4 max-w-xl text-sm leading-relaxed text-muted-foreground">
        Up to {max} products. Differences are marked with a thin accent underline on the strongest
        value for numeric rows only — text rows are left for you to read.
      </p>

      {products.length ? (
        <div className="mt-12">
          <ComparisonTable products={products} req={emptyRequirements} onRemove={toggle} />
        </div>
      ) : (
        <div className="mt-12 border border-dashed border-border-strong px-6 py-16 text-center">
          <p className="display text-2xl">Nothing selected yet</p>
          <p className="mx-auto mt-3 max-w-md text-sm text-muted-foreground">
            Add products from the catalog — hover any product card and choose Compare, or use the
            button on a product page.
          </p>
          <Link to="/explore" className="link-underline mt-6 inline-block text-sm">
            Browse products →
          </Link>
        </div>
      )}

      {products.length && products.length < max ? (
        <div className="mt-14">
          <p className="eyebrow">Add another</p>
          <div className="mt-4 flex flex-wrap gap-2">
            {PRODUCTS.filter((p) => !ids.includes(p.id))
              .slice(0, 8)
              .map((p) => (
                <button
                  key={p.id}
                  type="button"
                  onClick={() => toggle(p.id)}
                  className="border border-border px-3 py-2 text-xs text-muted-foreground transition-colors hover:border-foreground hover:text-foreground"
                >
                  {p.brand} · {p.name}
                </button>
              ))}
          </div>
        </div>
      ) : null}
    </div>
  );
}
