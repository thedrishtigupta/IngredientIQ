import { Link } from "@tanstack/react-router";
import { groupLabel, groupsOf, type Product } from "@/lib/data";
import { useCompare } from "@/lib/compare-store";

export function ProductCard({ product, index = 0 }: { product: Product; index?: number }) {
  const groups = groupsOf(product).slice(0, 3);
  const { has, toggle } = useCompare();
  const selected = has(product.id);

  return (
    <article className="group relative">
      <Link
        to="/product/$productId"
        params={{ productId: product.id }}
        className="block"
        aria-label={`${product.brand} ${product.name}`}
      >
        <div className="overflow-hidden bg-muted">
          <img
            src={product.image}
            alt={`${product.brand} ${product.name}`}
            width={900}
            height={1100}
            loading={index < 3 ? "eager" : "lazy"}
            className="aspect-[4/5] w-full object-cover transition-transform duration-700 ease-out group-hover:scale-[1.035]"
          />
        </div>
        <div className="mt-4">
          <p className="text-[0.7rem] uppercase tracking-[0.14em] text-muted-foreground">
            {product.brand}
          </p>
          <h3 className="mt-1.5 text-[0.98rem] leading-snug text-foreground">{product.name}</h3>
          <p className="mt-1 text-xs text-muted-foreground">{product.category}</p>
          <div className="mt-3 flex items-baseline justify-between border-t border-border pt-3">
            <span className="numeric text-sm">${product.price}</span>
            <span className="numeric text-xs text-muted-foreground">
              {product.rating.toFixed(1)} ★ · {product.reviewCount.toLocaleString()} reviews
            </span>
          </div>
          <p className="numeric mt-1 text-[0.7rem] text-muted-foreground">
            {product.loves.toLocaleString()} loves
          </p>
          <div className="mt-3 flex flex-wrap gap-1.5">
            {groups.map((g) => (
              <span
                key={g}
                className="border border-border px-2 py-0.5 text-[0.62rem] uppercase tracking-[0.1em] text-muted-foreground"
              >
                {groupLabel(g)}
              </span>
            ))}
          </div>
        </div>
      </Link>
      <button
        type="button"
        onClick={() => toggle(product.id)}
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
