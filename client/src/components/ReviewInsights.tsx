import type { ReviewAspect } from "@/lib/data";

export function ReviewInsights({ aspects }: { aspects: ReviewAspect[] | null }) {
  if (!aspects) {
    return (
      <div className="border border-dashed border-border-strong p-5">
        <p className="text-sm">No review signals for this product</p>
        <p className="mt-1.5 text-xs leading-relaxed text-muted-foreground">
          Aspect sentiment is only computed for the reviewed subset of the dataset. This product
          falls outside it, so review signals are excluded from its score rather than estimated.
        </p>
      </div>
    );
  }

  return (
    <ul className="divide-y divide-border border-y border-border">
      {aspects.map((a) => (
        <li key={a.aspect} className="grid grid-cols-[1fr_auto] items-center gap-4 py-3">
          <div>
            <p className="text-sm">{a.aspect}</p>
            <div className="mt-2 h-[3px] w-full max-w-56 bg-muted">
              <div
                className="h-full bg-olive transition-[width] duration-700"
                style={{ width: `${Math.round(a.positiveShare * 100)}%` }}
              />
            </div>
          </div>
          <p className="numeric text-right text-xs text-muted-foreground">
            {Math.round(a.positiveShare * 100)}% positive
            <br />
            {a.mentions.toLocaleString()} mentions
          </p>
        </li>
      ))}
    </ul>
  );
}
