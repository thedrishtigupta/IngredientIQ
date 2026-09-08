import { Link } from "@tanstack/react-router";
import { useState } from "react";
import { useCompare } from "@/lib/compare-store";

const links = [
  { to: "/explore", label: "Explore" },
  { to: "/ingredients", label: "Ingredients" },
  { to: "/compare", label: "Compare" },
  { to: "/research", label: "Research" },
] as const;

export function Navbar() {
  const [open, setOpen] = useState(false);
  const { ids } = useCompare();

  return (
    <header className="sticky top-0 z-40 border-b border-border bg-background/85 backdrop-blur-sm">
      <div className="mx-auto flex h-16 max-w-[1220px] items-center justify-between px-5 sm:px-8">
        <Link to="/" className="flex items-baseline gap-2" onClick={() => setOpen(false)}>
          <span className="display text-[1.35rem] leading-none">IngredientIQ</span>
          <span className="hidden text-[0.6rem] uppercase tracking-[0.18em] text-muted-foreground sm:inline">
            Ingredient-aware discovery
          </span>
        </Link>

        <nav className="hidden items-center gap-8 md:flex">
          {links.map((l) => (
            <Link
              key={l.to}
              to={l.to}
              className="link-underline text-sm text-foreground/80 hover:text-foreground"
              activeProps={{ className: "text-foreground font-medium" }}
            >
              {l.label}
              {l.to === "/compare" && ids.length > 0 ? (
                <span className="numeric ml-1 text-[0.7rem] text-accent">({ids.length})</span>
              ) : null}
            </Link>
          ))}
          <Link
            to="/explore"
            className="border border-foreground px-4 py-2 text-xs uppercase tracking-[0.14em] text-foreground transition-colors hover:bg-foreground hover:text-background"
          >
            Search
          </Link>
        </nav>

        <button
          type="button"
          aria-label="Menu"
          aria-expanded={open}
          onClick={() => setOpen((v) => !v)}
          className="flex h-9 w-9 flex-col items-center justify-center gap-[5px] md:hidden"
        >
          <span
            className={`h-px w-5 bg-foreground transition-transform ${open ? "translate-y-[3px] rotate-45" : ""}`}
          />
          <span
            className={`h-px w-5 bg-foreground transition-transform ${open ? "-translate-y-[3px] -rotate-45" : ""}`}
          />
        </button>
      </div>

      {open ? (
        <nav className="border-t border-border bg-paper md:hidden">
          {links.map((l) => (
            <Link
              key={l.to}
              to={l.to}
              onClick={() => setOpen(false)}
              className="block border-b border-border px-5 py-4 text-sm"
            >
              {l.label}
            </Link>
          ))}
        </nav>
      ) : null}
    </header>
  );
}
