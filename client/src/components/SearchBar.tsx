import { useState } from "react";

type Props = {
  value?: string;
  placeholder?: string;
  onSubmit: (value: string) => void;
  size?: "lg" | "md";
};

export function SearchBar({ value = "", placeholder, onSubmit, size = "lg" }: Props) {
  const [text, setText] = useState(value);

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        onSubmit(text.trim());
      }}
      className={`group flex items-end gap-3 border-b border-border-strong transition-colors focus-within:border-foreground ${
        size === "lg" ? "pb-3" : "pb-2"
      }`}
    >
      <label className="sr-only" htmlFor="requirement">
        Describe what you need
      </label>
      <input
        id="requirement"
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder={placeholder ?? "I want a lightweight moisturizer under $50 without fragrance."}
        className={`w-full bg-transparent text-foreground placeholder:text-muted-foreground/70 focus:outline-none ${
          size === "lg" ? "text-lg sm:text-2xl" : "text-base"
        }`}
      />
      <button
        type="submit"
        className={`shrink-0 whitespace-nowrap border-b border-foreground pb-1 uppercase tracking-[0.14em] text-foreground transition-opacity hover:opacity-60 ${
          size === "lg" ? "text-xs sm:text-sm" : "text-[0.65rem]"
        }`}
      >
        Find products
      </button>
    </form>
  );
}
