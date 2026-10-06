import { createFileRoute, Link } from "@tanstack/react-router";
import { useEffect } from "react";
import { ErrorNotice } from "@/components/ErrorNotice";
import { IngredientBadge } from "@/components/IngredientBadge";
import { IngredientProfile } from "@/components/IngredientProfile";
import { ProductCard } from "@/components/ProductCard";
import { ProductImage } from "@/components/ProductImage";
import { ReviewInsights } from "@/components/ReviewInsights";
import {
  ApiError,
  useProduct,
  useSimilar,
  type ProductDetail as Product,
  type ProductIngredient,
} from "@/lib/api";
import { useCompare } from "@/lib/compare-store";
import { fmtInt, fmtPrice, fmtRating, groupLabel, pct } from "@/lib/labels";

export const Route = createFileRoute("/product/$productId")({
  head: () => ({
    meta: [
      { title: "Product — IngredientIQ" },
      {
        name: "description",
        content:
          "Ingredient list, functional profile, review signals and similar products for one product.",
      },
    ],
  }),
  component: ProductPage,
});

const FLAGS: [keyof Product, string][] = [
  ["is_new", "New"],
  ["limited_edition", "Limited edition"],
  ["online_only", "Online only"],
  ["sephora_exclusive", "Sephora exclusive"],
  ["out_of_stock", "Out of stock"],
];

function ProductPage() {
  const { productId } = Route.useParams();
  const { data: product, error, isLoading } = useProduct(productId);

  useEffect(() => {
    if (product) document.title = `${product.brand ?? ""} ${product.product_name} — IngredientIQ`;
  }, [product]);

  if (isLoading) {
    return <p className="mx-auto max-w-[1220px] px-5 py-24 text-sm text-muted-foreground sm:px-8">Loading product…</p>;
  }
  if (error instanceof ApiError && error.status === 404) {
    return (
      <div className="mx-auto max-w-[1220px] px-5 py-24 text-center sm:px-8">
        <p className="eyebrow">404</p>
        <h1 className="display mt-3 text-4xl">Product not found</h1>
        <p className="mt-3 text-sm text-muted-foreground">
          There is no product with id <span className="numeric">{productId}</span> in the dataset.
        </p>
        <Link to="/explore" className="link-underline mt-6 inline-block text-sm">
          Back to Explore →
        </Link>
      </div>
    );
  }
  if (error || !product) {
    return (
      <div className="mx-auto max-w-[1220px] px-5 py-12 sm:px-8">
        <ErrorNotice error={error} />
      </div>
    );
  }
  return <ProductView product={product} />;
}

