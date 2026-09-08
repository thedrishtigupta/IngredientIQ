import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { SearchBar } from "@/components/SearchBar";
import { ProductGrid } from "@/components/ProductGrid";
import { ScoreBreakdown } from "@/components/ScoreBreakdown";
import { EvidenceList } from "@/components/RecommendationExplanation";
import { PRODUCTS, DATA_SOURCE_NOTE } from "@/lib/data";
import { EXAMPLE_QUERIES, parseRequirements, recommend } from "@/lib/scoring";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "IngredientIQ — Find beauty products by what's inside them" },
      {
        name: "description",
        content:
          "IngredientIQ ranks beauty products from ingredient composition, review signals, rating, popularity and price — and shows the evidence behind every recommendation.",
      },
      { property: "og:title", content: "IngredientIQ — Find beauty products by what's inside them" },
      {
        property: "og:description",
        content:
          "Explainable, ingredient-aware product discovery built on a Sephora product and review dataset.",
      },
    ],
  }),
  component: Home,
});

const DEMO_QUERY = "Hydrating moisturizer under $50, no fragrance.";

const steps = [
  { n: "01", t: "Tell us what you need", d: "Plain language: category, texture, budget, anything to avoid." },
  { n: "02", t: "Requirements are parsed", d: "The query becomes structured filters — category, budget, functional groups, exclusions." },
  { n: "03", t: "Products are ranked on evidence", d: "Ingredient match, review signals, rating, popularity and price are combined into one weighted score." },
  { n: "04", t: "See exactly why it matched", d: "Every result opens into the computed signals behind its position." },
];

