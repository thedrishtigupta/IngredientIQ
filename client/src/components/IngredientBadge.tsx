import type { FunctionGroup } from "@/lib/data";

const tone: Record<FunctionGroup, string> = {
  humectant: "border-olive/40 text-olive",
  emollient: "border-border-strong text-muted-foreground",
  occlusive: "border-border-strong text-muted-foreground",
  antioxidant: "border-accent/40 text-accent",
  exfoliant: "border-accent/40 text-accent",
  "uv-filter": "border-olive/40 text-olive",
  soothing: "border-olive/40 text-olive",
  fragrance: "border-border-strong text-muted-foreground",
};

export function IngredientBadge({
  label,
  group,
  onClick,
  active,
}: {
  label: string;
  group?: FunctionGroup;
  onClick?: () => void;
  active?: boolean;
}) {
  const cls = `inline-flex items-center border px-2.5 py-1 text-[0.68rem] uppercase tracking-[0.1em] transition-colors ${
    group ? tone[group] : "border-border-strong text-muted-foreground"
  } ${active ? "bg-foreground text-background border-foreground" : ""} ${
    onClick ? "hover:border-foreground hover:text-foreground" : ""
  }`;

  if (onClick) {
    return (
      <button type="button" onClick={onClick} className={cls}>
        {label}
      </button>
    );
  }
  return <span className={cls}>{label}</span>;
}
