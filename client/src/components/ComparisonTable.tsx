import { Link } from "@tanstack/react-router";
import { mainIngredients, type ProductDetail } from "@/lib/api";
import { fmtInt, fmtPrice, fmtRating, groupLabel, pct } from "@/lib/labels";
import { ProductImage } from "./ProductImage";

type Row = {
  label: string;
  render: (p: ProductDetail) => string;
  /** Higher is better; the best value in a numeric row gets an accent underline. */
  numeric?: (p: ProductDetail) => number;
};

const groupsOf = (p: ProductDetail) => [...new Set(mainIngredients(p).flatMap((i) => i.functional_groups))];
const fragranceOf = (p: ProductDetail) =>
  mainIngredients(p)
    .filter((i) => i.functional_groups.includes("fragrance_component"))
    .map((i) => i.name);

const rows: Row[] = [
  { label: "Price", render: (p) => fmtPrice(p.price), numeric: (p) => -(p.price ?? Infinity) },
  { label: "Rating", render: (p) => `${fmtRating(p.rating)} / 5`, numeric: (p) => p.rating ?? 0 },
  { label: "Review count", render: (p) => fmtInt(p.review_count ?? 0), numeric: (p) => p.review_count ?? 0 },
  { label: "Popularity (loves)", render: (p) => fmtInt(p.loves_count ?? 0), numeric: (p) => p.loves_count ?? 0 },
  { label: "Ingredients listed", render: (p) => String(mainIngredients(p).length) },
  {
    label: "Functional groups",
    render: (p) => groupsOf(p).map(groupLabel).join(", ") || "None mapped",
  },
  {
    label: "Fragrance-related",
    render: (p) => {
      const hits = fragranceOf(p);
      if (!hits.length) return "None detected";
      return hits.slice(0, 4).join(", ") + (hits.length > 4 ? ` +${hits.length - 4} more` : "");
    },
  },
  {
    label: "Review sentiment",
    render: (p) =>
      p.review_signals?.positive_share != null
        ? `${pct(p.review_signals.positive_share)} positive`
        : "No review data",
    numeric: (p) => p.review_signals?.positive_share ?? -1,
  },
  {
    label: "Would recommend",
    render: (p) =>
      p.review_summary?.recommendation_rate != null ? pct(p.review_summary.recommendation_rate) : "No review data",
    numeric: (p) => p.review_summary?.recommendation_rate ?? -1,
  },
];

export function ComparisonTable({
  products,
  onRemove,
}: {
  products: ProductDetail[];
  onRemove: (id: string) => void;
}) {
  return (
    <div className="-mx-5 overflow-x-auto px-5 sm:mx-0 sm:px-0">
      <table className="w-full min-w-[640px] border-collapse text-sm">
        <thead>
          <tr>
            <th className="w-40 border-b border-border py-4 text-left align-bottom">
              <span className="eyebrow">Attribute</span>
            </th>
            {products.map((p) => (
              <th key={p.product_id} className="border-b border-border py-4 pl-6 text-left align-bottom">
                <div className="mb-3 w-24">
                  <ProductImage id={p.product_id} alt={p.product_name} tag={false} />
                </div>
                <p className="text-[0.68rem] uppercase tracking-[0.12em] text-muted-foreground">{p.brand}</p>
                <Link
                  to="/product/$productId"
                  params={{ productId: p.product_id }}
                  className="link-underline font-normal"
                >
                  {p.product_name}
                </Link>
                <button
                  type="button"
                  onClick={() => onRemove(p.product_id)}
                  className="mt-2 block text-xs font-normal text-muted-foreground hover:text-foreground"
                >
                  Remove
                </button>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => {
            const values = row.numeric ? products.map(row.numeric) : null;
            const best = values ? Math.max(...values) : null;
            return (
              <tr key={row.label}>
                <th className="border-b border-border py-4 pr-4 text-left align-top font-normal text-muted-foreground">
                  {row.label}
                </th>
                {products.map((p, i) => {
                  const isBest = values !== null && values[i] === best && new Set(values).size > 1;
                  return (
                    <td
                      key={p.product_id}
                      className={`border-b border-border py-4 pl-6 align-top ${
                        isBest ? "text-foreground" : "text-muted-foreground"
                      }`}
                    >
                      <span className={isBest ? "border-b border-accent pb-0.5" : ""}>{row.render(p)}</span>
                    </td>
                  );
                })}
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
