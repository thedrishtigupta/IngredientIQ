import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { ErrorNotice } from "@/components/ErrorNotice";
import { FilterPanel } from "@/components/FilterPanel";
import { ProductCard } from "@/components/ProductCard";
import { ExplanationPanel, SummaryNote } from "@/components/RecommendationExplanation";
import { ScoreBreakdown } from "@/components/ScoreBreakdown";
import { useCategories, useGoals, useRecommend, type RecommendBody } from "@/lib/api";
import { humanize } from "@/lib/labels";
import { emptyForm, PRESETS, toBody, type SearchForm } from "@/lib/search-form";

type Search = { preset?: string | undefined };

export const Route = createFileRoute("/explore")({
  validateSearch: (s: Record<string, unknown>): Search => ({
    preset: typeof s["preset"] === "string" ? (s["preset"] as string) : undefined,
  }),
  head: () => ({
    meta: [
      { title: "Explore — IngredientIQ" },
      {
        name: "description",
        content:
          "Choose your goals, category, budget and ingredient preferences, and see why each product ranks where it does.",
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
  const { preset } = Route.useSearch();
  const startForm = PRESETS.find((p) => p.id === preset)?.form ?? emptyForm;

  const [form, setForm] = useState<SearchForm>(startForm);
  // The request that was sent (null until the first search). A preset link searches straight away.
  const [submitted, setSubmitted] = useState<RecommendBody | null>(preset ? toBody(startForm) : null);
  const [openId, setOpenId] = useState<string | null>(null);

  const goals = useGoals();
  const categories = useCategories();
  const rec = useRecommend(submitted);

  const run = (f: SearchForm) => {
    const body = toBody(f);
    if (JSON.stringify(body) === JSON.stringify(submitted)) void rec.refetch(); // same search again, e.g. after an error
    else setSubmitted(body);
  };

  const data = rec.data;
  const hasGoals = (data?.request.goals.length ?? 0) > 0;
  const open = data?.results.find((r) => r.product_id === openId) ?? null;
  const error = rec.error ?? goals.error ?? categories.error;

  return (
    <div className="mx-auto max-w-[1220px] px-5 py-12 sm:px-8">
      <p className="eyebrow">Recommendation</p>
      <h1 className="display mt-4 max-w-2xl text-4xl sm:text-5xl">
        Pick what you need. See what the evidence supports.
      </h1>

      <div className="mt-8 flex flex-wrap items-center gap-x-5 gap-y-2">
        <span className="eyebrow">Try</span>
        {PRESETS.map((p) => (
          <button
            key={p.id}
            type="button"
            onClick={() => {
              setForm(p.form);
              run(p.form);
            }}
            className="link-underline text-sm text-muted-foreground hover:text-foreground"
          >
            {p.label}
          </button>
        ))}
      </div>

      <div className="mt-10 gap-12 border-t border-border pt-10 lg:grid lg:grid-cols-[300px_1fr]">
        <aside className="mb-12 lg:mb-0">
          <FilterPanel
            form={form}
            onChange={setForm}
            onSubmit={() => run(form)}
            busy={rec.isFetching}
            goals={goals.data}
            categories={categories.data}
          />
        </aside>

        <div>
          {rec.isFetching && !data ? (
            <div className="border border-dashed border-border-strong px-6 py-16 text-center">
              <p className="display text-xl">Ranking products…</p>
            </div>
          ) : error ? (
            <ErrorNotice error={error} />
          ) : !data ? (
            <div className="border border-dashed border-border-strong px-6 py-16 text-center">
              <p className="display text-xl">Nothing searched yet</p>
              <p className="mt-2 text-sm text-muted-foreground">
                Choose a goal and any filters, then press “Find products”, or try one of the examples
                above.
              </p>
            </div>
          ) : (
            <>
              <div className="mb-8">
                <p className="numeric text-xs text-muted-foreground">
                  {data.count} products meet the filters · ranked by hybrid score
                  {rec.isFetching ? " · updating…" : ""}
                </p>
                <div className="mt-2 max-w-xl">
                  <SummaryNote llmUsed={data.llm_used} />
                </div>
              </div>

              <div className="grid grid-cols-1 gap-x-5 gap-y-14 sm:grid-cols-2 sm:gap-x-8 xl:grid-cols-3">
                {data.results.map((r, i) => (
                  <div key={r.product_id}>
                    <ProductCard
                      product={r}
                      index={i}
                      rank={i + 1}
                      tags={r.matched_goals.map(humanize)}
                    />
                    <div className="mt-4 border-t border-border pt-3">
                      <div className="mb-3 flex items-baseline justify-between">
                        <span className="eyebrow">Score</span>
                        <span className="numeric text-lg">{r.score.toFixed(2)}</span>
                      </div>
                      <ScoreBreakdown result={r} hasGoals={hasGoals} compact />
                      <button
                        type="button"
                        onClick={() => setOpenId(r.product_id)}
                        className="link-underline mt-4 text-xs uppercase tracking-[0.12em]"
                      >
                        Why this product?
                      </button>
                    </div>
                  </div>
                ))}
              </div>

              {!data.results.length ? (
                <div className="border border-dashed border-border-strong px-6 py-16 text-center">
                  <p className="display text-xl">Nothing satisfies these constraints</p>
                  <p className="mt-2 text-sm text-muted-foreground">
                    Relax the budget or remove an ingredient requirement rather than accepting a weaker
                    match.
                  </p>
                </div>
              ) : null}
            </>
          )}
        </div>
      </div>

      {open && data ? (
        <ExplanationPanel
          result={open}
          weights={data.weights}
          hasGoals={hasGoals}
          llmUsed={data.llm_used}
          onClose={() => setOpenId(null)}
        />
      ) : null}
    </div>
  );
}
