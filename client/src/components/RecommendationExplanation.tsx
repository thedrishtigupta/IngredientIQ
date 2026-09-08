import { groupLabel } from "@/lib/data";
import type { Requirements, ScoredProduct } from "@/lib/scoring";
import { ScoreBreakdown } from "./ScoreBreakdown";
import { ReviewInsights } from "./ReviewInsights";

export function EvidenceList({ result, req }: { result: ScoredProduct; req: Requirements }) {
  const items: { ok: boolean; text: string }[] = [];

  for (const f of req.functions) {
    items.push({
      ok: result.matched.includes(f),
      text: result.matched.includes(f)
        ? `${groupLabel(f)} ingredients detected`
        : `No ${groupLabel(f).toLowerCase()} ingredients detected`,
    });
  }
  for (const a of req.avoid) {
    items.push({
      ok: result.avoidedHits.length === 0,
      text:
        result.avoidedHits.length === 0
          ? `No ${groupLabel(a).toLowerCase()} ingredients detected`
          : `Contains ${result.avoidedHits.join(", ")}`,
    });
  }
  if (req.budget) {
    items.push({
      ok: result.product.price <= req.budget,
      text: `$${result.product.price} against a $${req.budget} budget`,
    });
  }
  const review = result.signals.find((s) => s.key === "review");
  if (review?.value !== null && review) {
    const top = result.product.reviewAspects?.slice().sort((a, b) => b.positiveShare - a.positiveShare)[0];
    if (top)
      items.push({
        ok: top.positiveShare >= 0.7,
        text: `${Math.round(top.positiveShare * 100)}% positive review sentiment on ${top.aspect.toLowerCase()}`,
      });
  }
  items.push({
    ok: result.product.rating >= 4.3,
    text: `Rated ${result.product.rating.toFixed(1)} of 5 across ${result.product.reviewCount.toLocaleString()} ratings`,
  });

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

export function ExplanationPanel({
  result,
  req,
  onClose,
}: {
  result: ScoredProduct;
  req: Requirements;
  onClose: () => void;
}) {
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
            <p className="mt-1.5 text-sm text-muted-foreground">{result.product.brand}</p>
            <h2 className="display text-2xl">{result.product.name}</h2>
          </div>
          <button type="button" onClick={onClose} className="text-sm text-muted-foreground hover:text-foreground">
            Close
          </button>
        </div>

        <div className="space-y-10 px-6 py-8">
          <section>
            <p className="eyebrow">Computed evidence</p>
            <div className="mt-4">
              <EvidenceList result={result} req={req} />
            </div>
          </section>

          <section>
            <ScoreBreakdown signals={result.signals} score={result.score} />
          </section>

          <section>
            <p className="eyebrow">Review signals</p>
            <div className="mt-4">
              <ReviewInsights aspects={result.product.reviewAspects} />
            </div>
          </section>

          <section className="border-t border-border pt-6">
            <p className="eyebrow">Written explanation</p>
            <p className="mt-3 text-sm leading-relaxed text-muted-foreground">
              The written summary is generated from the evidence above by the language model. It
              rephrases the computed signals; it does not select or reorder products. Connect the
              project API to generate it for live queries.
            </p>
          </section>
        </div>
      </div>
    </div>
  );
}
