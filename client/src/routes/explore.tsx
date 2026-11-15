import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { ErrorNotice } from "@/components/ErrorNotice";
import { FilterPanel } from "@/components/FilterPanel";
import { ProductCard } from "@/components/ProductCard";
import { ExplanationPanel, SummaryNote } from "@/components/RecommendationExplanation";
import { ScoreBreakdown } from "@/components/ScoreBreakdown";
import { SearchBar } from "@/components/SearchBar";
import {
  useAuth,
  useCategories,
  useGoals,
  useProducts,
  useRecommend,
  type RecommendBody,
} from "@/lib/api";
import { humanize } from "@/lib/labels";
import { emptyForm, fromParams, fromProfile, PRESETS, toBody, type SearchForm } from "@/lib/search-form";

/**
 * URL state: `?q=` is the text search, `?preset=` opens with an example goal search,
 * `?run=` (a saved /recommend body, from the search history) opens with that search filled in and run.
 */
type Search = {
  preset?: string | undefined;
  q?: string | undefined;
  run?: Record<string, unknown> | undefined;
};

const TEXT_RESULTS = 24;

export const Route = createFileRoute("/explore")({
  validateSearch: (s: Record<string, unknown>): Search => {
    const q = typeof s["q"] === "string" ? s["q"].trim() : "";
    const run = s["run"];
    return {
      preset: typeof s["preset"] === "string" ? (s["preset"] as string) : undefined,
      q: q || undefined,
      run: run && typeof run === "object" && !Array.isArray(run) ? (run as Record<string, unknown>) : undefined,
    };
  },
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
  const { preset, q = "", run: runParams } = Route.useSearch();
  const navigate = Route.useNavigate();
  const auth = useAuth();
  const signedIn = !!auth.user;
  const setQuery = (next: string) =>
    void navigate({ search: (prev) => ({ ...prev, q: next || undefined }), replace: true });
  // Wait until we know whether the user is signed in, so their search lands in their history.
  const textResults = useProducts(q, TEXT_RESULTS, q !== "" && !auth.loading, null, signedIn);

  const startForm = runParams
    ? fromParams(runParams)
    : (PRESETS.find((p) => p.id === preset)?.form ?? emptyForm);

  const [form, setForm] = useState<SearchForm>(startForm);
  // The request that was sent (null until the first search). Preset and history links search straight away.
  const [submitted, setSubmitted] = useState<RecommendBody | null>(
    preset || runParams ? toBody(startForm) : null,
  );
  const [openId, setOpenId] = useState<string | null>(null);

  const goals = useGoals();
  const categories = useCategories();
  const rec = useRecommend(
    submitted && !auth.loading ? { ...submitted, record_history: signedIn } : null,
  );
  const profile = auth.user?.profile;
  const hasProfile =
    !!profile &&
    (profile.goals.length > 0 ||
      !!profile.max_price ||
      !!profile.preferred_category ||
      profile.fragrance_free ||
      profile.avoided_ingredients.length > 0);

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

      <div className="mt-10 max-w-3xl">
        <SearchBar
          value={q}
          placeholder="Search by product, brand or type, e.g. drunk elephant serum"
          onSubmit={setQuery}
          onClear={() => setQuery("")}
          autoFocus={!preset}
        />
      </div>

      {q ? (
        <section aria-live="polite" className="mt-10">
          <div className="flex flex-wrap items-baseline justify-between gap-3">
            <p className="numeric text-xs text-muted-foreground">
              {textResults.isFetching || auth.loading
                ? "Searching…"
                : textResults.data
                  ? `${textResults.data.length === TEXT_RESULTS ? `Top ${TEXT_RESULTS}` : textResults.data.length} ${
                      textResults.data.length === 1 ? "product matches" : "products match"
                    } “${q}” · most-loved first`
                  : null}
            </p>
            <button
              type="button"
              onClick={() => setQuery("")}
              className="link-underline text-xs uppercase tracking-[0.12em]"
            >
              Clear search
            </button>
          </div>

          {textResults.error ? (
            <div className="mt-6">
              <ErrorNotice error={textResults.error} />
            </div>
          ) : textResults.data && !textResults.data.length ? (
            <div className="mt-6 border border-dashed border-border-strong px-6 py-12 text-center">
              <p className="display text-xl">No product matches “{q}”</p>
              <p className="mt-2 text-sm text-muted-foreground">
                Check the spelling, use fewer words, or search by goal with the filters below.
              </p>
            </div>
          ) : textResults.data ? (
            <div className="mt-8 grid grid-cols-2 gap-x-5 gap-y-12 sm:gap-x-8 lg:grid-cols-4">
              {textResults.data.map((p, i) => (
                <ProductCard key={p.product_id} product={p} index={i} />
              ))}
            </div>
          ) : null}
        </section>
      ) : null}

      <div className={`${q ? "mt-16 border-t border-border pt-10" : "mt-8"} flex flex-wrap items-center gap-x-5 gap-y-2`}>
        {hasProfile && profile ? (
          <button
            type="button"
            onClick={() => {
              const f = fromProfile(profile);
              setForm(f);
              run(f);
            }}
            className="border border-foreground px-3 py-1.5 text-xs uppercase tracking-[0.12em] transition-colors hover:bg-foreground hover:text-background"
          >
            Use my profile
          </button>
        ) : null}
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
          {(rec.isFetching || (submitted && auth.loading)) && !data ? (
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
