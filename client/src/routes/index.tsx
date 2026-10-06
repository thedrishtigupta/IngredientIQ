import { createFileRoute, Link } from "@tanstack/react-router";
import { DataNote } from "@/components/DataNote";
import { ErrorNotice } from "@/components/ErrorNotice";
import { EvidenceList, SummaryNote } from "@/components/RecommendationExplanation";
import { ProductGrid } from "@/components/ProductGrid";
import { ProductImage } from "@/components/ProductImage";
import { ScoreBreakdown } from "@/components/ScoreBreakdown";
import { useHealth, useProducts, useRecommend } from "@/lib/api";
import { fmtInt, fmtPrice, fmtRating } from "@/lib/labels";
import { PRESETS, toBody } from "@/lib/search-form";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "IngredientIQ — Find beauty products by what's inside them" },
      {
        name: "description",
        content:
          "IngredientIQ ranks beauty products from ingredient composition, review signals, rating and popularity — and shows the evidence behind every recommendation.",
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

// The first example doubles as the live worked example further down the page.
const WORKED_EXAMPLE = PRESETS[0]!;

const steps = [
  { n: "01", t: "Pick what you need", d: "Choose goals such as hydration or brightening, then a category, a budget and ingredients to include or avoid." },
  { n: "02", t: "Products are filtered", d: "Anything outside your category, budget or ingredient rules is removed before scoring." },
  { n: "03", t: "Products are ranked on evidence", d: "Ingredient match, ingredient similarity, product-type fit, review sentiment, rating and popularity are combined into one weighted score." },
  { n: "04", t: "See exactly why it matched", d: "Every result opens into the computed scores, matched ingredients and review aspects behind its position." },
];

function Home() {
  const health = useHealth().data;
  const loved = useProducts("", 8);
  const example = useRecommend(toBody(WORKED_EXAMPLE.form, 1));
  const top = example.data?.results[0];

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
            review-derived signals, rating and popularity, and produces recommendations you can
            inspect line by line.
          </p>
        </div>

        <div className="mt-14 max-w-3xl">
          <Link
            to="/explore"
            className="inline-block border border-foreground px-6 py-3 text-xs uppercase tracking-[0.14em] transition-colors hover:bg-foreground hover:text-background"
          >
            Find products
          </Link>
          <div className="mt-6 flex flex-wrap items-center gap-x-5 gap-y-2">
            <span className="eyebrow">Try</span>
            {PRESETS.map((p) => (
              <Link
                key={p.id}
                to="/explore"
                search={{ preset: p.id }}
                className="link-underline text-sm text-muted-foreground hover:text-foreground"
              >
                {p.label}
              </Link>
            ))}
          </div>
        </div>

        <dl className="mt-16 grid max-w-3xl grid-cols-3 gap-6 border-y border-border py-6">
          {[
            ["Products", health?.products],
            ["Reviews", health?.reviews],
            ["Products with reviews", health?.reviewed_products],
          ].map(([label, value]) => (
            <div key={label as string}>
              <dt className="eyebrow">{label}</dt>
              <dd className="numeric mt-1.5 text-xl sm:text-2xl">{typeof value === "number" ? fmtInt(value) : "—"}</dd>
            </div>
          ))}
        </dl>
        <p className="mt-3 max-w-3xl text-xs leading-relaxed text-muted-foreground">
          <DataNote />
        </p>
      </section>

      {/* How it works */}
      <section className="border-y border-border">
        <div className="mx-auto max-w-[1220px] px-5 py-16 sm:px-8">
          <div className="flex flex-wrap items-baseline justify-between gap-4">
            <h2 className="display text-3xl">How it works</h2>
            <p className="max-w-sm text-sm text-muted-foreground">
              The ranking is computed. A language model, when configured, only words the
              explanation — it never chooses the products.
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
          <h2 className="display text-3xl">Most-loved products</h2>
          <Link to="/explore" className="link-underline text-sm">
            Search with goals and filters →
          </Link>
        </div>
        <p className="mt-3 max-w-xl text-sm text-muted-foreground">
          The most-loved products in the catalog, regardless of goal. Product photos are
          placeholders: the dataset has none.
        </p>
        <div className="mt-12">
          {loved.error ? (
            <ErrorNotice error={loved.error} />
          ) : loved.data ? (
            <ProductGrid products={loved.data} />
          ) : (
            <p className="text-sm text-muted-foreground">Loading…</p>
          )}
        </div>
      </section>

      {/* Explainability */}
      <section className="border-y border-border bg-paper">
        <div className="mx-auto max-w-[1220px] px-5 py-20 sm:px-8">
          <div className="max-w-2xl">
            <p className="eyebrow">Explainability</p>
            <h2 className="display mt-4 text-3xl sm:text-4xl">Evidence, not a chat answer.</h2>
            <p className="mt-4 text-sm leading-relaxed text-muted-foreground">
              A live worked example: the top result of a real search. Every score below is computed
              from product data before any text is written.
            </p>
          </div>

          {example.error ? (
            <div className="mt-12">
              <ErrorNotice error={example.error} />
            </div>
          ) : top && example.data ? (
            <div className="mt-12 grid gap-12 lg:grid-cols-[0.9fr_1.1fr]">
              <div>
                <div className="border-l-2 border-accent pl-4">
                  <p className="eyebrow">Search</p>
                  <p className="display mt-2 text-xl">“{WORKED_EXAMPLE.label}”</p>
                </div>
                <div className="mt-8 flex gap-6">
                  <div className="w-32 shrink-0 sm:w-40">
                    <ProductImage id={top.product_id} alt={top.product_name} />
                  </div>
                  <div>
                    <p className="text-[0.7rem] uppercase tracking-[0.14em] text-muted-foreground">{top.brand}</p>
                    <h3 className="display mt-1 text-2xl">{top.product_name}</h3>
                    <p className="numeric mt-3 text-sm">{fmtPrice(top.price)}</p>
                    <p className="numeric text-xs text-muted-foreground">
                      {fmtRating(top.rating)} ★ · {fmtInt(top.review_count ?? 0)} reviews
                    </p>
                    <Link
                      to="/product/$productId"
                      params={{ productId: top.product_id }}
                      className="link-underline mt-4 inline-block text-sm"
                    >
                      Open product →
                    </Link>
                  </div>
                </div>
                <div className="mt-8">
                  <p className="eyebrow">Why this matches</p>
                  <p className="mt-4 text-sm leading-relaxed">{top.explanation?.summary}</p>
                  <div className="mt-3">
                    <SummaryNote llmUsed={example.data.llm_used} />
                  </div>
                  <div className="mt-5">
                    <EvidenceList result={top} />
                  </div>
                </div>
              </div>

              <div className="border border-border bg-background p-6 sm:p-8">
                <ScoreBreakdown
                  result={top}
                  weights={example.data.weights}
                  hasGoals={example.data.request.goals.length > 0}
                />
              </div>
            </div>
          ) : (
            <p className="mt-12 text-sm text-muted-foreground">Running the example search…</p>
          )}
        </div>
      </section>

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
