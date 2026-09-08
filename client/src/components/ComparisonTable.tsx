import { Link } from "@tanstack/react-router";
import { groupLabel, groupsOf, ingredientByName, type Product } from "@/lib/data";
import { scoreProduct, type Requirements } from "@/lib/scoring";

type Row = {
  label: string;
  render: (p: Product) => string;
  best?: (values: number[]) => number;
  numeric?: (p: Product) => number;
};

export function ComparisonTable({
  products,
  req,
  onRemove,
}: {
  products: Product[];
  req: Requirements;
  onRemove: (id: string) => void;
}) {
  const scored = products.map((p) => scoreProduct(p, req));

  const rows: Row[] = [
    { label: "Price", render: (p) => `$${p.price}`, numeric: (p) => -p.price },
    { label: "Rating", render: (p) => `${p.rating.toFixed(1)} / 5`, numeric: (p) => p.rating },
    {
      label: "Review count",
      render: (p) => p.reviewCount.toLocaleString(),
      numeric: (p) => p.reviewCount,
    },
    { label: "Popularity (loves)", render: (p) => p.loves.toLocaleString(), numeric: (p) => p.loves },
    {
      label: "Functional groups",
      render: (p) => groupsOf(p).map(groupLabel).join(", "),
    },
    {
      label: "Fragrance-related",
      render: (p) => {
        const hits = p.ingredients.filter((i) => ingredientByName(i)?.group === "fragrance");
        return hits.length ? hits.join(", ") : "None detected";
      },
    },
    {
      label: "Review sentiment",
      render: (p) =>
        p.reviewAspects
          ? `${Math.round(
              (p.reviewAspects.reduce((s, a) => s + a.positiveShare * a.mentions, 0) /
                p.reviewAspects.reduce((s, a) => s + a.mentions, 0)) *
                100,
            )}% positive`
          : "No review coverage",
    },
    {
      label: "Ingredient match",
      render: (p) => {
        const s = scored.find((x) => x.product.id === p.id)!;
        const v = s.signals.find((x) => x.key === "ingredient")!.value;
        return v === null ? "No requirement set" : v.toFixed(2);
      },
    },
    {
      label: "Recommendation score",
      render: (p) => scored.find((x) => x.product.id === p.id)!.score.toFixed(2),
      numeric: (p) => scored.find((x) => x.product.id === p.id)!.score,
    },
  ];

  return (
    <div className="-mx-5 overflow-x-auto px-5 sm:mx-0 sm:px-0">
      <table className="w-full min-w-[640px] border-collapse text-sm">
        <thead>
          <tr>
            <th className="w-40 border-b border-border py-4 text-left align-bottom">
              <span className="eyebrow">Attribute</span>
            </th>
            {products.map((p) => (
              <th key={p.id} className="border-b border-border py-4 pl-6 text-left align-bottom">
                <img
                  src={p.image}
                  alt={p.name}
                  width={900}
                  height={1100}
                  loading="lazy"
                  className="mb-3 aspect-[4/5] w-24 object-cover"
                />
                <p className="text-[0.68rem] uppercase tracking-[0.12em] text-muted-foreground">
                  {p.brand}
                </p>
                <Link
                  to="/product/$productId"
                  params={{ productId: p.id }}
                  className="link-underline font-normal"
                >
                  {p.name}
                </Link>
                <button
                  type="button"
                  onClick={() => onRemove(p.id)}
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
                  const isBest =
                    values !== null && best !== null && values[i] === best && new Set(values).size > 1;
                  return (
                    <td
                      key={p.id}
                      className={`border-b border-border py-4 pl-6 align-top ${
                        isBest ? "text-foreground" : "text-muted-foreground"
                      }`}
                    >
                      <span className={isBest ? "border-b border-accent pb-0.5" : ""}>
                        {row.render(p)}
                      </span>
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
