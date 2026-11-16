import { groupLabel } from "@/lib/labels";

// Only a few groups get a colour; every other group id falls back to the neutral style.
const tone: Record<string, string> = {
  humectant: "border-olive/30 bg-olive/5 text-olive",
  botanical: "border-olive/30 bg-olive/5 text-olive",
  uv_filter: "border-olive/30 bg-olive/5 text-olive",
  antioxidant: "border-accent/30 bg-accent/5 text-accent",
  exfoliant: "border-accent/30 bg-accent/5 text-accent",
  aha: "border-accent/30 bg-accent/5 text-accent",
  bha: "border-accent/30 bg-accent/5 text-accent",
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
  // `active` replaces the tone instead of competing with it, so the result never depends on CSS order.
  const look = active
    ? "border-foreground bg-foreground text-background"
    : (group && tone[group]) || "border-border bg-paper/70 text-muted-foreground";
  const cls = `inline-flex max-w-full items-center break-words rounded-full border px-3 py-1 text-[0.64rem] uppercase tracking-[0.12em] transition-colors duration-150 ${look} ${
    onClick && !active ? "hover:border-foreground hover:text-foreground" : ""
  }`;
  const text = label ?? (group ? groupLabel(group) : "");

  if (onClick) {
    return (
      <button type="button" onClick={onClick} aria-pressed={!!active} className={cls}>
        {text}
      </button>
    );
  }
  return <span className={cls}>{text}</span>;
}
