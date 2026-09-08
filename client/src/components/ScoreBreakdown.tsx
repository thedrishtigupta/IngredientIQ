import type { Signal } from "@/lib/scoring";

export function ScoreBreakdown({ signals, score }: { signals: Signal[]; score: number }) {
  return (
    <div>
      <div className="flex items-baseline justify-between">
        <p className="eyebrow">Computed recommendation score</p>
        <p className="numeric text-2xl">{score.toFixed(2)}</p>
      </div>
      <ul className="mt-5 space-y-4">
        {signals.map((s) => (
          <li key={s.key}>
            <div className="flex items-baseline justify-between gap-4">
              <span className="text-sm">{s.label}</span>
              <span className="numeric text-xs text-muted-foreground">
                {s.value === null ? "no data" : s.value.toFixed(2)} · w {s.weight.toFixed(2)}
              </span>
            </div>
            <div className="mt-1.5 h-[3px] w-full bg-muted">
              {s.value === null ? (
                <div className="h-full w-full [background:repeating-linear-gradient(90deg,var(--color-border-strong)_0_4px,transparent_4px_8px)]" />
              ) : (
                <div
                  className="h-full bg-foreground transition-[width] duration-700 ease-out"
                  style={{ width: `${Math.round(s.value * 100)}%` }}
                />
              )}
            </div>
            <p className="mt-1.5 text-xs leading-relaxed text-muted-foreground">{s.detail}</p>
          </li>
        ))}
      </ul>
      <p className="mt-5 border-t border-border pt-3 text-xs leading-relaxed text-muted-foreground">
        Signals without data are dropped and the remaining weights are renormalised, so a missing
        signal never counts as a zero.
      </p>
    </div>
  );
}
