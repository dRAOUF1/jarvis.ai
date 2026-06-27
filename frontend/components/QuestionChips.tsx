"use client";

import { useState } from "react";
import { cn } from "@/lib/cn";

interface QuestionChipsProps {
  options: string[];
  onPick: (option: string) => void;
}

export function QuestionChips({ options, onPick }: QuestionChipsProps) {
  const [picked, setPicked] = useState<string | null>(null);

  function handlePick(opt: string) {
    if (picked) return;
    setPicked(opt);
    onPick(opt);
  }

  return (
    <div className="flex flex-wrap gap-2 mt-3">
      {options.map((opt, i) => (
        <button
          key={opt}
          onClick={() => handlePick(opt)}
          disabled={picked !== null}
          className={cn(
            "px-3 py-1.5 text-sm rounded-pill border transition-all duration-150",
            picked === opt
              ? "opacity-100"
              : picked !== null
              ? "opacity-40"
              : "hover:border-accent hover:text-accent"
          )}
          style={{
            animationDelay: `${i * 40}ms`,
            borderColor: picked === opt ? "var(--accent)" : "var(--stroke)",
            color: picked === opt ? "var(--accent)" : "var(--fg-1)",
            background: picked === opt ? "var(--accent-soft)" : "transparent",
            borderRadius: "var(--r-pill)",
            cursor: picked !== null ? "default" : "pointer",
          }}
        >
          {opt}
        </button>
      ))}
    </div>
  );
}
