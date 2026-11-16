export type MetricRow = { metric: string; modelA: number; modelB: number; higherIsBetter: boolean };

export function PendingResult({ title, note }: { title: string; note: string }) {
  return (
    <div className="empty-state px-6 py-12">
      <p className="eyebrow">Awaiting results</p>
      <p className="display mt-2 text-2xl">{title}</p>
      <p className="mt-3 max-w-xl text-sm leading-relaxed text-muted-foreground">{note}</p>
    </div>
  );
}

export function ModelComparisonChart({ rows }: { rows: MetricRow[] | null }) {
  if (!rows) {
    return (
      <PendingResult
        title="Model A vs Model B not yet computed"
        note="This panel renders cross-validated metrics for the baseline metadata model and the metadata-plus-ingredient-features model once the modelling pipeline publishes them. No placeholder numbers are shown."
      />
    );
  }

  return (
    <ul className="divide-y divide-border border-y border-border">
      {rows.map((r) => {
        const max = Math.max(r.modelA, r.modelB) || 1;
        return (
          <li key={r.metric} className="py-5">
            <div className="flex items-baseline justify-between">
              <p className="text-sm">{r.metric}</p>
              <p className="numeric text-xs text-muted-foreground">
                {r.higherIsBetter ? "higher is better" : "lower is better"}
              </p>
            </div>
            {[
              { label: "A · metadata only", v: r.modelA, cls: "bg-border-strong" },
              { label: "B · + ingredient features", v: r.modelB, cls: "bar-fill" },
            ].map((b) => (
              <div key={b.label} className="mt-3 grid grid-cols-[minmax(0,8rem)_1fr_3rem] items-center gap-3 sm:grid-cols-[11rem_1fr_3rem]">
                <span className="break-words text-xs text-muted-foreground">{b.label}</span>
                <span className="bar-track h-2">
                  <span
                    className={`block h-full rounded-full ${b.cls}`}
                    style={{ width: `${(b.v / max) * 100}%` }}
                  />
                </span>
                <span className="numeric text-right text-xs">{b.v.toFixed(3)}</span>
              </div>
            ))}
          </li>
        );
      })}
    </ul>
  );
}

export function AssociationChart({
  items,
}: {
  items: { label: string; effect: number; adjustedP: number }[] | null;
}) {
  if (!items) {
    return (
      <PendingResult
        title="Ingredient associations not yet computed"
        note="Ranked ingredients and frequent ingredient combinations appear here after correlation and group testing with Benjamini–Hochberg correction and effect sizes. Associations only — never causal claims."
      />
    );
  }

  if (!items.length) return null;
  const max = Math.max(...items.map((i) => Math.abs(i.effect))) || 1;
  return (
    <ul className="space-y-3">
      {items.map((i) => (
        <li key={i.label} className="grid grid-cols-[minmax(0,9rem)_1fr_4.5rem] items-center gap-3 sm:grid-cols-[12rem_1fr_5rem]">
          <span className="truncate text-sm" title={i.label}>{i.label}</span>
          <span className="bar-track h-2.5">
            <span
              className={`block h-full rounded-full ${i.effect >= 0 ? "bg-olive" : "bg-accent"}`}
              style={{ width: `${(Math.abs(i.effect) / max) * 100}%` }}
            />
          </span>
          <span className="numeric text-right text-xs text-muted-foreground">
            q={i.adjustedP.toFixed(3)}
          </span>
        </li>
      ))}
    </ul>
  );
}
