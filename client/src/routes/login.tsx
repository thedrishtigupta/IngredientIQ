import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { useEffect, useRef, useState } from "react";
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

const input = "field mt-2";

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
  const errorRef = useRef<HTMLParagraphElement>(null);
  // Move focus to the error after a failed attempt, so it is read out and seen.
  useEffect(() => {
    if (signIn.isError) errorRef.current?.focus();
  }, [signIn.isError]);
  const message =
    error instanceof ApiError && error.status === null
      ? "The IngredientIQ API is not responding. Start it and try again."
      : error?.message;

  return (
    <div className="mx-auto max-w-[480px] px-5 py-16 sm:py-24">
      <div className="card-lux rise p-8 sm:p-10">
      <p className="eyebrow-gold">{registering ? "Create an account" : "Welcome back"}</p>
      <h1 className="display mt-5 text-5xl">{registering ? "Create your account" : "Sign in"}</h1>
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
              name="name"
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
            name="email"
            inputMode="email"
            autoComplete="email"
            autoCapitalize="none"
            spellCheck={false}
            aria-invalid={message ? true : undefined}
            aria-describedby={message ? "login-error" : undefined}
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
            name="password"
            minLength={registering ? 8 : undefined}
            aria-invalid={message ? true : undefined}
            aria-describedby={[registering ? "password-hint" : "", message ? "login-error" : ""].filter(Boolean).join(" ") || undefined}
            autoComplete={registering ? "new-password" : "current-password"}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className={input}
          />
          {registering ? (
            <span id="password-hint" className="mt-1.5 block text-xs text-muted-foreground">At least 8 characters.</span>
          ) : null}
        </label>

        {message ? (
          <p
            id="login-error"
            ref={errorRef}
            tabIndex={-1}
            role="alert"
            className="rounded-xl border border-accent/30 bg-accent/5 px-4 py-3 text-sm text-foreground focus:outline-none"
          >
            {message}
          </p>
        ) : null}

        <button
          type="submit"
          disabled={signIn.isPending}
          aria-busy={signIn.isPending}
          className="btn btn-primary w-full"
        >
          {signIn.isPending ? <span className="spinner" aria-hidden="true" /> : null}
          {signIn.isPending ? "One moment…" : registering ? "Create account" : "Sign in"}
        </button>
      </form>

      <p className="mt-8 text-sm text-muted-foreground">
        {registering ? "Already have an account? " : "New to IngredientIQ? "}
        <Link
          to="/login"
          search={{ mode: registering ? undefined : "register", redirect }}
          onClick={() => signIn.reset()}
          className="link-underline py-1 text-foreground"
        >
          {registering ? "Sign in" : "Create an account"}
        </Link>
      </p>
      </div>
    </div>
  );
}
