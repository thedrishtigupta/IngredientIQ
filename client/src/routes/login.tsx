import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { ApiError, useAuth, useSignIn } from "@/lib/api";

type Search = { mode?: "register" | undefined; redirect?: string | undefined };

export const Route = createFileRoute("/login")({
  validateSearch: (s: Record<string, unknown>): Search => ({
    mode: s["mode"] === "register" ? "register" : undefined,
    // Only same-site paths, never a full URL (no open redirect).
    redirect:
      typeof s["redirect"] === "string" && s["redirect"].startsWith("/") && !s["redirect"].startsWith("//")
        ? s["redirect"]
        : undefined,
  }),
  head: () => ({ meta: [{ title: "Sign in — IngredientIQ" }] }),
  component: Login,
});

const input =
  "mt-2 w-full border border-border bg-transparent px-3 py-2.5 text-sm focus:border-foreground focus:outline-none";

function Login() {
  const { mode, redirect } = Route.useSearch();
  const navigate = useNavigate();
  const { user } = useAuth();
  const signIn = useSignIn();
  const registering = mode === "register";

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");

  // Already signed in (or just signed in): go where the user was heading.
  useEffect(() => {
    if (user) void navigate({ to: redirect ?? "/account", replace: true });
  }, [user, redirect, navigate]);

  const error = signIn.error;
  const message =
    error instanceof ApiError && error.status === null
      ? "The IngredientIQ API is not responding. Start it and try again."
      : error?.message;

  return (
    <div className="mx-auto max-w-[440px] px-5 py-16 sm:py-24">
      <p className="eyebrow">{registering ? "Create an account" : "Welcome back"}</p>
      <h1 className="display mt-4 text-4xl">{registering ? "Create your account" : "Sign in"}</h1>
      <p className="mt-3 text-sm leading-relaxed text-muted-foreground">
        {registering
          ? "Save your skin profile, keep your search history and bookmark products."
          : "Sign in to see your search history, saved products and recommendations for you."}
      </p>

      <form
        className="mt-10 space-y-6"
        onSubmit={(e) => {
          e.preventDefault();
          signIn.mutate({ mode: registering ? "register" : "login", email, password, display_name: name });
        }}
      >
        {registering ? (
          <label className="block">
            <span className="eyebrow">Name</span>
            <input
              required
              maxLength={60}
              autoComplete="nickname"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className={input}
            />
          </label>
        ) : null}
        <label className="block">
          <span className="eyebrow">Email</span>
          <input
            required
            type="email"
            autoComplete="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className={input}
          />
        </label>
        <label className="block">
          <span className="eyebrow">Password</span>
          <input
            required
            type="password"
            minLength={registering ? 8 : undefined}
            autoComplete={registering ? "new-password" : "current-password"}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className={input}
          />
          {registering ? (
            <span className="mt-1.5 block text-xs text-muted-foreground">At least 8 characters.</span>
          ) : null}
        </label>

        {message ? (
          <p role="alert" className="border-l-2 border-accent pl-3 text-sm text-foreground">
            {message}
          </p>
        ) : null}

        <button
          type="submit"
          disabled={signIn.isPending}
          className="w-full border border-foreground bg-foreground px-5 py-3 text-xs uppercase tracking-[0.14em] text-background transition-opacity hover:opacity-85 disabled:opacity-50"
        >
          {signIn.isPending ? "One moment…" : registering ? "Create account" : "Sign in"}
        </button>
      </form>

      <p className="mt-8 text-sm text-muted-foreground">
        {registering ? "Already have an account? " : "New to IngredientIQ? "}
        <Link
          to="/login"
          search={{ mode: registering ? undefined : "register", redirect }}
          onClick={() => signIn.reset()}
          className="link-underline text-foreground"
        >
          {registering ? "Sign in" : "Create an account"}
        </Link>
      </p>
    </div>
  );
}
