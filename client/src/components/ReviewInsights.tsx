import type { Aspects } from "@/lib/api";
import { fmtInt, humanize, pct } from "@/lib/labels";

/** Per-aspect review sentiment. `null` = the product is outside the reviewed subset. */
export function ReviewInsights({ aspects }: { aspects: Aspects | null | undefined }) {
  if (!aspects) {
    return (
      <div className="empty-state p-6">
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
            <p className="break-words text-sm">{humanize(aspect)}</p>
            <div className="bar-track mt-2 max-w-56" aria-hidden="true">
              <span
                className="bar-scale bg-olive"
                style={{ "--v": Math.max(0, Math.min(1, a.positive_share)) } as React.CSSProperties}
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
