import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { useState } from "react";
import { DataNote } from "@/components/DataNote";
import { SearchBar } from "@/components/SearchBar";
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
  { n: "03", t: "Ranked on evidence", d: "Ingredient match, ingredient similarity, product-type fit, review sentiment, rating and popularity are combined into one weighted score." },
  { n: "04", t: "See exactly why", d: "Every result opens into the computed scores, matched ingredients and review aspects behind its position." },
];

// Decorative ticker in the hero: common functional ingredients.
const TICKER = [
  "Niacinamide",
  "Hyaluronic acid",
  "Ceramides",
  "Squalane",
  "Retinol",
  "Vitamin C",
  "Salicylic acid",
  "Peptides",
  "Glycerin",
  "Panthenol",
  "Centella asiatica",
  "Zinc oxide",
];

function Home() {
  const navigate = useNavigate();
  const healthQuery = useHealth();
  const health = healthQuery.data;
  const loved = useProducts("", 8);
  const example = useRecommend(toBody(WORKED_EXAMPLE.form, 1));
  const top = example.data?.results[0];
  const [tickerPaused, setTickerPaused] = useState(false);

  return (
    <>
      {/* Hero */}
      <section className="ink-band overflow-hidden">
        <div className="mx-auto max-w-[1280px] px-5 pb-20 pt-16 sm:px-8 sm:pt-24 lg:pb-28">
          <div className="rise">
            <p className="eyebrow-gold !text-gold">Ingredient-aware discovery · non-medical</p>
            <h1 className="display mt-8 max-w-5xl text-[3rem] sm:text-7xl lg:text-[6.2rem]">
              Find beauty by what is <em className="text-gilded">actually inside</em> it.
            </h1>
          </div>

          <div className="mt-12 grid gap-10 lg:grid-cols-[1.25fr_0.75fr] lg:items-end">
            <div className="rise text-foreground" style={{ animationDelay: "120ms" }}>
              <SearchBar
                placeholder="Search by product, brand or type…"
                onSubmit={(q) => void navigate({ to: "/explore", search: { q: q || undefined } })}
              />
              <div className="mt-6 flex flex-wrap items-center gap-2">
                <span className="mr-2 text-[0.68rem] uppercase tracking-[0.22em] text-ink-foreground/50">
                  Try
                </span>
                {PRESETS.map((p) => (
                  <Link
                    key={p.id}
                    to="/explore"
                    search={{ preset: p.id }}
                    className="inline-flex min-h-9 items-center rounded-full border border-white/15 bg-white/5 px-4 py-1.5 text-[0.8rem] text-ink-foreground/80 backdrop-blur transition-[border-color,color,transform] duration-150 hover:border-gold/60 hover:text-gold active:scale-[0.97] [@media(pointer:coarse)]:min-h-11"
                  >
                    {p.label}
                  </Link>
                ))}
              </div>
            </div>
            <div className="rise lg:pb-2" style={{ animationDelay: "220ms" }}>
              <p className="max-w-md text-[0.98rem] leading-relaxed text-ink-foreground/65">
                IngredientIQ reads ingredient lists as functional composition, combines that with
                review-derived signals, rating and popularity, and produces recommendations you can
                inspect line by line.
              </p>
              <Link to="/explore" className="btn btn-gold mt-7">
                Find products by goal <span aria-hidden="true" className="arrow">→</span>
              </Link>
            </div>
          </div>

          <dl className="rise mt-20 grid grid-cols-3 divide-x divide-white/10 rounded-[1.5rem] border border-white/10 bg-white/[0.03] backdrop-blur" style={{ animationDelay: "320ms" }}>
            {[
              ["Products", health?.products],
              ["Reviews", health?.reviews],
              ["With reviews", health?.reviewed_products],
            ].map(([label, value]) => (
              <div key={label as string} className="min-w-0 px-4 py-6 sm:px-8 sm:py-8">
                <dt className="text-[0.62rem] uppercase tracking-[0.22em] text-ink-foreground/50 sm:text-[0.68rem]">
                  {label}
                </dt>
                <dd className="display mt-2 truncate tabular-nums text-3xl text-gilded sm:text-5xl">
                  {typeof value === "number" ? (
                    fmtInt(value)
                  ) : healthQuery.isLoading ? (
                    <span aria-hidden="true" className="mt-2 block h-8 w-24 max-w-full rounded-full bg-white/10 sm:h-11 sm:w-36" />
                  ) : (
                    "—"
                  )}
                </dd>
              </div>
            ))}
          </dl>
          <p className="mt-4 max-w-3xl text-xs leading-relaxed text-ink-foreground/45">
            <DataNote />
          </p>
        </div>

        <div className="relative border-t border-white/10" data-paused={tickerPaused}>
          <div className="flex w-max marquee gap-12 whitespace-nowrap py-5" aria-hidden="true">
            {[...TICKER, ...TICKER].map((t, i) => (
              <span key={i} className="display flex items-center gap-12 text-2xl italic text-ink-foreground/35">
                {t}
                <span className="text-sm not-italic text-gold/60">✦</span>
              </span>
            ))}
          </div>
          {/* Motion longer than 5s gets a pause control (hidden under reduced motion, where it never moves). */}
          <button
            type="button"
            onClick={() => setTickerPaused((v) => !v)}
            aria-label={tickerPaused ? "Play ingredient ticker" : "Pause ingredient ticker"}
            aria-pressed={tickerPaused}
            className="absolute right-3 top-1/2 flex h-9 w-9 -translate-y-1/2 items-center justify-center rounded-full border border-white/15 bg-ink/80 text-ink-foreground/70 backdrop-blur transition-colors duration-150 hover:border-gold/60 hover:text-gold motion-reduce:hidden sm:right-6"
          >
            <svg aria-hidden="true" viewBox="0 0 16 16" className="h-3 w-3" fill="currentColor">
              {tickerPaused ? <path d="M4 2.5v11l9-5.5z" /> : <path d="M4 2.5h3v11H4zM9 2.5h3v11H9z" />}
            </svg>
          </button>
        </div>
      </section>

      {/* How it works */}
      <section className="mx-auto max-w-[1280px] px-5 py-24 sm:px-8">
        <div className="flex flex-wrap items-end justify-between gap-6">
          <div>
            <p className="eyebrow-gold">The method</p>
            <h2 className="display mt-5 text-4xl sm:text-5xl">How it works</h2>
          </div>
          <p className="max-w-sm text-sm leading-relaxed text-muted-foreground">
            The ranking is computed. A language model, when configured, only words the
            explanation — it never chooses the products.
          </p>
        </div>
        <ol className="mt-14 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
          {steps.map((s) => (
            <li
              key={s.n}
              className="card-lux relative overflow-hidden p-7"
            >
              <span className="display text-gilded text-5xl">{s.n}</span>
              <h3 className="display mt-6 text-2xl">{s.t}</h3>
              <p className="mt-3 text-sm leading-relaxed text-muted-foreground">{s.d}</p>
              <span aria-hidden="true" className="absolute inset-x-7 bottom-0 h-px bg-gradient-to-r from-accent/50 to-gold/50" />
            </li>
          ))}
        </ol>
      </section>

      {/* Most loved */}
      <section className="mx-auto max-w-[1280px] px-5 pb-24 sm:px-8">
        <div className="flex flex-wrap items-end justify-between gap-6">
          <div>
            <p className="eyebrow-gold">The edit</p>
            <h2 className="display mt-5 text-4xl sm:text-5xl">Most-loved products</h2>
            <p className="mt-4 max-w-xl text-sm text-muted-foreground">
              The most-loved products in the catalog, regardless of goal. Product photos are
              placeholders: the dataset has none.
            </p>
          </div>
          <Link to="/explore" className="btn btn-outline">
            Search with goals <span aria-hidden="true" className="arrow">→</span>
          </Link>
        </div>
        <div className="mt-14">
          {loved.error ? (
            <ErrorNotice error={loved.error} />
          ) : loved.data ? (
            <ProductGrid products={loved.data} />
          ) : (
            <div className="grid grid-cols-2 gap-x-5 gap-y-14 sm:gap-x-8 lg:grid-cols-4">
              {Array.from({ length: 4 }).map((_, i) => (
                <div key={i} aria-hidden="true">
                  <div className="shimmer aspect-[4/5] rounded-[1.25rem]" />
                  <div className="shimmer mt-4 h-3 w-1/3 rounded-full" />
                  <div className="shimmer mt-3 h-5 w-3/4 rounded-full" />
                </div>
              ))}
            </div>
          )}
        </div>
      </section>

      {/* Explainability */}
      <section className="mx-auto max-w-[1280px] px-5 sm:px-8">
        <div className="card-lux overflow-hidden bg-paper p-6 sm:p-12 lg:p-16">
          <div className="max-w-2xl">
            <p className="eyebrow-gold">Explainability</p>
            <h2 className="display mt-5 text-4xl sm:text-5xl">
              Evidence, <em className="text-accent">not</em> a chat answer.
            </h2>
            <p className="mt-5 text-sm leading-relaxed text-muted-foreground">
              A live worked example: the top result of a real search. Every score below is computed
              from product data before any text is written.
            </p>
          </div>

          {example.error ? (
            <div className="mt-12">
              <ErrorNotice error={example.error} />
            </div>
          ) : top && example.data ? (
            <div className="mt-14 grid gap-12 lg:grid-cols-[0.95fr_1.05fr]">
              <div>
                <div className="rounded-2xl border border-gold/40 bg-gold-soft/30 px-5 py-4">
                  <p className="eyebrow">Search</p>
                  <p className="display mt-1.5 text-2xl">“{WORKED_EXAMPLE.label}”</p>
                </div>
                <div className="mt-8 flex gap-6">
                  <div className="w-32 shrink-0 overflow-hidden rounded-2xl shadow-[var(--shadow-soft)] sm:w-40">
                    <ProductImage id={top.product_id} alt={top.product_name} />
                  </div>
                  <div className="min-w-0">
                    <p className="text-[0.66rem] font-medium uppercase tracking-[0.2em] text-accent">{top.brand}</p>
                    <h3 className="display mt-1.5 break-words text-3xl">{top.product_name}</h3>
                    <p className="numeric mt-3 text-sm">{fmtPrice(top.price)}</p>
                    <p className="numeric text-xs text-muted-foreground">
                      <span aria-hidden="true" className="text-gold">★</span> {fmtRating(top.rating)} · {fmtInt(top.review_count ?? 0)} reviews
                    </p>
                    <Link
                      to="/product/$productId"
                      params={{ productId: top.product_id }}
                      className="btn btn-outline btn-sm mt-5"
                    >
                      Open product <span aria-hidden="true" className="arrow">→</span>
                    </Link>
                  </div>
                </div>
                <div className="mt-10">
                  <p className="eyebrow">Why this matches</p>
                  <p className="display mt-4 text-xl leading-snug">
                    {top.explanation?.summary || "No summary available."}
                  </p>
                  <div className="mt-3">
                    <SummaryNote llmUsed={example.data.llm_used} />
                  </div>
                  <div className="mt-6">
                    <EvidenceList result={top} />
                  </div>
                </div>
              </div>

              <div className="rounded-[1.5rem] border border-border bg-background p-6 sm:p-9">
                <ScoreBreakdown
                  result={top}
                  weights={example.data.weights}
                  hasGoals={example.data.request.goals.length > 0}
                />
              </div>
            </div>
          ) : (
            <div className="mt-14 grid gap-12 lg:grid-cols-2">
              <div className="shimmer h-72 rounded-2xl" />
              <div className="shimmer h-72 rounded-2xl" />
            </div>
          )}
        </div>
      </section>

      {/* Research teaser */}
      <section className="mx-auto max-w-[1280px] px-5 pt-24 sm:px-8">
        <div className="grid gap-10 border-t border-border pt-16 lg:grid-cols-[1.1fr_0.9fr] lg:items-end">
          <div>
            <p className="eyebrow-gold">Research track</p>
            <h2 className="display mt-5 text-4xl sm:text-5xl">
              Do ingredients predict product success — beyond brand, category and price?
            </h2>
          </div>
          <div>
            <p className="text-sm leading-relaxed text-muted-foreground">
              A parallel study compares a baseline metadata model against the same model with
              ingredient and ingredient-combination features, and reports SHAP-based feature
              importance. All findings are associational, never causal.
            </p>
            <Link to="/research" className="btn btn-primary mt-7">
              Read the study <span aria-hidden="true" className="arrow">→</span>
            </Link>
          </div>
        </div>
      </section>
    </>
  );
}
