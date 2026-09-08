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

  const max = Math.max(...rows.map((r) => r.meanAbsShap));
  return (
    <ul className="space-y-2.5">
      {rows.map((r) => (
        <li key={r.feature} className="grid grid-cols-[13rem_1fr_4rem] items-center gap-3">
          <span className="truncate text-sm">{r.feature}</span>
          <span className="h-3 w-full bg-muted">
            <span
              className={`block h-full ${r.direction === "positive" ? "bg-foreground" : "bg-border-strong"}`}
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
