import { Link } from "@tanstack/react-router";
import type { Recommendation } from "@/lib/api";
import { humanize } from "@/lib/labels";
import { useDialog } from "@/lib/use-dialog";
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
          <span
            aria-hidden="true"
            className={`numeric mt-[2px] flex h-5 w-5 shrink-0 items-center justify-center rounded-full text-[0.65rem] ${i.ok ? "bg-olive/10 text-olive" : "bg-muted text-muted-foreground"}`}
          >
            {i.ok ? "✓" : "—"}
          </span>
          <span className={`min-w-0 break-words ${i.ok ? "" : "text-muted-foreground"}`}>
            <span className="sr-only">{i.ok ? "Strength: " : "Weakness: "}</span>
            {i.text}
          </span>
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
  const ref = useDialog<HTMLDivElement>(true, onClose);
  const titleId = `why-${result.product_id}`;

  return (
    <div className="fixed inset-0 z-50 flex justify-end" role="dialog" aria-modal="true" aria-labelledby={titleId}>
      {/* Pointer-only backdrop: keyboard users close with Escape or the panel's own button. */}
      <div aria-hidden="true" onClick={onClose} className="sheet-fade absolute inset-0 bg-ink/45 backdrop-blur-[3px]" />
      <div
        ref={ref}
        tabIndex={-1}
        className="sheet-in relative flex h-full w-full max-w-[540px] flex-col overflow-y-auto overscroll-contain border-l border-border bg-paper pb-[env(safe-area-inset-bottom)] shadow-2xl focus:outline-none"
      >
        <div className="glass sticky top-0 z-10 flex items-start justify-between gap-6 border-b border-border px-7 py-6">
          <div>
            <p className="eyebrow-gold">Why this product</p>
            <p className="mt-1.5 text-sm text-muted-foreground">{result.brand}</p>
            <h2 id={titleId} className="display break-words text-3xl">
              {result.product_name}
            </h2>
          </div>
          <button
            type="button"
            data-autofocus
            onClick={onClose}
            aria-label="Close explanation"
            className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full border border-border text-muted-foreground transition-[background-color,color,transform] duration-150 hover:bg-foreground hover:text-background active:scale-95"
          >
            <span aria-hidden="true">✕</span>
          </button>
        </div>

        <div className="space-y-10 px-7 py-8">
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
              Open the full product page <span aria-hidden="true" className="arrow">→</span>
            </Link>
          </section>
        </div>
      </div>
    </div>
  );
}
