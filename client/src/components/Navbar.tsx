import { Link } from "@tanstack/react-router";
import { useState } from "react";
import { useAuth } from "@/lib/api";
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
  const { user, loading } = useAuth();
  // Short label for the account link: the user's first name, or "Sign in".
  const accountLabel = user ? (user.display_name.split(/\s+/)[0] ?? "Account") : "Sign in";

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
          <Link
            to={user ? "/account" : "/login"}
            className={`flex items-center gap-2 text-sm text-foreground/80 hover:text-foreground ${loading ? "invisible" : ""}`}
            activeProps={{ className: "text-foreground font-medium" }}
          >
            <span
              aria-hidden="true"
              className="flex h-7 w-7 items-center justify-center rounded-full border border-border-strong text-[0.7rem] uppercase"
            >
              {user ? user.display_name.charAt(0) : (
                <svg viewBox="0 0 24 24" className="h-3.5 w-3.5" fill="none" stroke="currentColor" strokeWidth="1.5">
                  <circle cx="12" cy="8" r="4" />
                  <path d="M4 21c1.5-4 4.5-6 8-6s6.5 2 8 6" strokeLinecap="round" />
                </svg>
              )}
            </span>
            <span className="hidden max-w-[9rem] truncate lg:inline">{accountLabel}</span>
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
          <Link
            to={user ? "/account" : "/login"}
            onClick={() => setOpen(false)}
            className="block border-b border-border px-5 py-4 text-sm"
          >
            {user ? `My account (${accountLabel})` : "Sign in"}
          </Link>
        </nav>
      ) : null}
    </header>
  );
}
