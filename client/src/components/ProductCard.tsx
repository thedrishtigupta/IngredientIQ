import { Link } from "@tanstack/react-router";
import type { ProductSummary } from "@/lib/api";
import { fmtInt, fmtPrice, fmtRating } from "@/lib/labels";
import { useCompare } from "@/lib/compare-store";
import { ProductImage } from "./ProductImage";
import { SaveButton } from "./SaveButton";

type Props = {
  product: ProductSummary & { loves_count?: number | null };
  index?: number;
  /** Position in a ranked list (1 = best). */
  rank?: number;
  /** Small chips under the card, e.g. matched goals. */
  tags?: string[];
};

export function ProductCard({ product, index = 0, rank, tags = [] }: Props) {
  const { has, toggle } = useCompare();
  const selected = has(product.product_id);
  const name = `${product.brand ?? ""} ${product.product_name}`.trim();

  return (
    <article className="group relative min-w-0">
      <Link to="/product/$productId" params={{ productId: product.product_id }} className="block rounded-[1.25rem]">
        <div className="overflow-hidden rounded-[1.25rem] shadow-[var(--shadow-soft)] ring-1 ring-border/60 transition-shadow duration-300 group-hover:shadow-[var(--shadow-lift)]">
          <ProductImage
            id={product.product_id}
            alt={name}
            eager={index < 3}
            className="zoom aspect-[4/5] w-full object-cover"
          />
        </div>
        <div className="mt-4 px-0.5">
          <p className="truncate text-[0.66rem] font-medium uppercase tracking-[0.2em] text-accent">
            {product.brand ?? "Unknown brand"}
          </p>
          <h3 className="display mt-1.5 line-clamp-2 break-words text-[1.3rem] leading-[1.15] text-foreground">
            <span className="link-underline">{product.product_name}</span>
          </h3>
          <p className="mt-1 truncate text-xs text-muted-foreground">
            {[product.category, product.subcategory].filter(Boolean).join(" · ")}
          </p>
          <div className="mt-3 flex items-baseline justify-between gap-3 border-t border-border pt-3">
            <span className="numeric text-sm font-medium">{fmtPrice(product.price)}</span>
            <span className="numeric text-xs text-muted-foreground">
              <span aria-hidden="true" className="text-gold">
                ★
              </span>
              <span className="sr-only">Rating </span>
              {fmtRating(product.rating)} · {fmtInt(product.review_count ?? 0)}
              <span className="sr-only"> reviews</span>
            </span>
          </div>
          {product.loves_count != null ? (
            <p className="numeric mt-1 text-[0.7rem] text-muted-foreground">
              <span aria-hidden="true">♡ </span>
              {fmtInt(product.loves_count)} loves
            </p>
          ) : null}
          {tags.length ? (
            <div className="mt-3 flex flex-wrap gap-1.5">
              {tags.slice(0, 3).map((t) => (
                <span
                  key={t}
                  className="rounded-full bg-gold-soft/60 px-2.5 py-0.5 text-[0.62rem] uppercase tracking-[0.12em] text-foreground/75"
                >
                  {t}
                </span>
              ))}
            </div>
          ) : null}
        </div>
      </Link>
      {rank !== undefined ? (
        <span
          className={`numeric pointer-events-none absolute left-3 top-3 flex h-9 min-w-9 items-center justify-center rounded-full px-2 text-xs shadow-md ${
            rank === 1 ? "btn-gold" : "bg-ink/85 text-ink-foreground backdrop-blur"
          }`}
        >
          <span className="sr-only">Rank </span>
          {rank}
        </span>
      ) : null}
      {/* Always visible on touch; on a fine pointer it appears on hover or keyboard focus. */}
      <button
        type="button"
        onClick={() => toggle(product.product_id)}
        aria-pressed={selected}
        aria-label={selected ? `Remove ${name} from comparison` : `Add ${name} to comparison`}
        className={`absolute right-14 top-3 flex h-9 items-center rounded-full px-3 text-[0.6rem] uppercase tracking-[0.14em] shadow-sm backdrop-blur transition-[opacity,background-color,color,transform] duration-150 active:scale-95 ${
          selected
            ? "bg-foreground text-background"
            : "bg-background/85 text-foreground [@media(hover:hover)_and_(pointer:fine)]:opacity-0 [@media(hover:hover)_and_(pointer:fine)]:group-hover:opacity-100 focus-visible:opacity-100"
        }`}
      >
        <span aria-hidden="true">{selected ? "✓ Comparing" : "+ Compare"}</span>
      </button>
      <SaveButton productId={product.product_id} className="absolute right-3 top-3" />
    </article>
  );
}
