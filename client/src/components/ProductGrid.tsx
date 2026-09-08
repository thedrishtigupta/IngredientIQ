import type { Product } from "@/lib/data";
import { ProductCard } from "./ProductCard";

export function ProductGrid({ products }: { products: Product[] }) {
  if (!products.length) {
    return (
      <div className="border border-dashed border-border-strong px-6 py-16 text-center">
        <p className="display text-xl">No products meet these constraints</p>
        <p className="mt-2 text-sm text-muted-foreground">
          Relax the budget, remove an avoided ingredient group, or widen the category.
        </p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-2 gap-x-5 gap-y-12 sm:gap-x-8 lg:grid-cols-3 xl:grid-cols-4">
      {products.map((p, i) => (
        <ProductCard key={p.id} product={p} index={i} />
      ))}
    </div>
  );
}
