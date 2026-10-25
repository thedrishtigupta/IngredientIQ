import { useState, type ReactNode } from "react";
import { createFileRoute } from "@tanstack/react-router";
import { AssociationChart, ModelComparisonChart } from "@/components/ResearchChart";
import { SHAPChart } from "@/components/SHAPChart";
import {
  research,
  scopeNames,
  targetsFor,
  type TargetKey,
  type TargetResult,
} from "@/lib/research";
import { fmtInt } from "@/lib/labels";

export const Route = createFileRoute("/research")({
  head: () => ({
    meta: [
      { title: "Research — Do ingredients predict product success? | IngredientIQ" },
      {
        name: "description",
        content:
          "A statistical and machine-learning study comparing a baseline metadata model against the same model with ingredient features, reported with SHAP explainability and as association, not causation.",
      },
      { property: "og:title", content: "Research — IngredientIQ" },
      {
        property: "og:description",
        content:
          "Model A vs Model B, ingredient associations and SHAP feature importance for beauty product success indicators.",
      },
    ],
  }),
  component: Research,
});

const method = [
  {
    t: "Feature engineering",
    d: "Presence and list position of the 300 most common ingredients, frequent combinations mined per category with FP-Growth, functional-group shares, and baseline metadata features.",
  },
  {
    t: "Statistical analysis",
    d: "Mann–Whitney U / chi-square / Kruskal–Wallis with Cliff's δ, Cramér's V and ε², Benjamini–Hochberg correction, and a second test holding brand, subcategory and price fixed.",
  },
  {
    t: "Predictive modelling",
    d: "Ridge / Logistic, Random Forest and LightGBM, each trained as Model A and Model B on identical folds: repeated 5-fold CV and a stricter split that holds out whole brands.",
  },
  {
    t: "Explainability",
    d: "SHAP values on the ingredient-aware LightGBM, with every important ingredient cross-checked against the adjusted statistical test. Reported as association only.",
  },
];

const GROUP_LABELS: Record<string, string> = {
  baseline: "Metadata (brand, category, price, popularity)",
  ingredient: "Individual ingredients",
  functional_group: "Functional-group shares",
  combination: "Ingredient combinations",
};

const CV_LABELS = { random: "Random 5-fold ×3", unseen_brand: "Unseen brands" } as const;

const fmtP = (p: number | null) => (p === null ? "—" : p < 0.001 ? "<0.001" : p.toFixed(3));
const fmtSigned = (v: number) => (v >= 0 ? "+" : "−") + Math.abs(v).toFixed(3);

function Chip({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: ReactNode;
}) {
  return (
    <button
      type="button"
      aria-pressed={active}
      onClick={onClick}
      className={`border px-3 py-1.5 text-sm transition-colors ${
        active
          ? "border-foreground bg-foreground text-background"
          : "border-border text-muted-foreground hover:border-border-strong hover:text-foreground"
      }`}
    >
      {children}
    </button>
  );
}

