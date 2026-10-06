import { Link } from "@tanstack/react-router";
import type { ProductSummary } from "@/lib/api";
import { fmtInt, fmtPrice, fmtRating } from "@/lib/labels";
import { useCompare } from "@/lib/compare-store";
import { ProductImage } from "./ProductImage";

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
    <article className="group relative">
      <Link
        to="/product/$productId"
        params={{ productId: product.product_id }}
        className="block"
        aria-label={name}
      >
        <ProductImage
          id={product.product_id}
          alt={name}
          eager={index < 3}
          className="aspect-[4/5] w-full object-cover transition-transform duration-700 ease-out group-hover:scale-[1.035]"
        />
        <div className="mt-4">
          <p className="text-[0.7rem] uppercase tracking-[0.14em] text-muted-foreground">
            {product.brand ?? "Unknown brand"}
          </p>
          <h3 className="mt-1.5 text-[0.98rem] leading-snug text-foreground">{product.product_name}</h3>
          <p className="mt-1 text-xs text-muted-foreground">
            {[product.category, product.subcategory].filter(Boolean).join(" · ")}
          </p>
          <div className="mt-3 flex items-baseline justify-between border-t border-border pt-3">
            <span className="numeric text-sm">{fmtPrice(product.price)}</span>
            <span className="numeric text-xs text-muted-foreground">
              {fmtRating(product.rating)} ★ · {fmtInt(product.review_count ?? 0)} reviews
            </span>
          </div>
          {product.loves_count != null ? (
            <p className="numeric mt-1 text-[0.7rem] text-muted-foreground">
              {fmtInt(product.loves_count)} loves
            </p>
          ) : null}
          {tags.length ? (
            <div className="mt-3 flex flex-wrap gap-1.5">
              {tags.slice(0, 3).map((t) => (
                <span
                  key={t}
                  className="border border-border px-2 py-0.5 text-[0.62rem] uppercase tracking-[0.1em] text-muted-foreground"
                >
                  {t}
                </span>
              ))}
            </div>
          ) : null}
        </div>
      </Link>
      {rank !== undefined ? (
        <span className="numeric pointer-events-none absolute left-3 top-3 bg-foreground px-2.5 py-1 text-xs text-background">
          #{rank}
        </span>
      ) : null}
      <button
        type="button"
        onClick={() => toggle(product.product_id)}
        className={`absolute right-3 top-3 border px-2.5 py-1 text-[0.62rem] uppercase tracking-[0.12em] transition-opacity ${
          selected
            ? "border-foreground bg-foreground text-background opacity-100"
            : "border-border-strong bg-background/90 text-foreground opacity-0 focus:opacity-100 group-hover:opacity-100"
        }`}
      >
        {selected ? "In compare" : "Compare"}
      </button>
    </article>
  );
}
