import { Link } from "@tanstack/react-router";
import { DataNote } from "./DataNote";

export function Footer() {
  return (
    <footer className="mt-24 border-t border-border">
      <div className="mx-auto grid max-w-[1220px] gap-10 px-5 py-14 sm:px-8 md:grid-cols-[1.4fr_1fr_1fr]">
        <div>
          <p className="display text-2xl">IngredientIQ</p>
          <p className="mt-3 max-w-sm text-sm leading-relaxed text-muted-foreground">
            An explainable, ingredient-aware discovery and recommendation system. Rankings are
            computed from ingredient composition, review-derived signals, rating and popularity.
            A language model, when one is configured, only words the explanation — it does not pick
            products.
          </p>
        </div>
        <div className="text-sm">
          <p className="eyebrow">Sections</p>
          <ul className="mt-4 space-y-2 text-muted-foreground">
            <li><Link to="/explore" className="link-underline">Explore</Link></li>
            <li><Link to="/ingredients" className="link-underline">Ingredients</Link></li>
            <li><Link to="/compare" className="link-underline">Compare</Link></li>
            <li><Link to="/research" className="link-underline">Research</Link></li>
          </ul>
        </div>
        <div className="text-sm text-muted-foreground">
          <p className="eyebrow">Scope</p>
          <p className="mt-4 leading-relaxed">
            Non-medical. Findings are associational, not causal, and nothing here is diagnostic or
            dermatological advice.
          </p>
          <p className="mt-4 leading-relaxed"><DataNote /></p>
        </div>
      </div>
      <div className="border-t border-border">
        <p className="mx-auto max-w-[1220px] px-5 py-5 text-xs text-muted-foreground sm:px-8">
          Minor project — Department of Information Technology, BPIT.
        </p>
      </div>
    </footer>
  );
}
