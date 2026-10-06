import type { Aspects } from "@/lib/api";
import { fmtInt, humanize, pct } from "@/lib/labels";

/** Per-aspect review sentiment. `null` = the product is outside the reviewed subset. */
export function ReviewInsights({ aspects }: { aspects: Aspects | null | undefined }) {
  if (!aspects) {
    return (
      <div className="border border-dashed border-border-strong p-5">
        <p className="text-sm">No review signals for this product</p>
        <p className="mt-1.5 text-xs leading-relaxed text-muted-foreground">
          Review signals are only computed for the reviewed subset of the dataset. This product falls
          outside it, so review sentiment is excluded from its score rather than estimated.
        </p>
      </div>
    );
  }

  const rows = Object.entries(aspects).sort((a, b) => b[1].mentions - a[1].mentions);
  if (!rows.length) {
    return <p className="text-sm text-muted-foreground">No aspect has enough review mentions to report.</p>;
  }

  return (
    <ul className="divide-y divide-border border-y border-border">
      {rows.map(([aspect, a]) => (
        <li key={aspect} className="grid grid-cols-[1fr_auto] items-center gap-4 py-3">
          <div>
            <p className="text-sm">{humanize(aspect)}</p>
            <div className="mt-2 h-[3px] w-full max-w-56 bg-muted">
              <div
                className="h-full bg-olive transition-[width] duration-700"
                style={{ width: pct(a.positive_share) }}
              />
            </div>
          </div>
          <p className="numeric text-right text-xs text-muted-foreground">
            {pct(a.positive_share)} positive
            <br />
            {fmtInt(a.mentions)} mentions
          </p>
        </li>
      ))}
    </ul>
  );
}
