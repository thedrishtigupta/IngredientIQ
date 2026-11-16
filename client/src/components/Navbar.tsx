import { Link, useRouterState } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { useAuth } from "@/lib/api";
import { useCompare } from "@/lib/compare-store";

const links = [
  { to: "/explore", label: "Explore" },
  { to: "/ingredients", label: "Ingredients" },
  { to: "/compare", label: "Compare" },
  { to: "/research", label: "Research" },
] as const;

export function Logo({ light = false }: { light?: boolean }) {
  return (
    <span className="flex items-center gap-2.5">
      <span
        aria-hidden="true"
        className={`flex h-8 w-8 items-center justify-center rounded-full border ${
          light ? "border-gold/50 text-gold" : "border-accent/40 text-accent"
        }`}
      >
        <span className="display text-[1.05rem] italic leading-none">iq</span>
      </span>
      <span className="display text-[1.4rem] leading-none tracking-tight">
        Ingredient<span className={light ? "text-gold" : "text-accent"}>IQ</span>
      </span>
    </span>
  );
}

export function Navbar() {
  const [open, setOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);
  const { ids } = useCompare();
  const { user, loading } = useAuth();
  // Short label for the account link: the user's first name, or "Sign in".
  const accountLabel = user ? (user.display_name.split(/\s+/)[0] ?? "Account") : "Sign in";

  const pathname = useRouterState({ select: (s) => s.location.pathname });
  // Close the mobile menu after any navigation, and on Escape.
  useEffect(() => setOpen(false), [pathname]);
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        setOpen(false);
        document.getElementById("menu-toggle")?.focus();
      }
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [open]);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 8);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <header
      className={`glass sticky top-0 z-40 border-b transition-[border-color,box-shadow] duration-300 ${
        scrolled ? "border-border shadow-[0_8px_30px_-20px_rgba(40,25,10,0.35)]" : "border-transparent"
      }`}
    >
      <div className="mx-auto flex h-[4.5rem] max-w-[1280px] items-center justify-between gap-6 px-5 sm:px-8">
        <Link to="/" aria-label="IngredientIQ home" onClick={() => setOpen(false)}>
          <Logo />
        </Link>

        <nav aria-label="Main" className="hidden items-center rounded-full border border-border bg-paper/70 p-1 shadow-[var(--shadow-soft)] md:flex">
          {links.map((l) => (
            <Link
              key={l.to}
              to={l.to}
              className="rounded-full px-4 py-1.5 text-[0.82rem] text-foreground/70 transition-colors duration-150 hover:bg-muted/70 hover:text-foreground"
              activeProps={{ className: "bg-foreground !text-background" }}
            >
              {l.label}
              {l.to === "/compare" && ids.length > 0 ? (
                <span className="numeric ml-1.5 inline-flex h-4 min-w-4 items-center justify-center rounded-full bg-accent px-1 text-[0.6rem] text-accent-foreground">
                  {ids.length}
                </span>
              ) : null}
            </Link>
          ))}
        </nav>

        <div className="hidden items-center gap-3 md:flex">
          <Link
            to={user ? "/account" : "/login"}
            className={`flex items-center gap-2.5 rounded-full py-1 pl-1 pr-3 text-sm text-foreground/80 transition-colors hover:bg-muted hover:text-foreground ${loading ? "invisible" : ""}`}
            activeProps={{ className: "text-foreground" }}
          >
            <span
              aria-hidden="true"
              className={`flex h-8 w-8 items-center justify-center rounded-full text-[0.75rem] uppercase ${
                user ? "bg-gradient-to-br from-gold to-accent text-ink" : "border border-border-strong"
              }`}
            >
              {user && user.display_name.trim() ? (
                user.display_name.trim().charAt(0)
              ) : (
                <svg viewBox="0 0 24 24" className="h-3.5 w-3.5" fill="none" stroke="currentColor" strokeWidth="1.5">
                  <circle cx="12" cy="8" r="4" />
                  <path d="M4 21c1.5-4 4.5-6 8-6s6.5 2 8 6" strokeLinecap="round" />
                </svg>
              )}
            </span>
            <span className="hidden max-w-[9rem] truncate lg:inline">{accountLabel}</span>
          </Link>
          <Link to="/explore" className="btn btn-primary btn-sm">
            Find products
          </Link>
        </div>

        <button
          type="button"
          id="menu-toggle"
          aria-label={open ? "Close menu" : "Open menu"}
          aria-expanded={open}
          aria-controls="mobile-nav"
          onClick={() => setOpen((v) => !v)}
          className="flex h-11 w-11 flex-col items-center justify-center gap-[5px] rounded-full border border-border transition-colors duration-150 active:bg-muted md:hidden"
        >
          <span
            className={`h-px w-4 bg-foreground transition-transform ${open ? "translate-y-[3px] rotate-45" : ""}`}
          />
          <span
            className={`h-px w-4 bg-foreground transition-transform ${open ? "-translate-y-[3px] -rotate-45" : ""}`}
          />
        </button>
      </div>

      {open ? (
        <nav id="mobile-nav" aria-label="Main" className="rise max-h-[calc(100dvh-4.5rem)] overflow-y-auto overscroll-contain border-t border-border bg-paper px-5 pb-[max(1.5rem,env(safe-area-inset-bottom))] pt-2 md:hidden">
          {links.map((l) => (
            <Link
              key={l.to}
              to={l.to}
              onClick={() => setOpen(false)}
              className="display flex items-center justify-between border-b border-border py-4 text-2xl"
              activeProps={{ "aria-current": "page", className: "text-accent" }}
            >
              {l.label}
              <span aria-hidden className="text-base text-muted-foreground">→</span>
            </Link>
          ))}
          <Link
            to={user ? "/account" : "/login"}
            onClick={() => setOpen(false)}
            className="btn btn-primary mt-6 w-full"
          >
            {user ? `My account · ${accountLabel}` : "Sign in"}
          </Link>
        </nav>
      ) : null}
    </header>
  );
}
