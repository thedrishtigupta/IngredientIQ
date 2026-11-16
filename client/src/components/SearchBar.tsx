import { useEffect, useId, useRef, useState } from "react";

type Props = {
  value?: string;
  placeholder?: string;
  buttonLabel?: string;
  onSubmit: (value: string) => void;
  /** When set, a "Clear" button appears while there is text; it empties the box and calls this. */
  onClear?: () => void;
  size?: "lg" | "md";
  /** Focus on mount, on a desktop pointer only (never pops the keyboard on a phone). */
  autoFocus?: boolean;
};

export function SearchBar({
  value = "",
  placeholder,
  buttonLabel = "Search",
  onSubmit,
  onClear,
  size = "lg",
  autoFocus = false,
}: Props) {
  const [text, setText] = useState(value);
  const id = useId(); // unique per instance, so two search bars on one page don't share a label
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (autoFocus && window.matchMedia("(pointer: fine)").matches) inputRef.current?.focus({ preventScroll: true });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Follow the parent when it changes the value (e.g. the URL's ?q= or a "clear" elsewhere).
  useEffect(() => setText(value), [value]);

  return (
    <form
      role="search"
      onSubmit={(e) => {
        e.preventDefault();
        onSubmit(text.trim());
      }}
      className={`group flex items-center gap-3 rounded-full border border-border bg-paper/90 shadow-[var(--shadow-soft)] transition-[border-color,box-shadow] duration-300 focus-within:border-accent focus-within:shadow-[0_0_0_5px_color-mix(in_oklab,var(--color-gold)_20%,transparent),var(--shadow-lift)] ${
        size === "lg" ? "py-2 pl-6 pr-2" : "py-1.5 pl-4 pr-1.5"
      }`}
    >
      <label className="sr-only" htmlFor={id}>
        {placeholder ?? "Search"}
      </label>
      <svg
        aria-hidden="true"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.5"
        className={`shrink-0 self-center text-muted-foreground ${size === "lg" ? "h-5 w-5 sm:h-6 sm:w-6" : "h-4 w-4"}`}
      >
        <circle cx="11" cy="11" r="7" />
        <path d="m20 20-3.5-3.5" strokeLinecap="round" />
      </svg>
      <input
        id={id}
        ref={inputRef}
        type="search"
        name="q"
        autoComplete="off"
        spellCheck={false}
        enterKeyHint="search"
        value={text}
        onChange={(e) => setText(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Escape" && onClear && text) {
            setText("");
            onClear();
          }
        }}
        placeholder={placeholder}
        className={`w-full min-w-0 bg-transparent text-foreground placeholder:text-muted-foreground/70 focus:outline-none [&::-webkit-search-cancel-button]:hidden ${
          size === "lg" ? "py-2 text-base sm:text-lg" : "py-1 text-sm"
        }`}
      />
      {onClear && text ? (
        <button
          type="button"
          onClick={() => {
            setText("");
            onClear();
            inputRef.current?.focus();
          }}
          aria-label="Clear search"
          className={`shrink-0 whitespace-nowrap rounded-full px-2 py-2 uppercase tracking-[0.14em] text-muted-foreground transition-colors hover:text-foreground ${
            size === "lg" ? "text-xs sm:text-sm" : "text-[0.65rem]"
          }`}
        >
          Clear
        </button>
      ) : null}
      <button
        type="submit"
        className={`btn btn-primary shrink-0 ${size === "lg" ? "" : "btn-sm"}`}
      >
        {buttonLabel}
      </button>
    </form>
  );
}
