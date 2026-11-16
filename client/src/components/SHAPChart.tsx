import { PendingResult } from "./ResearchChart";

export type ShapRow = { feature: string; meanAbsShap: number; direction: "positive" | "negative" };

export function SHAPChart({ rows }: { rows: ShapRow[] | null }) {
  if (!rows) {
    return (
      <PendingResult
        title="SHAP feature importance not yet computed"
        note="Mean absolute SHAP values per feature are exported by the trained model and rendered here. Until that artefact exists, nothing is drawn — a fabricated importance plot would misrepresent the study."
      />
    );
  }

  if (!rows.length) return <p className="text-sm text-muted-foreground">No features to show.</p>;
  const max = Math.max(...rows.map((r) => r.meanAbsShap)) || 1;
  return (
    <ul className="space-y-2.5">
      {rows.map((r) => (
        <li key={r.feature} className="grid grid-cols-[minmax(0,9rem)_1fr_3.5rem] items-center gap-3 sm:grid-cols-[13rem_1fr_4rem]">
          <span className="truncate text-sm" title={r.feature}>{r.feature}</span>
          <span className="bar-track h-3">
            <span
              className={`block h-full rounded-full ${r.direction === "positive" ? "bar-fill" : "bg-border-strong"}`}
              style={{ width: `${(r.meanAbsShap / max) * 100}%` }}
            />
          </span>
          <span className="numeric text-right text-xs text-muted-foreground">
            {r.meanAbsShap.toFixed(3)}
          </span>
        </li>
      ))}
    </ul>
  );
}
