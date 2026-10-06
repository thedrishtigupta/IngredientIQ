import { Link } from "@tanstack/react-router";
import type { Recommendation } from "@/lib/api";
import { humanize } from "@/lib/labels";
import { IngredientBadge } from "./IngredientBadge";
import { ReviewInsights } from "./ReviewInsights";
import { ScoreBreakdown } from "./ScoreBreakdown";

/** The API's computed strengths (check) and weaknesses (dash). */
export function EvidenceList({ result }: { result: Recommendation }) {
  const items = [
    ...(result.explanation?.strengths ?? []).map((text) => ({ ok: true, text })),
    ...(result.explanation?.weaknesses ?? []).map((text) => ({ ok: false, text })),
  ];
  if (!items.length) return <p className="text-sm text-muted-foreground">No strengths or weaknesses reported.</p>;

  return (
    <ul className="space-y-2.5">
      {items.map((i, idx) => (
        <li key={idx} className="flex gap-3 text-sm leading-relaxed">
          <span className={`numeric mt-[1px] ${i.ok ? "text-olive" : "text-muted-foreground"}`}>
            {i.ok ? "✓" : "—"}
          </span>
          <span className={i.ok ? "" : "text-muted-foreground"}>{i.text}</span>
        </li>
      ))}
    </ul>
  );
}

/** Where the summary text came from, so nobody mistakes a template for an LLM answer. */
export function SummaryNote({ llmUsed }: { llmUsed: boolean }) {
  return (
    <p className="text-xs leading-relaxed text-muted-foreground">
      {llmUsed
        ? "Written by a language model from the computed evidence below. It rephrases the scores; it does not choose or reorder products."
        : "Template sentence built from the computed evidence below (no language model is configured). Either way, the ranking itself is computed, not generated."}
    </p>
  );
}

export function ExplanationPanel({
  result,
  weights,
  hasGoals,
  llmUsed,
  onClose,
}: {
  result: Recommendation;
  weights: Record<string, number>;
  hasGoals: boolean;
  llmUsed: boolean;
  onClose: () => void;
}) {
  const matched = result.matched_ingredients;

  return (
    <div className="fixed inset-0 z-50 flex justify-end" role="dialog" aria-modal="true">
      <button
        type="button"
        aria-label="Close explanation"
        onClick={onClose}
        className="absolute inset-0 bg-foreground/25"
      />
      <div className="relative flex h-full w-full max-w-[520px] flex-col overflow-y-auto border-l border-border bg-paper rise">
        <div className="sticky top-0 flex items-start justify-between gap-6 border-b border-border bg-paper px-6 py-5">
          <div>
            <p className="eyebrow">Why this product</p>
            <p className="mt-1.5 text-sm text-muted-foreground">{result.brand}</p>
            <h2 className="display text-2xl">{result.product_name}</h2>
          </div>
          <button type="button" onClick={onClose} className="text-sm text-muted-foreground hover:text-foreground">
            Close
          </button>
        </div>

        <div className="space-y-10 px-6 py-8">
          <section>
            <p className="eyebrow">Summary</p>
            <p className="mt-4 text-sm leading-relaxed">{result.explanation?.summary ?? "No summary available."}</p>
            <div className="mt-3">
              <SummaryNote llmUsed={llmUsed} />
            </div>
          </section>

          <section>
            <p className="eyebrow">Strengths and weaknesses</p>
            <div className="mt-4">
              <EvidenceList result={result} />
            </div>
          </section>

          <section>
            <p className="eyebrow">
              Matched ingredients{result.matched_goals.length ? ` · ${result.matched_goals.map(humanize).join(", ")}` : ""}
            </p>
            {matched.length ? (
              <div className="mt-4 flex flex-wrap gap-1.5">
                {matched.slice(0, 24).map((name) => (
                  <IngredientBadge key={name} label={name} />
                ))}
                {matched.length > 24 ? (
                  <span className="px-1 py-1 text-xs text-muted-foreground">+{matched.length - 24} more</span>
                ) : null}
              </div>
            ) : (
              <p className="mt-4 text-sm text-muted-foreground">
                {hasGoals ? "None of the goal's ingredients were found." : "No goal was selected, so nothing was matched."}
              </p>
            )}
          </section>

          <section>
            <ScoreBreakdown result={result} weights={weights} hasGoals={hasGoals} />
          </section>

          <section>
            <p className="eyebrow">Review signals</p>
            <div className="mt-4">
              <ReviewInsights aspects={result.review_score === null ? null : result.aspects} />
            </div>
          </section>

          <section className="border-t border-border pt-6">
            <Link
              to="/product/$productId"
              params={{ productId: result.product_id }}
              className="link-underline text-sm"
            >
              Open the full product page →
            </Link>
          </section>
        </div>
      </div>
    </div>
  );
}
