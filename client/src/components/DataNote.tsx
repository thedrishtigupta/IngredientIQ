import { useHealth } from "@/lib/api";
import { fmtInt } from "@/lib/labels";

/** One sentence about the data, with the real numbers from GET /health. */
export function DataNote() {
  const { data } = useHealth();
  if (!data || data.status !== "ok") {
    return <>Sephora product and review dataset, served by the project API.</>;
  }
  return (
    <>
      Sephora dataset: {fmtInt(data.products)} products and {fmtInt(data.reviews)} reviews. The
      reviews cover {fmtInt(data.reviewed_products)} of those products, so review signals exist only
      for that reviewed subset.
    </>
  );
}
