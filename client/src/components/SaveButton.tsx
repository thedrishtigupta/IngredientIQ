import { useNavigate, useRouterState } from "@tanstack/react-router";
import { useAuth, useSaved, useToggleSaved } from "@/lib/api";

type Props = {
  productId: string;
  /** "icon": small round button over a product image; "text": a labelled button. */
  variant?: "icon" | "text";
  className?: string;
};

function Heart({ filled }: { filled: boolean }) {
  return (
    <svg aria-hidden="true" viewBox="0 0 24 24" className="h-4 w-4" fill={filled ? "currentColor" : "none"} stroke="currentColor" strokeWidth="1.5">
      <path
        strokeLinejoin="round"
        d="M12 20.5s-7.5-4.6-7.5-10.1A4.4 4.4 0 0 1 12 7.6a4.4 4.4 0 0 1 7.5 2.8c0 5.5-7.5 10.1-7.5 10.1Z"
      />
    </svg>
  );
}

/** Save / unsave a product. Signed out, it sends the user to sign in and back here afterwards. */
export function SaveButton({ productId, variant = "icon", className = "" }: Props) {
  const { user } = useAuth();
  const saved = useSaved();
  const toggle = useToggleSaved();
  const navigate = useNavigate();
  const here = useRouterState({ select: (s) => s.location.href });

  const isSaved = saved.data?.some((p) => p.product_id === productId) ?? false;
  // Show the state the user asked for while the request is in flight.
  const shown = toggle.isPending && toggle.variables?.productId === productId ? toggle.variables.save : isSaved;
  const label = shown ? "Saved" : "Save";

  const onClick = (e: React.MouseEvent) => {
    e.preventDefault(); // the icon sits inside a product link
    e.stopPropagation();
    if (!user) {
      void navigate({ to: "/login", search: { redirect: here } });
      return;
    }
    toggle.mutate({ productId, save: !isSaved });
  };

  if (variant === "text") {
    return (
      <button
        type="button"
        onClick={onClick}
        aria-pressed={shown}
        className={`inline-flex items-center gap-2 border px-4 py-2 text-xs uppercase tracking-[0.14em] transition-colors ${
          shown
            ? "border-foreground bg-foreground text-background"
            : "border-foreground text-foreground hover:bg-foreground hover:text-background"
        } ${className}`}
      >
        <Heart filled={shown} />
        {label}
      </button>
    );
  }

  return (
    <button
      type="button"
      onClick={onClick}
      aria-pressed={shown}
      aria-label={shown ? "Remove from saved" : "Save product"}
      title={shown ? "Remove from saved" : "Save"}
      className={`flex h-9 w-9 items-center justify-center rounded-full bg-background/90 text-foreground shadow-sm backdrop-blur-sm transition-colors hover:bg-foreground hover:text-background ${
        shown ? "text-accent" : ""
      } ${className}`}
    >
      <Heart filled={shown} />
    </button>
  );
}
