import product1 from "@/assets/product-1.jpg";
import product2 from "@/assets/product-2.jpg";
import product3 from "@/assets/product-3.jpg";
import product4 from "@/assets/product-4.jpg";
import product5 from "@/assets/product-5.jpg";
import product6 from "@/assets/product-6.jpg";

const PLACEHOLDERS = [product1, product2, product3, product4, product5, product6];

/** The dataset has no product photos, so a product id always maps to the same stock image. */
function placeholderFor(id: string) {
  let h = 0;
  for (const c of id) h = (h * 31 + c.charCodeAt(0)) >>> 0;
  return PLACEHOLDERS[h % PLACEHOLDERS.length]!;
}

export function ProductImage({
  id,
  alt,
  className = "aspect-[4/5] w-full object-cover",
  eager = false,
  tag = true,
}: {
  id: string;
  alt: string;
  className?: string;
  eager?: boolean;
  /** Show the small "Placeholder image" label (hide it on tiny thumbnails). */
  tag?: boolean;
}) {
  return (
    <div className="relative overflow-hidden bg-muted" title="Placeholder image: the dataset has no product photos">
      <img
        src={placeholderFor(id)}
        alt={alt}
        width={900}
        height={1100}
        loading={eager ? "eager" : "lazy"}
        className={className}
      />
      {tag ? (
        <span className="pointer-events-none absolute bottom-2 left-2 bg-background/85 px-1.5 py-0.5 text-[0.55rem] uppercase tracking-[0.12em] text-muted-foreground">
          Placeholder image
        </span>
      ) : null}
    </div>
  );
}
