import { useEffect, useId, useState } from "react";

type Props = {
  value?: string;
  placeholder?: string;
  buttonLabel?: string;
  onSubmit: (value: string) => void;
  /** When set, a "Clear" button appears while there is text; it empties the box and calls this. */
  onClear?: () => void;
  size?: "lg" | "md";
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

  // Follow the parent when it changes the value (e.g. the URL's ?q= or a "clear" elsewhere).
  useEffect(() => setText(value), [value]);

  return (
    <form
      role="search"
      onSubmit={(e) => {
        e.preventDefault();
        onSubmit(text.trim());
      }}
      className={`group flex items-end gap-3 border-b border-border-strong transition-colors focus-within:border-foreground ${
        size === "lg" ? "pb-3" : "pb-2"
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
        type="search"
        autoFocus={autoFocus}
        autoComplete="off"
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
          size === "lg" ? "text-lg sm:text-2xl" : "text-base"
        }`}
      />
      {onClear && text ? (
        <button
          type="button"
          onClick={() => {
            setText("");
            onClear();
          }}
          className={`shrink-0 whitespace-nowrap pb-1 uppercase tracking-[0.14em] text-muted-foreground transition-colors hover:text-foreground ${
            size === "lg" ? "text-xs sm:text-sm" : "text-[0.65rem]"
          }`}
        >
          Clear
        </button>
      ) : null}
      <button
        type="submit"
        className={`shrink-0 whitespace-nowrap border-b border-foreground pb-1 uppercase tracking-[0.14em] text-foreground transition-opacity hover:opacity-60 ${
          size === "lg" ? "text-xs sm:text-sm" : "text-[0.65rem]"
        }`}
      >
        {buttonLabel}
      </button>
    </form>
  );
}