function ProductView({ product }: { product: Product }) {
  const { has, toggle } = useCompare();
  const similar = useSimilar(product.product_id, 4);
  const name = `${product.brand ?? ""} ${product.product_name}`.trim();

  // Ingredient lists in label order: "main" first, then shade/variant-specific lists.
  const sections = new Map<string, ProductIngredient[]>();
  for (const ing of product.ingredients) sections.set(ing.section, [...(sections.get(ing.section) ?? []), ing]);
  const main = sections.get("main") ?? [];
  const variants = [...sections.entries()].filter(([section]) => section !== "main");

  const signals = product.review_signals;
  const summary = product.review_summary;
  const flags = FLAGS.filter(([key]) => product[key] === true);

  return (
    <article className="mx-auto max-w-[1220px] px-5 py-10 sm:px-8">
      <nav className="text-xs text-muted-foreground">
        <Link to="/explore" className="link-underline">
          Explore
        </Link>
        <span className="mx-2">/</span>
        <span>{[product.category, product.subcategory].filter(Boolean).join(" · ")}</span>
      </nav>

      <div className="mt-8 grid gap-12 lg:grid-cols-[1fr_1fr] lg:gap-20">
        <ProductImage id={product.product_id} alt={name} eager className="aspect-[4/5] w-full object-cover" />

        <div className="lg:pt-6">
          <p className="text-[0.72rem] uppercase tracking-[0.16em] text-muted-foreground">{product.brand}</p>
          <h1 className="display mt-3 text-4xl sm:text-5xl">{product.product_name}</h1>
          {product.variation_value ? (
            <p className="mt-4 text-sm text-muted-foreground">
              {product.variation_type ? `${product.variation_type}: ` : ""}
              {product.variation_value}
            </p>
          ) : null}

          <dl className="mt-8 grid grid-cols-2 gap-y-5 border-y border-border py-6 sm:grid-cols-4">
            {[
              ["Price", fmtPrice(product.price) + (product.sale_price_usd ? ` · sale ${fmtPrice(product.sale_price_usd)}` : "")],
              ["Rating", `${fmtRating(product.rating)} / 5`],
              ["Reviews", fmtInt(product.review_count ?? 0)],
              ["Loves", fmtInt(product.loves_count ?? 0)],
            ].map(([k, v]) => (
              <div key={k}>
                <dt className="eyebrow">{k}</dt>
                <dd className="numeric mt-1.5 text-lg">{v}</dd>
              </div>
            ))}
          </dl>

          {flags.length || product.highlights?.length ? (
            <div className="mt-6 flex flex-wrap gap-1.5">
              {flags.map(([, label]) => (
                <IngredientBadge key={label} label={label} />
              ))}
              {product.highlights?.map((h) => (
                <IngredientBadge key={h} label={h} />
              ))}
            </div>
          ) : null}

          <div className="mt-8 flex flex-wrap gap-3">
            <button
              type="button"
              onClick={() => toggle(product.product_id)}
              className="border border-foreground px-5 py-2.5 text-xs uppercase tracking-[0.14em] transition-colors hover:bg-foreground hover:text-background"
            >
              {has(product.product_id) ? "Remove from compare" : "Add to compare"}
            </button>
            <Link
              to="/compare"
              className="border border-border px-5 py-2.5 text-xs uppercase tracking-[0.14em] text-muted-foreground transition-colors hover:border-foreground hover:text-foreground"
            >
              Open comparison
            </Link>
          </div>
        </div>
      </div>

      <div className="mt-20 grid gap-16 lg:grid-cols-[1fr_1fr] lg:gap-20">
        <section>
          <IngredientProfile profile={product.functional_profile} />

          <div className="mt-10">
            <p className="eyebrow">Full ingredient list · {main.length} in label order</p>
            <IngredientRows ingredients={main} />
            {variants.map(([section, list]) => (
              <details key={section} className="mt-6">
                <summary className="cursor-pointer text-sm text-muted-foreground">
                  Separate list for “{section}” ({list.length})
                </summary>
                <IngredientRows ingredients={list} />
              </details>
            ))}
          </div>
        </section>

        <section className="space-y-12">
          <div>
            <p className="eyebrow">Review insights</p>
            {signals ? (
              <>
                <dl className="mt-4 grid grid-cols-2 gap-y-5 border-y border-border py-5 sm:grid-cols-4">
                  {[
                    ["Review score", signals.review_score === null ? "—" : signals.review_score.toFixed(2)],
                    ["Positive", signals.positive_share === null ? "—" : pct(signals.positive_share)],
                    ["Negative", signals.negative_share === null ? "—" : pct(signals.negative_share)],
                    ["Analysed", `${fmtInt(signals.analyzed_count)} of ${fmtInt(signals.review_count)}`],
                  ].map(([k, v]) => (
                    <div key={k}>
                      <dt className="eyebrow">{k}</dt>
                      <dd className="numeric mt-1.5 text-lg">{v}</dd>
                    </div>
                  ))}
                </dl>
                <p className="mt-3 text-xs leading-relaxed text-muted-foreground">
                  Sentiment is computed from the review text ({signals.method}). Review signals exist only for the
                  reviewed subset of the catalog.
                </p>
              </>
            ) : null}
            <div className="mt-4">
              <ReviewInsights aspects={signals?.aspects ?? null} />
            </div>
          </div>

          {summary ? (
            <div>
              <p className="eyebrow">Review summary</p>
              <dl className="mt-4 grid grid-cols-2 gap-y-5 border-y border-border py-5">
                {[
                  ["Reviews", fmtInt(summary.review_count)],
                  ["Average review rating", summary.average_review_rating?.toFixed(2) ?? "—"],
                  ["Would recommend", summary.recommendation_rate === null ? "—" : pct(summary.recommendation_rate)],
                  ["Review period", `${summary.earliest_review_date ?? "?"} to ${summary.latest_review_date ?? "?"}`],
                ].map(([k, v]) => (
                  <div key={k}>
                    <dt className="eyebrow">{k}</dt>
                    <dd className="numeric mt-1.5 text-sm">{v}</dd>
                  </div>
                ))}
              </dl>
            </div>
          ) : null}
        </section>
      </div>

      <section className="mt-24">
        <h2 className="display text-3xl">Similar products</h2>
        <p className="mt-2 text-sm text-muted-foreground">
          Products with the most similar mix of ingredient functions (cosine similarity), from any category.
        </p>
        {similar.isLoading ? (
          <p className="mt-10 text-sm text-muted-foreground">Loading…</p>
        ) : similar.error ? (
          <div className="mt-10">
            <ErrorNotice error={similar.error} />
          </div>
        ) : similar.data?.length ? (
          <div className="mt-10 grid grid-cols-2 gap-x-5 gap-y-12 sm:gap-x-8 lg:grid-cols-4">
            {similar.data.map((p, i) => (
              <ProductCard key={p.product_id} product={p} index={i} tags={[`${pct(p.similarity)} similar`]} />
            ))}
          </div>
        ) : (
          <p className="mt-10 text-sm text-muted-foreground">
            This product has no ingredient vector, so no similar products can be found.
          </p>
        )}
      </section>
    </article>
  );
}

function IngredientRows({ ingredients }: { ingredients: ProductIngredient[] }) {
  return (
    <ul className="mt-4 divide-y divide-border border-y border-border">
      {ingredients.map((ing) => (
        <li key={`${ing.section}-${ing.position}`} className="flex items-start justify-between gap-6 py-3">
          <div className="flex gap-3">
            <span className="numeric w-6 shrink-0 text-right text-xs text-muted-foreground">{ing.position}</span>
            <div>
              <Link to="/ingredients" search={{ i: ing.ingredient_id }} className="link-underline text-sm">
                {ing.name}
              </Link>
              {ing.presence_type === "MAY_CONTAIN" ? (
                <p className="mt-1 text-xs text-muted-foreground">May contain</p>
              ) : null}
            </div>
          </div>
          <span className="shrink-0 text-right text-[0.68rem] uppercase tracking-[0.1em] text-muted-foreground">
            {ing.functional_groups.length ? ing.functional_groups.map(groupLabel).join(" · ") : "Unmapped"}
          </span>
        </li>
      ))}
    </ul>
  );
}