function Home() {
  const navigate = useNavigate();
  const go = (q: string) =>
    navigate({ to: "/explore", search: { q } as never });

  const req = parseRequirements(DEMO_QUERY);
  const demo = recommend(req)[0];
  const curated = PRODUCTS.slice(0, 8);

  return (
    <>
      {/* Hero */}
      <section className="mx-auto max-w-[1220px] px-5 pb-16 pt-14 sm:px-8 sm:pt-20">
        <div className="grid gap-10 lg:grid-cols-[1.15fr_0.85fr] lg:items-end">
          <div>
            <p className="eyebrow">Ingredient-aware discovery · non-medical</p>
            <h1 className="display mt-5 text-[2.6rem] sm:text-6xl lg:text-[4.4rem]">
              Find beauty products based on what is actually inside them.
            </h1>
          </div>
          <p className="max-w-md text-[0.95rem] leading-relaxed text-muted-foreground lg:pb-3">
            IngredientIQ reads ingredient lists as functional composition, combines that with
            review-derived signals, rating, popularity and price, and produces recommendations you
            can inspect line by line.
          </p>
        </div>

        <div className="mt-14 max-w-3xl">
          <SearchBar onSubmit={(v) => go(v || DEMO_QUERY)} />
          <div className="mt-5 flex flex-wrap items-center gap-x-5 gap-y-2">
            <span className="eyebrow">Try</span>
            {EXAMPLE_QUERIES.map((q) => (
              <button
                key={q}
                type="button"
                onClick={() => go(q)}
                className="link-underline text-sm text-muted-foreground hover:text-foreground"
              >
                {q}
              </button>
            ))}
          </div>
        </div>
      </section>

      {/* How it works */}
      <section className="border-y border-border">
        <div className="mx-auto max-w-[1220px] px-5 py-16 sm:px-8">
          <div className="flex flex-wrap items-baseline justify-between gap-4">
            <h2 className="display text-3xl">How it works</h2>
            <p className="max-w-sm text-sm text-muted-foreground">
              The ranking is computed. The language model parses your sentence and describes the
              result — it never chooses the products.
            </p>
          </div>
          <ol className="mt-12 grid gap-x-10 gap-y-10 sm:grid-cols-2 lg:grid-cols-4">
            {steps.map((s) => (
              <li key={s.n} className="rule-top pt-4">
                <span className="numeric text-xs text-accent">{s.n}</span>
                <h3 className="mt-3 text-base">{s.t}</h3>
                <p className="mt-2 text-sm leading-relaxed text-muted-foreground">{s.d}</p>
              </li>
            ))}
          </ol>
        </div>
      </section>

      {/* Explore */}
      <section className="mx-auto max-w-[1220px] px-5 py-20 sm:px-8">
        <div className="flex flex-wrap items-baseline justify-between gap-4">
          <h2 className="display text-3xl">Explore the catalog</h2>
          <Link to="/explore" className="link-underline text-sm">
            All products and filters →
          </Link>
        </div>
        <p className="mt-3 max-w-xl text-sm text-muted-foreground">{DATA_SOURCE_NOTE}</p>
        <div className="mt-12">
          <ProductGrid products={curated} />
        </div>
      </section>

      {/* Explainability */}
      {demo ? (
        <section className="border-y border-border bg-paper">
          <div className="mx-auto max-w-[1220px] px-5 py-20 sm:px-8">
            <div className="max-w-2xl">
              <p className="eyebrow">Explainability</p>
              <h2 className="display mt-4 text-3xl sm:text-4xl">
                Evidence, not a chat answer.
              </h2>
              <p className="mt-4 text-sm leading-relaxed text-muted-foreground">
                A worked example against the demo catalog. Every line below is computed from
                product data before any text is written.
              </p>
            </div>

            <div className="mt-12 grid gap-12 lg:grid-cols-[0.9fr_1.1fr]">
              <div>
                <div className="border-l-2 border-accent pl-4">
                  <p className="eyebrow">User query</p>
                  <p className="display mt-2 text-xl">“{DEMO_QUERY}”</p>
                </div>
                <div className="mt-8 flex gap-6">
                  <img
                    src={demo.product.image}
                    alt={demo.product.name}
                    width={900}
                    height={1100}
                    loading="lazy"
                    className="aspect-[4/5] w-32 shrink-0 object-cover sm:w-40"
                  />
                  <div>
                    <p className="text-[0.7rem] uppercase tracking-[0.14em] text-muted-foreground">
                      {demo.product.brand}
                    </p>
                    <h3 className="display mt-1 text-2xl">{demo.product.name}</h3>
                    <p className="numeric mt-3 text-sm">${demo.product.price}</p>
                    <p className="numeric text-xs text-muted-foreground">
                      {demo.product.rating.toFixed(1)} ★ · {demo.product.reviewCount.toLocaleString()} reviews
                    </p>
                    <Link
                      to="/product/$productId"
                      params={{ productId: demo.product.id }}
                      className="link-underline mt-4 inline-block text-sm"
                    >
                      Open product →
                    </Link>
                  </div>
                </div>
                <div className="mt-8">
                  <p className="eyebrow">Why this matches</p>
                  <div className="mt-4">
                    <EvidenceList result={demo} req={req} />
                  </div>
                </div>
              </div>

              <div className="border border-border bg-background p-6 sm:p-8">
                <ScoreBreakdown signals={demo.signals} score={demo.score} />
              </div>
            </div>
          </div>
        </section>
      ) : null}

      {/* Research teaser */}
      <section className="mx-auto max-w-[1220px] px-5 py-20 sm:px-8">
        <div className="grid gap-10 lg:grid-cols-[1fr_1fr] lg:items-end">
          <div>
            <p className="eyebrow">Research track</p>
            <h2 className="display mt-4 text-3xl sm:text-4xl">
              Do ingredients predict product success — beyond brand, category and price?
            </h2>
          </div>
          <div>
            <p className="text-sm leading-relaxed text-muted-foreground">
              A parallel study compares a baseline metadata model against the same model with
              ingredient and ingredient-combination features, and reports SHAP-based feature
              importance. All findings are associational, never causal.
            </p>
            <Link to="/research" className="link-underline mt-5 inline-block text-sm">
              Read the study →
            </Link>
          </div>
        </div>
      </section>
    </>
  );
}
