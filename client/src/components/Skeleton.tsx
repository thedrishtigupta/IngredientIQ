/**
 * Loading placeholders that mirror the layout they stand in for, so nothing jumps when data lands.
 * Each block is aria-hidden; the wrapper carries one status message for screen readers.
 */

/** The one spinner (the `spinner` utility in styles.css). */
export function Spinner({ className = "" }: { className?: string }) {
  return <span aria-hidden="true" className={`spinner ${className}`} />;
}

function Bar({ className }: { className: string }) {
  return <div aria-hidden="true" className={`shimmer rounded-full ${className}`} />;
}

/** A grid of product-card placeholders (image, brand, name, price row). */
export function ProductGridSkeleton({
  count = 4,
  label = "Loading products…",
  className = "grid grid-cols-2 gap-x-5 gap-y-14 sm:gap-x-8 lg:grid-cols-4",
}: {
  count?: number;
  label?: string;
  className?: string;
}) {
  return (
    <div role={label ? "status" : undefined} aria-live={label ? "polite" : undefined} className={className}>
      {label ? <span className="sr-only">{label}</span> : null}
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} aria-hidden="true">
          <div className="shimmer aspect-[4/5] rounded-[1.25rem]" />
          <Bar className="mt-4 h-2.5 w-1/3" />
          <Bar className="mt-3 h-5 w-4/5" />
          <Bar className="mt-2 h-3 w-1/2" />
          <div className="mt-4 flex justify-between border-t border-border pt-3">
            <Bar className="h-3 w-12" />
            <Bar className="h-3 w-20" />
          </div>
        </div>
      ))}
    </div>
  );
}

/** Stacked text-line placeholders, e.g. for a list or a panel body. */
export function LinesSkeleton({
  lines = 6,
  label = "Loading…",
  className = "",
}: {
  lines?: number;
  label?: string;
  className?: string;
}) {
  const widths = ["w-11/12", "w-3/4", "w-5/6", "w-2/3", "w-4/5", "w-1/2"];
  return (
    <div role={label ? "status" : undefined} aria-live={label ? "polite" : undefined} className={`space-y-3.5 ${className}`}>
      {label ? <span className="sr-only">{label}</span> : null}
      {Array.from({ length: lines }).map((_, i) => (
        <Bar key={i} className={`h-3.5 ${widths[i % widths.length]}`} />
      ))}
    </div>
  );
}

/** A product-detail page placeholder: image on the left, title, stats and actions on the right. */
export function ProductDetailSkeleton() {
  return (
    <div role="status" aria-live="polite" className="mx-auto max-w-[1280px] px-5 py-10 sm:px-8">
      <span className="sr-only">Loading product…</span>
      <Bar className="h-3 w-40" />
      <div aria-hidden="true" className="mt-8 grid gap-12 lg:grid-cols-2 lg:gap-20">
        <div className="shimmer aspect-[4/5] rounded-[1.75rem]" />
        <div className="lg:pt-6">
          <Bar className="h-3 w-28" />
          <Bar className="mt-6 h-12 w-11/12" />
          <Bar className="mt-3 h-12 w-2/3" />
          <div className="mt-10 grid grid-cols-4 gap-4 rounded-[1.75rem] border border-border p-6">
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i}>
                <Bar className="h-2.5 w-2/3" />
                <Bar className="mt-3 h-5 w-full" />
              </div>
            ))}
          </div>
          <div className="mt-8 flex gap-3">
            <Bar className="h-11 w-28" />
            <Bar className="h-11 w-40" />
          </div>
        </div>
      </div>
    </div>
  );
}
