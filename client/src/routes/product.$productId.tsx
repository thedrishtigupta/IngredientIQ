import { createFileRoute, Link, notFound } from "@tanstack/react-router";
import { IngredientProfile } from "@/components/IngredientProfile";
import { ReviewInsights } from "@/components/ReviewInsights";
import { ScoreBreakdown } from "@/components/ScoreBreakdown";
import { IngredientBadge } from "@/components/IngredientBadge";
import { ProductCard } from "@/components/ProductCard";
import { useCompare } from "@/lib/compare-store";
import {
  PRODUCTS,
  groupLabel,
  groupsOf,
  ingredientByName,
  productById,
} from "@/lib/data";
import { emptyRequirements, scoreProduct } from "@/lib/scoring";

export const Route = createFileRoute("/product/$productId")({
  loader: ({ params }) => {
    const product = productById(params.productId);
    if (!product) throw notFound();
    return { product };
  },
  head: ({ loaderData }) => {
    if (!loaderData) {
      return {
        meta: [{ title: "Product unavailable — IngredientIQ" }, { name: "robots", content: "noindex" }],
      };
    }
    const { product } = loaderData;
    const title = `${product.brand} ${product.name} — IngredientIQ`;
    const description = `${product.blurb} Ingredient profile, review signals and the computed evidence behind its ranking.`;
    return {
      meta: [
        { title },
        { name: "description", content: description },
        { property: "og:title", content: title },
        { property: "og:description", content: description },
      ],
    };
  },
  component: ProductDetail,
});

function ProductDetail() {
  const { product } = Route.useLoaderData();
  const { has, toggle } = useCompare();
  const scored = scoreProduct(product, emptyRequirements);
  const groups = groupsOf(product);

  const similar = PRODUCTS.filter(
    (p) => p.id !== product.id && (p.category === product.category || groupsOf(p).some((g) => groups.includes(g))),
  ).slice(0, 4);

  return (
    <article className="mx-auto max-w-[1220px] px-5 py-10 sm:px-8">
      <nav className="text-xs text-muted-foreground">
        <Link to="/explore" className="link-underline">
          Explore
        </Link>
        <span className="mx-2">/</span>
        <span>{product.category}</span>
      </nav>

      <div className="mt-8 grid gap-12 lg:grid-cols-[1fr_1fr] lg:gap-20">
        <img
          src={product.image}
          alt={`${product.brand} ${product.name}`}
          width={900}
          height={1100}
          className="aspect-[4/5] w-full bg-muted object-cover"
        />

        <div className="lg:pt-6">
          <p className="text-[0.72rem] uppercase tracking-[0.16em] text-muted-foreground">
            {product.brand}
          </p>
          <h1 className="display mt-3 text-4xl sm:text-5xl">{product.name}</h1>
          <p className="mt-4 max-w-md text-sm leading-relaxed text-muted-foreground">
            {product.blurb}
          </p>

          <dl className="mt-8 grid grid-cols-2 gap-y-5 border-y border-border py-6 sm:grid-cols-4">
            {[
              ["Price", `$${product.price}`],
              ["Rating", `${product.rating.toFixed(1)} / 5`],
              ["Reviews", product.reviewCount.toLocaleString()],
              ["Loves", product.loves.toLocaleString()],
            ].map(([k, v]) => (
              <div key={k}>
                <dt className="eyebrow">{k}</dt>
                <dd className="numeric mt-1.5 text-lg">{v}</dd>
              </div>
            ))}
          </dl>

          <div className="mt-6 flex flex-wrap gap-1.5">
            {groups.map((g) => (
              <IngredientBadge key={g} label={groupLabel(g)} group={g} />
            ))}
          </div>

          <div className="mt-8 flex flex-wrap gap-3">
            <button
              type="button"
              onClick={() => toggle(product.id)}
              className="border border-foreground px-5 py-2.5 text-xs uppercase tracking-[0.14em] transition-colors hover:bg-foreground hover:text-background"
            >
              {has(product.id) ? "Remove from compare" : "Add to compare"}
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
          <IngredientProfile product={product} />

          <div className="mt-10">
            <p className="eyebrow">Full ingredient list</p>
            <ul className="mt-4 divide-y divide-border border-y border-border">
              {product.ingredients.map((name) => {
                const ing = ingredientByName(name);
                return (
                  <li key={name} className="flex items-start justify-between gap-6 py-3">
                    <div>
                      <Link
                        to="/ingredients"
                        search={{ i: name } as never}
                        className="link-underline text-sm"
                      >
                        {name}
                      </Link>
                      {ing ? (
                        <p className="mt-1 text-xs leading-relaxed text-muted-foreground">
                          {ing.note}
                        </p>
                      ) : null}
                    </div>
                    <span className="shrink-0 text-[0.68rem] uppercase tracking-[0.1em] text-muted-foreground">
                      {ing ? groupLabel(ing.group) : "Unmapped"}
                    </span>
                  </li>
                );
              })}
            </ul>
          </div>
        </section>

        <section className="space-y-12">
          <div>
            <p className="eyebrow">Review insights</p>
            <div className="mt-4">
              <ReviewInsights aspects={product.reviewAspects} />
            </div>
          </div>

          <div className="surface p-6 sm:p-8">
            <ScoreBreakdown signals={scored.signals} score={scored.score} />
            <p className="mt-4 text-xs leading-relaxed text-muted-foreground">
              Shown without a query: ingredient match and price match need stated requirements, so
              they are excluded here. Run a search to see them contribute.
            </p>
          </div>
        </section>
      </div>

      <section className="mt-24">
        <h2 className="display text-3xl">Similar products</h2>
        <p className="mt-2 text-sm text-muted-foreground">
          Matched on category and shared functional ingredient groups.
        </p>
        <div className="mt-10 grid grid-cols-2 gap-x-5 gap-y-12 sm:gap-x-8 lg:grid-cols-4">
          {similar.map((p, i) => (
            <ProductCard key={p.id} product={p} index={i} />
          ))}
        </div>
      </section>
    </article>
  );
}
