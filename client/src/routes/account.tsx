import { createFileRoute, Link, useBlocker, useNavigate } from "@tanstack/react-router";
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
import { fmtBudget, fmtRelative, humanize } from "@/lib/labels";
import { LinesSkeleton, ProductGridSkeleton } from "@/components/Skeleton";

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
    return (
      <div className="mx-auto max-w-[1280px] px-5 py-12 sm:px-8">
        <LinesSkeleton lines={1} label="Loading your account…" className="max-w-32" />
        <div aria-hidden="true" className="shimmer mt-6 h-14 w-1/2 rounded-2xl" />
        <div aria-hidden="true" className="shimmer mt-10 h-11 w-80 max-w-full rounded-full" />
        <ProductGridSkeleton count={4} label="" className="mt-10 grid grid-cols-2 gap-x-5 gap-y-12 sm:gap-x-8 lg:grid-cols-4" />
      </div>
    );
  }
  if (!user) {
    return (
      <div className="mx-auto max-w-[1280px] px-5 py-16 sm:px-8">
        {error ? (
          <ErrorNotice error={error} />
        ) : (
          <div className="max-w-lg">
            <p className="eyebrow-gold">My account</p>
            <h1 className="display mt-5 text-4xl">Sign in to see your profile</h1>
            <p className="mt-3 text-sm leading-relaxed text-muted-foreground">
              Your search history, saved products and recommendations based on your skin profile live here.
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <Link
                to="/login"
                search={{ redirect: "/account" }}
                className="btn btn-primary"
              >
                Sign in
              </Link>
              <Link
                to="/login"
                search={{ mode: "register", redirect: "/account" }}
                className="btn btn-outline"
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
    <div className="mx-auto max-w-[1280px] px-5 py-12 sm:px-8">
      <div className="flex flex-wrap items-end justify-between gap-6">
        <div>
          <p className="eyebrow-gold">My account</p>
          <h1 className="display mt-5 break-words text-5xl sm:text-6xl">Hello, {user.display_name}</h1>
          <p className="mt-2 break-all text-sm text-muted-foreground sm:break-normal">
            {user.email}
            {user.profile.skin_type ? ` · ${humanize(user.profile.skin_type)} skin` : ""}
          </p>
        </div>
        <button
          type="button"
          onClick={() => signOut.mutate(undefined, { onSettled: () => void navigate({ to: "/" }) })}
          disabled={signOut.isPending}
          className="link-underline py-1 text-xs uppercase tracking-[0.14em] text-muted-foreground hover:text-foreground disabled:opacity-50"
        >
          Sign out
        </button>
      </div>

      <nav className="mt-10 inline-flex max-w-full gap-1 overflow-x-auto rounded-full border border-border bg-paper/70 p-1" aria-label="Account sections">
        {TABS.map((t) => (
          <Link
            key={t.id}
            to="/account"
            search={{ tab: t.id === "for-you" ? undefined : t.id }}
            replace
            aria-current={tab === t.id ? "page" : undefined}
            className={`flex min-h-10 shrink-0 items-center whitespace-nowrap rounded-full px-5 py-2 text-sm transition-colors duration-150 ${
              tab === t.id ? "bg-foreground text-background" : "text-muted-foreground hover:text-foreground"
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
          {p.max_price ? `, under ${fmtBudget(p.max_price)}` : ""}
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
          <ProductGridSkeleton count={4} label="Finding products for you…" />
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

  if (history.isPending) return <LinesSkeleton lines={5} label="Loading your searches…" className="max-w-3xl" />;
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
          className="link-underline py-1 text-xs uppercase tracking-[0.12em] text-muted-foreground hover:text-foreground disabled:opacity-50"
        >
          Clear history
        </button>
      </div>
      <ul className="mt-6 divide-y divide-border border-y border-border">
        {history.data.map((h) => (
          <HistoryRow
            key={h.search_id}
            item={h}
            onDelete={() => {
              if (window.confirm(`Delete “${h.query}” from your search history?`)) del.mutate(h.search_id);
            }}
          />
        ))}
      </ul>
    </section>
  );
}

function HistoryRow({ item, onDelete }: { item: HistoryItem; onDelete: () => void }) {
  const when = fmtRelative(item.created_at);
  const again =
    item.kind === "text" ? (
      <Link to="/explore" search={{ q: item.query }} className="link-underline py-1 text-xs uppercase tracking-[0.12em]">
        Search again
      </Link>
    ) : (
      <Link to="/explore" search={{ run: item.params }} className="link-underline py-1 text-xs uppercase tracking-[0.12em]">
        Run again
      </Link>
    );

  return (
    <li className="flex flex-wrap items-center gap-x-6 gap-y-2 py-4">
      <span className="eyebrow w-20 shrink-0">{item.kind === "text" ? "Search" : "Goals"}</span>
      <div className="min-w-0 flex-1">
        <p className="truncate text-sm text-foreground">{item.query}</p>
        <p className="numeric mt-0.5 text-xs text-muted-foreground">
          {item.result_count} {item.result_count === 1 ? "result" : "results"} ·{" "}
          <time dateTime={item.created_at} title={new Date(item.created_at).toLocaleString("en-US")} suppressHydrationWarning>
            {when}
          </time>
        </p>
      </div>
      <div className="flex items-center gap-5">
        {again}
        <button
          type="button"
          onClick={onDelete}
          aria-label={`Delete “${item.query}” from history`}
          className="flex h-9 w-9 items-center justify-center rounded-full text-lg leading-none text-muted-foreground transition-colors duration-150 hover:bg-muted hover:text-foreground active:scale-95"
        >
          <span aria-hidden="true">×</span>
        </button>
      </div>
    </li>
  );
}

// ---------- Saved ----------

function Saved() {
  const saved = useSaved();
  if (saved.isPending) return <ProductGridSkeleton count={4} label="Loading saved products…" />;
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


const toggle = <T,>(arr: T[], v: T) => (arr.includes(v) ? arr.filter((x) => x !== v) : [...arr, v]);

function ProfileForm({ user }: { user: Me }) {
  const goals = useGoals();
  const categories = useCategories();
  const update = useUpdateProfile();

  const [p, setP] = useState<Profile>(user.profile);
  const [avoid, setAvoid] = useState(user.profile.avoided_ingredients.join(", "));
  const [savedAt, setSavedAt] = useState<number | null>(null);
  useEffect(() => setSavedAt(null), [p, avoid]); // any edit hides "Saved"

  // Warn before leaving (tab switch, link, reload, close) with unsaved edits.
  const dirty =
    savedAt === null &&
    (JSON.stringify(p) !== JSON.stringify(user.profile) || avoid !== user.profile.avoided_ingredients.join(", "));
  useBlocker({
    shouldBlockFn: () => !window.confirm("Your profile has unsaved changes. Leave without saving?"),
    enableBeforeUnload: dirty,
    disabled: !dirty || update.isPending,
  });

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
      <fieldset>
        <legend className="eyebrow">Skin type</legend>
        <div className="mt-3 flex flex-wrap gap-1.5">
          {SKIN_TYPES.map((s) => (
            <button
              key={s}
              type="button"
              aria-pressed={p.skin_type === s}
              onClick={() => setP({ ...p, skin_type: p.skin_type === s ? null : s })}
              className="chip"
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
      </fieldset>

      <fieldset>
        <legend className="eyebrow">Goals</legend>
        <div className="mt-3 flex flex-wrap gap-1.5">
          {goals.data ? (
            goals.data.map((g) => (
              <button
                key={g.id}
                type="button"
                aria-pressed={p.goals.includes(g.id)}
                onClick={() => setP({ ...p, goals: toggle(p.goals, g.id) })}
                className="chip"
              >
                {g.label}
              </button>
            ))
          ) : (
            <span className="text-xs text-muted-foreground">Loading goals…</span>
          )}
        </div>
      </fieldset>

      <fieldset>
        <legend className="eyebrow">Usual category</legend>
        <div className="mt-3 flex flex-wrap gap-1.5">
          {categories.isPending ? <span className="text-xs text-muted-foreground">Loading categories…</span> : null}
          {categories.data?.map((c) => (
            <button
              key={c.category}
              type="button"
              aria-pressed={p.preferred_category === c.category}
              onClick={() =>
                setP({ ...p, preferred_category: p.preferred_category === c.category ? null : c.category })
              }
              className="chip"
            >
              {c.category}
            </button>
          ))}
        </div>
      </fieldset>

      <fieldset className="max-w-sm">
        <div className="flex items-baseline justify-between">
          <legend className="eyebrow float-left">Budget</legend>
          <p className="numeric text-xs" aria-hidden="true">
            {p.max_price ? `Up to ${fmtBudget(p.max_price)}` : "Any"}
          </p>
        </div>
        <input
          type="range"
          name="max_price"
          aria-label="Maximum price"
          aria-valuetext={p.max_price ? `Up to ${fmtBudget(p.max_price)}` : "Any price"}
          min={10}
          max={200}
          step={5}
          value={p.max_price ?? 200}
          onChange={(e) => setP({ ...p, max_price: Number(e.target.value) })}
          style={{ "--fill": `${(((p.max_price ?? 200) - 10) / 190) * 100}%` } as React.CSSProperties}
          className="mt-4 w-full"
        />
        <button
          type="button"
          onClick={() => setP({ ...p, max_price: null })}
          className="link-underline mt-2 py-1 text-xs text-muted-foreground"
        >
          No budget
        </button>
      </fieldset>

      <fieldset className="max-w-lg">
        <legend className="eyebrow">Ingredients</legend>
        <label className="mt-2 flex min-h-11 cursor-pointer select-none items-center gap-3 text-sm">
          <input
            type="checkbox"
            checked={p.fragrance_free}
            onChange={() => setP({ ...p, fragrance_free: !p.fragrance_free })}
            className="h-4 w-4 accent-[var(--color-accent)]"
          />
          Fragrance-free only
        </label>
        <input
          aria-label="Ingredients to avoid"
          name="avoided_ingredients"
          autoComplete="off"
          spellCheck={false}
          value={avoid}
          onChange={(e) => setAvoid(e.target.value)}
          placeholder="Always avoid, e.g. alcohol, coconut oil…"
          className="field mt-3"
        />
        <p className="mt-2 text-xs text-muted-foreground">Separate several names with commas.</p>
      </fieldset>

      <div className="flex flex-wrap items-center gap-5 border-t border-border pt-8">
        <button
          type="submit"
          disabled={update.isPending}
          aria-busy={update.isPending}
          className="btn btn-primary"
        >
          {update.isPending ? <span className="spinner" aria-hidden="true" /> : null}
          {update.isPending ? "Saving…" : "Save profile"}
        </button>
        {savedAt ? (
          <span role="status" className="text-sm text-muted-foreground">
            Saved.{" "}
            <Link to="/account" className="link-underline text-foreground">
              See products for you <span aria-hidden="true" className="arrow">→</span>
            </Link>
          </span>
        ) : null}
        {update.error ? (
          <span role="alert" className="break-words text-sm text-foreground">
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
    <div className="empty-state px-6 py-14 text-center">
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
