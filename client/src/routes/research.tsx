import { createFileRoute } from "@tanstack/react-router";
import { AssociationChart, ModelComparisonChart } from "@/components/ResearchChart";
import { SHAPChart } from "@/components/SHAPChart";
import { researchStatus } from "@/lib/data";

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
    d: "Individual ingredient presence and rank, frequent ingredient combinations via Apriori / FP-Growth, functional-group aggregates, and baseline metadata features.",
  },
  {
    t: "Statistical analysis",
    d: "Pearson and Spearman correlation, t-test / ANOVA / chi-square, Benjamini–Hochberg correction, and effect sizes (Cohen's d, Cramér's V).",
  },
  {
    t: "Predictive modelling",
    d: "Classification of high vs low performers and regression on continuous outcomes, using Logistic/Linear baselines and Random Forest, XGBoost and LightGBM.",
  },
  {
    t: "Explainability",
    d: "SHAP values rank the features most associated with high-performing products. Reported as association only.",
  },
];

function Research() {
  const { modelComparison, associations, shap } = researchStatus;

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

      {/* Model comparison */}
      <section className="mt-20">
        <div className="flex flex-wrap items-baseline justify-between gap-4">
          <h2 className="display text-3xl">Model A vs Model B</h2>
          <p className="text-sm text-muted-foreground">
            R², MAE, RMSE for regression · Accuracy, F1, ROC-AUC for classification
          </p>
        </div>
        <div className="mt-8">
          <ModelComparisonChart rows={modelComparison} />
        </div>
      </section>

      {/* Associations */}
      <section className="mt-20">
        <h2 className="display text-3xl">Ingredients associated with high performers</h2>
        <p className="mt-3 max-w-2xl text-sm leading-relaxed text-muted-foreground">
          Ranked by effect size with multiple-comparison-corrected significance. An ingredient
          appearing here is associated with high-performing products in this dataset; it does not
          make a product succeed.
        </p>
        <div className="mt-8">
          <AssociationChart items={associations} />
        </div>
      </section>

      {/* SHAP */}
      <section className="mt-20">
        <h2 className="display text-3xl">SHAP feature importance</h2>
        <p className="mt-3 max-w-2xl text-sm leading-relaxed text-muted-foreground">
          Mean absolute SHAP value per feature in the ingredient-aware model, showing which inputs
          move its predictions most.
        </p>
        <div className="mt-8">
          <SHAPChart rows={shap} />
        </div>
      </section>

      <section className="mt-20 border-t border-border pt-8">
        <p className="eyebrow">Interpretation limits</p>
        <ul className="mt-4 max-w-2xl space-y-2 text-sm leading-relaxed text-muted-foreground">
          <li>— Findings are associational / correlational. No causal claim is made or implied.</li>
          <li>— Review-derived signals are limited to the reviewed subset of the catalog.</li>
          <li>— Popularity and rating are market outcomes shaped by brand, price and marketing.</li>
          <li>— Nothing here is medical, dermatological or diagnostic guidance.</li>
        </ul>
      </section>
    </div>
  );
}
