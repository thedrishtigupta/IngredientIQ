import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { formatDistanceToNow } from "date-fns";
import { useEffect, useState } from "react";
import { ErrorNotice } from "@/components/ErrorNotice";
import { ProductCard } from "@/components/ProductCard";
import {
  SKIN_TYPES,
  useAuth,
  useCategories,
  useDeleteHistory,
  useForYou,
  useGoals,
  useHistory,
  useSaved,
  useSignOut,
  useUpdateProfile,
  type HistoryItem,
  type Me,
  type Profile,
} from "@/lib/api";
import { humanize } from "@/lib/labels";

const TABS = [
  { id: "for-you", label: "For you" },
  { id: "history", label: "Search history" },
  { id: "saved", label: "Saved" },
  { id: "profile", label: "Profile" },
] as const;
type Tab = (typeof TABS)[number]["id"];

export const Route = createFileRoute("/account")({
  validateSearch: (s: Record<string, unknown>): { tab?: Tab | undefined } => ({
    tab: TABS.some((t) => t.id === s["tab"]) ? (s["tab"] as Tab) : undefined,
  }),
  head: () => ({ meta: [{ title: "My account — IngredientIQ" }] }),
  component: Account,
});

function Account() {
  const { user, loading, error } = useAuth();
  const { tab = "for-you" } = Route.useSearch();
  const signOut = useSignOut();
  const navigate = useNavigate();

  if (loading) {
    return <div className="mx-auto max-w-[1220px] px-5 py-24 text-sm text-muted-foreground sm:px-8">Loading…</div>;
  }
  if (!user) {
    return (
      <div className="mx-auto max-w-[1220px] px-5 py-16 sm:px-8">
        {error ? (
          <ErrorNotice error={error} />
        ) : (
          <div className="max-w-lg">
            <p className="eyebrow">My account</p>
            <h1 className="display mt-4 text-4xl">Sign in to see your profile</h1>
            <p className="mt-3 text-sm leading-relaxed text-muted-foreground">
              Your search history, saved products and recommendations based on your skin profile live here.
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <Link
                to="/login"
                search={{ redirect: "/account" }}
                className="border border-foreground bg-foreground px-6 py-3 text-xs uppercase tracking-[0.14em] text-background hover:opacity-85"
              >
                Sign in
              </Link>
              <Link
                to="/login"
                search={{ mode: "register", redirect: "/account" }}
                className="border border-foreground px-6 py-3 text-xs uppercase tracking-[0.14em] hover:bg-foreground hover:text-background"
              >
                Create account
              </Link>
            </div>
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-[1220px] px-5 py-12 sm:px-8">
      <div className="flex flex-wrap items-end justify-between gap-6">
        <div>
          <p className="eyebrow">My account</p>
          <h1 className="display mt-4 text-4xl sm:text-5xl">Hello, {user.display_name}</h1>
          <p className="mt-2 text-sm text-muted-foreground">
            {user.email}
            {user.profile.skin_type ? ` · ${humanize(user.profile.skin_type)} skin` : ""}
          </p>
        </div>
        <button
          type="button"
          onClick={() => signOut.mutate(undefined, { onSettled: () => void navigate({ to: "/" }) })}
          className="link-underline text-xs uppercase tracking-[0.14em] text-muted-foreground hover:text-foreground"
        >
          Sign out
        </button>
      </div>

      <nav className="mt-10 flex gap-6 overflow-x-auto border-b border-border" aria-label="Account sections">
        {TABS.map((t) => (
          <Link
            key={t.id}
            to="/account"
            search={{ tab: t.id === "for-you" ? undefined : t.id }}
            replace
            aria-current={tab === t.id ? "page" : undefined}
            className={`-mb-px shrink-0 whitespace-nowrap border-b-2 pb-3 text-sm transition-colors ${
              tab === t.id
                ? "border-foreground text-foreground"
                : "border-transparent text-muted-foreground hover:text-foreground"
            }`}
          >
            {t.label}
          </Link>
        ))}
      </nav>

      <div className="pt-10">
        {tab === "for-you" ? <ForYou user={user} /> : null}
        {tab === "history" ? <History /> : null}
        {tab === "saved" ? <Saved /> : null}
        {tab === "profile" ? <ProfileForm user={user} /> : null}
      </div>
    </div>
  );
}

// ---------- For you ----------

const profileIsEmpty = (p: Profile) =>
  !p.goals.length && !p.max_price && !p.preferred_category && !p.avoided_ingredients.length && !p.fragrance_free;

function ForYou({ user }: { user: Me }) {
  const rec = useForYou(8);
  const p = user.profile;

  return (
    <section>
      {profileIsEmpty(p) ? (
        <Notice
          title="Tell us about your skin"
          text="Add your skin type, goals and ingredients to avoid, and this page will rank products for you. Until then it shows the best-rated, most-loved products."
          action={{ label: "Set up profile", tab: "profile" }}
        />
      ) : (
        <p className="max-w-2xl text-sm leading-relaxed text-muted-foreground">
          Ranked for{" "}
          <span className="text-foreground">
            {p.goals.length ? p.goals.map(humanize).join(", ") : "any goal"}
          </span>
          {p.preferred_category ? ` in ${p.preferred_category}` : ""}
          {p.max_price ? `, under $${p.max_price}` : ""}
          {p.fragrance_free ? ", fragrance-free" : ""}
          {p.avoided_ingredients.filter((x) => x !== "fragrance").length
            ? `, without ${p.avoided_ingredients.filter((x) => x !== "fragrance").join(", ")}`
            : ""}
          .{" "}
          <Link to="/account" search={{ tab: "profile" }} className="link-underline text-foreground">
            Edit profile
          </Link>
        </p>
      )}

      <div className="mt-10">
        {rec.isPending ? (
          <p className="text-sm text-muted-foreground">Finding products for you…</p>
        ) : rec.error ? (
          <ErrorNotice error={rec.error} />
        ) : !rec.data.results.length ? (
          <Notice
            title="Nothing matches your profile yet"
            text="Your budget or ingredient rules rule out every product. Loosen them in your profile."
            action={{ label: "Edit profile", tab: "profile" }}
          />
        ) : (
          <div className="grid grid-cols-2 gap-x-5 gap-y-12 sm:gap-x-8 lg:grid-cols-4">
            {rec.data.results.map((r, i) => (
              <ProductCard key={r.product_id} product={r} index={i} rank={i + 1} tags={r.matched_goals.map(humanize)} />
            ))}
          </div>
        )}
      </div>
    </section>
  );
}

// ---------- History ----------

function History() {
  const history = useHistory(100);
  const del = useDeleteHistory();

  if (history.isPending) return <p className="text-sm text-muted-foreground">Loading your searches…</p>;
  if (history.error) return <ErrorNotice error={history.error} />;
  if (!history.data.length) {
    return (
      <Notice
        title="No searches yet"
        text="Searches you run while signed in, by name or by goals and filters, appear here so you can run them again."
        action={{ label: "Start searching", to: "/explore" }}
      />
    );
  }

  return (
    <section>
      <div className="flex flex-wrap items-baseline justify-between gap-3">
        <p className="numeric text-xs text-muted-foreground">
          {history.data.length} {history.data.length === 1 ? "search" : "searches"} · newest first
        </p>
        <button
          type="button"
          disabled={del.isPending}
          onClick={() => {
            if (window.confirm("Delete your whole search history?")) del.mutate(null);
          }}
          className="link-underline text-xs uppercase tracking-[0.12em] text-muted-foreground hover:text-foreground disabled:opacity-50"
        >
          Clear history
        </button>
      </div>
      <ul className="mt-6 divide-y divide-border border-y border-border">
        {history.data.map((h) => (
          <HistoryRow key={h.search_id} item={h} onDelete={() => del.mutate(h.search_id)} />
        ))}
      </ul>
    </section>
  );
}

function HistoryRow({ item, onDelete }: { item: HistoryItem; onDelete: () => void }) {
  const when = formatDistanceToNow(new Date(item.created_at), { addSuffix: true });
  const again =
    item.kind === "text" ? (
      <Link to="/explore" search={{ q: item.query }} className="link-underline text-xs uppercase tracking-[0.12em]">
        Search again
      </Link>
    ) : (
      <Link to="/explore" search={{ run: item.params }} className="link-underline text-xs uppercase tracking-[0.12em]">
        Run again
      </Link>
    );

  return (
    <li className="flex flex-wrap items-center gap-x-6 gap-y-2 py-4">
      <span className="eyebrow w-20 shrink-0">{item.kind === "text" ? "Search" : "Goals"}</span>
      <div className="min-w-0 flex-1">
        <p className="truncate text-sm text-foreground">{item.query}</p>
        <p className="numeric mt-0.5 text-xs text-muted-foreground">
          {item.result_count} {item.result_count === 1 ? "result" : "results"} · {when}
        </p>
      </div>
      <div className="flex items-center gap-5">
        {again}
        <button
          type="button"
          onClick={onDelete}
          aria-label={`Delete "${item.query}" from history`}
          className="text-lg leading-none text-muted-foreground hover:text-foreground"
        >
          ×
        </button>
      </div>
    </li>
  );
}

// ---------- Saved ----------

function Saved() {
  const saved = useSaved();
  if (saved.isPending) return <p className="text-sm text-muted-foreground">Loading saved products…</p>;
  if (saved.error) return <ErrorNotice error={saved.error} />;
  if (!saved.data.length) {
    return (
      <Notice
        title="No saved products"
        text="Press the heart on any product to keep it here."
        action={{ label: "Explore products", to: "/explore" }}
      />
    );
  }
  return (
    <div className="grid grid-cols-2 gap-x-5 gap-y-12 sm:gap-x-8 lg:grid-cols-4">
      {saved.data.map((p, i) => (
        <ProductCard key={p.product_id} product={p} index={i} />
      ))}
    </div>
  );
}

// ---------- Profile ----------

/** Starting points per skin type: a suggestion the user can accept, not advice. */
const SUGGESTED_GOALS: Record<string, string[]> = {
  dry: ["hydration", "moisturization", "barrier_support"],
  oily: ["oil_control", "cleansing", "exfoliation"],
  combination: ["hydration", "oil_control"],
  normal: ["antioxidant", "uv_protection"],
  sensitive: ["soothing", "barrier_support"],
};

const chip = (active: boolean) =>
  `border px-3 py-1.5 text-xs transition-colors ${
    active
      ? "border-foreground bg-foreground text-background"
      : "border-border text-muted-foreground hover:border-foreground hover:text-foreground"
  }`;

const toggle = <T,>(arr: T[], v: T) => (arr.includes(v) ? arr.filter((x) => x !== v) : [...arr, v]);

function ProfileForm({ user }: { user: Me }) {
  const goals = useGoals();
  const categories = useCategories();
  const update = useUpdateProfile();

  const [p, setP] = useState<Profile>(user.profile);
  const [avoid, setAvoid] = useState(user.profile.avoided_ingredients.join(", "));
  const [savedAt, setSavedAt] = useState<number | null>(null);
  useEffect(() => setSavedAt(null), [p, avoid]); // any edit hides "Saved"

  const suggestions = p.skin_type ? (SUGGESTED_GOALS[p.skin_type] ?? []) : [];
  const missing = suggestions.filter((g) => !p.goals.includes(g));

  const submit = () => {
    const avoided = avoid
      .split(",")
      .map((x) => x.trim())
      .filter(Boolean);
    update.mutate({ ...p, avoided_ingredients: avoided }, { onSuccess: () => setSavedAt(Date.now()) });
  };

  return (
    <form
      className="grid max-w-3xl gap-10"
      onSubmit={(e) => {
        e.preventDefault();
        submit();
      }}
    >
      <section>
        <p className="eyebrow">Skin type</p>
        <div className="mt-3 flex flex-wrap gap-1.5">
          {SKIN_TYPES.map((s) => (
            <button
              key={s}
              type="button"
              aria-pressed={p.skin_type === s}
              onClick={() => setP({ ...p, skin_type: p.skin_type === s ? null : s })}
              className={chip(p.skin_type === s)}
            >
              {humanize(s)}
            </button>
          ))}
        </div>
        {missing.length ? (
          <p className="mt-3 text-xs text-muted-foreground">
            Common goals for {p.skin_type} skin: {missing.map(humanize).join(", ")}.{" "}
            <button
              type="button"
              onClick={() =>
                setP({
                  ...p,
                  goals: [...p.goals, ...missing],
                  fragrance_free: p.fragrance_free || p.skin_type === "sensitive",
                })
              }
              className="link-underline text-foreground"
            >
              Add {missing.length === 1 ? "it" : "them"}
              {p.skin_type === "sensitive" && !p.fragrance_free ? " and go fragrance-free" : ""}
            </button>
          </p>
        ) : null}
      </section>

      <section>
        <p className="eyebrow">Goals</p>
        <div className="mt-3 flex flex-wrap gap-1.5">
          {goals.data ? (
            goals.data.map((g) => (
              <button
                key={g.id}
                type="button"
                aria-pressed={p.goals.includes(g.id)}
                onClick={() => setP({ ...p, goals: toggle(p.goals, g.id) })}
                className={chip(p.goals.includes(g.id))}
              >
                {g.label}
              </button>
            ))
          ) : (
            <span className="text-xs text-muted-foreground">Loading goals…</span>
          )}
        </div>
      </section>

      <section>
        <p className="eyebrow">Usual category</p>
        <div className="mt-3 flex flex-wrap gap-1.5">
          {categories.data?.map((c) => (
            <button
              key={c.category}
              type="button"
              aria-pressed={p.preferred_category === c.category}
              onClick={() =>
                setP({ ...p, preferred_category: p.preferred_category === c.category ? null : c.category })
              }
              className={chip(p.preferred_category === c.category)}
            >
              {c.category}
            </button>
          ))}
        </div>
      </section>

      <section className="max-w-sm">
        <div className="flex items-baseline justify-between">
          <p className="eyebrow">Budget</p>
          <p className="numeric text-xs">{p.max_price ? `Up to $${p.max_price}` : "Any"}</p>
        </div>
        <input
          type="range"
          aria-label="Maximum price"
          min={10}
          max={200}
          step={5}
          value={p.max_price ?? 200}
          onChange={(e) => setP({ ...p, max_price: Number(e.target.value) })}
          className="mt-3 w-full accent-[var(--color-accent)]"
        />
        <button
          type="button"
          onClick={() => setP({ ...p, max_price: null })}
          className="link-underline mt-2 text-xs text-muted-foreground"
        >
          No budget
        </button>
      </section>

      <section className="max-w-lg">
        <p className="eyebrow">Ingredients</p>
        <label className="mt-3 flex cursor-pointer items-center gap-3 text-sm">
          <input
            type="checkbox"
            checked={p.fragrance_free}
            onChange={() => setP({ ...p, fragrance_free: !p.fragrance_free })}
            className="h-3.5 w-3.5 accent-[var(--color-accent)]"
          />
          Fragrance-free only
        </label>
        <input
          aria-label="Ingredients to avoid"
          value={avoid}
          onChange={(e) => setAvoid(e.target.value)}
          placeholder="Always avoid, e.g. alcohol, coconut oil"
          className="mt-3 w-full border border-border bg-transparent px-3 py-2 text-sm focus:border-foreground focus:outline-none"
        />
        <p className="mt-2 text-xs text-muted-foreground">Separate several names with commas.</p>
      </section>

      <div className="flex flex-wrap items-center gap-5 border-t border-border pt-8">
        <button
          type="submit"
          disabled={update.isPending}
          className="border border-foreground bg-foreground px-6 py-3 text-xs uppercase tracking-[0.14em] text-background transition-opacity hover:opacity-85 disabled:opacity-50"
        >
          {update.isPending ? "Saving…" : "Save profile"}
        </button>
        {savedAt ? (
          <span role="status" className="text-sm text-muted-foreground">
            Saved. <Link to="/account" className="link-underline text-foreground">See products for you →</Link>
          </span>
        ) : null}
        {update.error ? (
          <span role="alert" className="text-sm text-foreground">
            {update.error.message}
          </span>
        ) : null}
      </div>
      <p className="text-xs leading-relaxed text-muted-foreground">
        Your profile only personalises rankings. It is not medical or dermatological advice.
      </p>
    </form>
  );
}

// ---------- shared ----------

function Notice({
  title,
  text,
  action,
}: {
  title: string;
  text: string;
  action: { label: string; tab?: Tab; to?: "/explore" };
}) {
  return (
    <div className="border border-dashed border-border-strong px-6 py-12 text-center">
      <p className="display text-xl">{title}</p>
      <p className="mx-auto mt-2 max-w-md text-sm text-muted-foreground">{text}</p>
      {action.to ? (
        <Link to={action.to} className="link-underline mt-5 inline-block text-xs uppercase tracking-[0.12em]">
          {action.label}
        </Link>
      ) : (
        <Link
          to="/account"
          search={{ tab: action.tab }}
          className="link-underline mt-5 inline-block text-xs uppercase tracking-[0.12em]"
        >
          {action.label}
        </Link>
      )}
    </div>
  );
}
