import { Link } from "@tanstack/react-router";
import { DataNote } from "./DataNote";
import { Logo } from "./Navbar";

export function Footer() {
  return (
    <footer className="ink-band mt-28 overflow-hidden pb-[env(safe-area-inset-bottom)]">
      <div className="mx-auto max-w-[1280px] px-5 pt-20 sm:px-8">
        <div className="flex flex-wrap items-end justify-between gap-8 border-b border-white/10 pb-14">
          <h2 className="display max-w-2xl text-4xl sm:text-5xl">
            Beauty, read by its <em className="text-gilded">ingredients</em>.
          </h2>
          <Link to="/explore" className="btn btn-gold">
            Start exploring <span aria-hidden="true" className="arrow">→</span>
          </Link>
        </div>

        <div className="grid gap-12 py-14 md:grid-cols-[1.4fr_1fr_1fr]">
          <div>
            <Logo light />
            <p className="mt-5 max-w-sm text-sm leading-relaxed text-ink-foreground/60">
              An explainable, ingredient-aware discovery and recommendation system. Rankings are
              computed from ingredient composition, review-derived signals, rating and popularity.
              A language model, when one is configured, only words the explanation — it does not
              pick products.
            </p>
          </div>
          <div className="text-sm">
            <p className="text-[0.68rem] uppercase tracking-[0.22em] text-gold/80">Sections</p>
            <ul className="mt-5 space-y-1 text-ink-foreground/70">
              {(
                [
                  ["/explore", "Explore"],
                  ["/ingredients", "Ingredients"],
                  ["/compare", "Compare"],
                  ["/research", "Research"],
                ] as const
              ).map(([to, label]) => (
                <li key={to}>
                  <Link to={to} className="link-underline inline-block py-1.5 transition-colors duration-150 hover:text-ink-foreground">
                    {label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>
          <div className="text-sm text-ink-foreground/60">
            <p className="text-[0.68rem] uppercase tracking-[0.22em] text-gold/80">Scope</p>
            <p className="mt-5 leading-relaxed">
              Non-medical. Findings are associational, not causal, and nothing here is diagnostic
              or dermatological advice.
            </p>
            <p className="mt-4 leading-relaxed">
              <DataNote />
            </p>
          </div>
        </div>
      </div>
      <div className="border-t border-white/10">
        <div className="mx-auto flex max-w-[1280px] flex-wrap items-center justify-between gap-3 px-5 py-6 text-xs text-ink-foreground/45 sm:px-8">
          <p>Minor project — Department of Information Technology, BPIT.</p>
          <p className="tracking-[0.18em] uppercase">Evidence over opinion</p>
        </div>
      </div>
    </footer>
  );
}