function Research() {
  const [scope, setScope] = useState(scopeNames[0] ?? "All");
  const targets = targetsFor(scope);
  const [targetKey, setTargetKey] = useState<TargetKey>("rating");
  const current = targets.find(([k]) => k === targetKey) ?? targets[0];
  const d = research.dataset;

  return (
    <div className="mx-auto max-w-[1220px] px-5 py-12 sm:px-8">
      <p className="eyebrow">Research track</p>
      <h1 className="display mt-4 max-w-3xl text-4xl sm:text-6xl">
        Do ingredient features add predictive value beyond brand, category, price and existing
        popularity?
      </h1>
      <p className="mt-6 max-w-2xl text-sm leading-relaxed text-muted-foreground">
        Success indicators under study are rating, popularity (loves), review count and
        recommendation rate. Two models are trained on the same outcome: one on metadata alone, one
        with ingredient and ingredient-combination features added. The difference between them is
        the evidence.
      </p>
      <p className="mt-4 max-w-2xl text-sm leading-relaxed text-muted-foreground">
        {fmtInt(d.analysis_products)} of {fmtInt(d.catalogue_products)} catalogue products are
        analysed: single formulas with an ingredient list, one product per family (minis, sets and
        re-listings removed). Model B adds {fmtInt(d.ingredientFeatures)} ingredient features,
        including {d.combinations} mined combinations. Generated {research.generatedOn}.
      </p>

      {/* Method */}
      <section className="mt-16 border-y border-border py-12">
        <div className="grid gap-x-12 gap-y-10 sm:grid-cols-2 lg:grid-cols-4">
          {method.map((m, i) => (
            <div key={m.t} className="rule-top pt-4">
              <span className="numeric text-xs text-accent">{String(i + 1).padStart(2, "0")}</span>
              <h2 className="mt-3 text-base">{m.t}</h2>
              <p className="mt-2 text-sm leading-relaxed text-muted-foreground">{m.d}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Selectors */}
      <section className="mt-16 space-y-4">
        <div className="flex flex-wrap items-center gap-2">
          <span className="eyebrow mr-3 w-16">Scope</span>
          {scopeNames.map((s) => (
            <Chip key={s} active={s === scope} onClick={() => setScope(s)}>
              {s === "All" ? "All categories" : s}
            </Chip>
          ))}
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <span className="eyebrow mr-3 w-16">Outcome</span>
          {targets.map(([k, t]) => (
            <Chip key={k} active={k === current?.[0]} onClick={() => setTargetKey(k)}>
              {t.label}
            </Chip>
          ))}
        </div>
      </section>

      {current ? <TargetView result={current[1]} /> : null}

      {/* Pre-specified hypotheses */}
      <section className="mt-20">
        <h2 className="display text-3xl">Hypotheses named before the analysis</h2>
        <p className="mt-3 max-w-2xl text-sm leading-relaxed text-muted-foreground">
          The synopsis proposed glycerin with hyaluronic acid as an example combination. Effect is
          the brand-, subcategory- and price-adjusted difference in standard deviations (in
          probability for the high-performer label).
          {research.untestable.length > 0
            ? ` Not testable, too rare in the catalogue: ${research.untestable.join(", ")}.`
            : null}
        </p>
        <div className="mt-6 overflow-x-auto">
          <table className="w-full min-w-[560px] text-sm">
            <thead>
              <tr className="border-b border-border text-left text-xs text-muted-foreground">
                <th className="py-2 font-normal">Combination</th>
                <th className="py-2 font-normal">Scope</th>
                <th className="py-2 font-normal">Outcome</th>
                <th className="py-2 text-right font-normal">Adjusted effect</th>
                <th className="py-2 text-right font-normal">q (adjusted)</th>
              </tr>
            </thead>
            <tbody>
              {research.prespecified.map((p) => (
                <tr key={`${p.label}-${p.scope}-${p.target}`} className="border-b border-border">
                  <td className="py-2">{p.label}</td>
                  <td className="py-2">{p.scope}</td>
                  <td className="py-2">
                    {research.scopes[p.scope]?.[p.target]?.label ?? p.target}
                  </td>
                  <td className="numeric py-2 text-right">
                    {p.effect === null ? "—" : fmtSigned(p.effect)}
                  </td>
                  <td className="numeric py-2 text-right">{fmtP(p.adjustedP)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="mt-20 border-t border-border pt-8">
        <p className="eyebrow">Interpretation limits</p>
        <ul className="mt-4 max-w-2xl space-y-2 text-sm leading-relaxed text-muted-foreground">
          <li>— Findings are associational / correlational. No causal claim is made or implied.</li>
          <li>
            — Recommendation rate exists only for {fmtInt(d.targetsAvailable.rec_rate)} reviewed
            products, all of them Skincare.
          </li>
          <li>
            — Ratings are used only for products with at least 25 reviews (
            {fmtInt(d.targetsAvailable.rating)} products).
          </li>
          <li>— Popularity and rating are market outcomes shaped by brand, price and marketing.</li>
          <li>
            — A high SHAP share means the model uses a feature, not that the feature adds
            information the metadata did not already carry. Compare with Model A vs Model B.
          </li>
          <li>— Nothing here is medical, dermatological or diagnostic guidance.</li>
        </ul>
      </section>
    </div>
  );
}

function TargetView({ result }: { result: TargetResult }) {
  const shares = Object.entries(result.shapShares).sort((a, b) => (b[1] ?? 0) - (a[1] ?? 0));

  return (
    <>
      {/* Model comparison */}
      <section className="mt-16">
        <div className="flex flex-wrap items-baseline justify-between gap-4">
          <h2 className="display text-3xl">Model A vs Model B</h2>
          <p className="text-sm text-muted-foreground">
            {fmtInt(result.n)} products · LightGBM, random CV, mean over folds
          </p>
        </div>
        <div className="mt-8">
          <ModelComparisonChart rows={result.modelComparison} />
        </div>

        <div className="mt-10 overflow-x-auto">
          <table className="w-full min-w-[640px] text-sm">
            <thead>
              <tr className="border-b border-border text-left text-xs text-muted-foreground">
                <th className="py-2 font-normal">Model</th>
                <th className="py-2 font-normal">Split</th>
                <th className="py-2 text-right font-normal">A</th>
                <th className="py-2 text-right font-normal">B</th>
                <th className="py-2 text-right font-normal">Gain</th>
                <th className="py-2 text-right font-normal">B wins</th>
                <th className="py-2 text-right font-normal">p (corrected)</th>
                <th className="py-2 pl-4 font-normal">Verdict</th>
              </tr>
            </thead>
            <tbody>
              {result.comparisons.map((c) => (
                <tr key={`${c.model}-${c.cv}`} className="border-b border-border">
                  <td className="py-2">{c.model}</td>
                  <td className="py-2 text-muted-foreground">{CV_LABELS[c.cv]}</td>
                  <td className="numeric py-2 text-right">{c.a.toFixed(3)}</td>
                  <td className="numeric py-2 text-right">{c.b.toFixed(3)}</td>
                  <td className="numeric py-2 text-right">{fmtSigned(c.gain)}</td>
                  <td className="numeric py-2 text-right">
                    {c.bWins}/{c.folds}
                  </td>
                  <td className="numeric py-2 text-right">{fmtP(c.pCorrected)}</td>
                  <td
                    className={`py-2 pl-4 ${c.verdict === "B better" ? "text-olive" : c.verdict === "A better" ? "text-accent" : "text-muted-foreground"}`}
                  >
                    {c.verdict}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="mt-3 max-w-2xl text-xs leading-relaxed text-muted-foreground">
            Metric: {result.comparisons[0]?.metric}. The corrected p-value (Nadeau–Bengio) accounts
            for cross-validation folds sharing training data. “Unseen brands” holds out whole
            brands, so the model cannot rely on knowing which brands are popular.
          </p>
        </div>
      </section>

      {/* Associations */}
      <section className="mt-20">
        <h2 className="display text-3xl">Ingredients associated with this outcome</h2>
        <p className="mt-3 max-w-2xl text-sm leading-relaxed text-muted-foreground">
          {fmtInt(result.tests.total)} ingredients and combinations tested.{" "}
          {fmtInt(result.tests.significantRaw)} look significant on their own; only{" "}
          {fmtInt(result.tests.significantAdjusted)} remain when comparing products of the same
          brand, subcategory and price, and {fmtInt(result.tests.robust)} pass both tests in the
          same direction. Those robust ones are shown, as the adjusted difference in standard
          deviations; q is the Benjamini–Hochberg corrected p-value.
        </p>
        <div className="mt-8">
          {result.associations.length > 0 ? (
            <AssociationChart items={result.associations} />
          ) : (
            <p className="text-sm text-muted-foreground">
              No ingredient or combination passes both tests for this outcome.
            </p>
          )}
        </div>
      </section>

      {/* SHAP */}
      <section className="mt-20">
        <h2 className="display text-3xl">SHAP feature importance</h2>
        <p className="mt-3 max-w-2xl text-sm leading-relaxed text-muted-foreground">
          Mean absolute SHAP value per feature in the ingredient-aware LightGBM model: how much each
          input moves its predictions. Share of the total by feature family:
        </p>
        <ul className="mt-6 max-w-2xl space-y-2">
          {shares.map(([group, share]) => (
            <li
              key={group}
              className="grid grid-cols-[minmax(0,16rem)_1fr_3.5rem] items-center gap-3"
            >
              <span className="truncate text-sm">{GROUP_LABELS[group] ?? group}</span>
              <span className="h-2 w-full bg-muted">
                <span
                  className={`block h-full ${group === "baseline" ? "bg-border-strong" : "bg-foreground"}`}
                  style={{ width: `${(share ?? 0) * 100}%` }}
                />
              </span>
              <span className="numeric text-right text-xs">{((share ?? 0) * 100).toFixed(0)}%</span>
            </li>
          ))}
        </ul>
        <div className="mt-10 grid gap-12 lg:grid-cols-2">
          <div>
            <p className="eyebrow mb-4">All features</p>
            <SHAPChart rows={result.shap} />
          </div>
          <div>
            <p className="eyebrow mb-4">Ingredient-type features</p>
            <SHAPChart rows={result.ingredientShap} />
            <p className="mt-4 text-xs leading-relaxed text-muted-foreground">
              Confirmed by the adjusted statistical test:{" "}
              {result.ingredientShap
                .filter((r) => r.confirmed)
                .map((r) => r.feature)
                .join(", ") || "none of these"}
              .
            </p>
          </div>
        </div>
      </section>
    </>
  );
}
