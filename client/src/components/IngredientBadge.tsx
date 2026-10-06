import { groupLabel } from "@/lib/labels";

// Only a few groups get a colour; every other group id falls back to the neutral style.
const tone: Record<string, string> = {
  humectant: "border-olive/40 text-olive",
  botanical: "border-olive/40 text-olive",
  uv_filter: "border-olive/40 text-olive",
  antioxidant: "border-accent/40 text-accent",
  exfoliant: "border-accent/40 text-accent",
  aha: "border-accent/40 text-accent",
  bha: "border-accent/40 text-accent",
};

export function IngredientBadge({
  label,
  group,
  onClick,
  active,
}: {
  label?: string;
  /** Functional group id; used for the colour and as the label when none is given. */
  group?: string;
  onClick?: () => void;
  active?: boolean;
}) {
  const cls = `inline-flex items-center border px-2.5 py-1 text-[0.68rem] uppercase tracking-[0.1em] transition-colors ${
    (group && tone[group]) || "border-border-strong text-muted-foreground"
  } ${active ? "bg-foreground text-background border-foreground" : ""} ${
    onClick ? "hover:border-foreground hover:text-foreground" : ""
  }`;
  const text = label ?? (group ? groupLabel(group) : "");

  if (onClick) {
    return (
      <button type="button" onClick={onClick} className={cls}>
        {text}
      </button>
    );
  }
  return <span className={cls}>{text}</span>;
}
