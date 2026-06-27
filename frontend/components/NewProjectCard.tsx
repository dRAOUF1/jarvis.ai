"use client";

import Link from "next/link";
import { Plus } from "lucide-react";

export function NewProjectCard() {
  return (
    <Link
      href="/create"
      className="group flex flex-col items-center justify-center gap-2 transition-all duration-200 h-full min-h-[140px]"
      style={{
        border: "1.5px dashed var(--stroke)",
        borderRadius: "var(--r-card)",
        background: "transparent",
        padding: "20px",
        color: "var(--fg-2)",
      }}
      onMouseEnter={(e) => {
        const el = e.currentTarget as HTMLElement;
        el.style.borderColor = "var(--accent)";
        el.style.background = "var(--accent-soft)";
        el.style.color = "var(--accent)";
      }}
      onMouseLeave={(e) => {
        const el = e.currentTarget as HTMLElement;
        el.style.borderColor = "var(--stroke)";
        el.style.background = "transparent";
        el.style.color = "var(--fg-2)";
      }}
    >
      <div
        className="w-10 h-10 rounded-full flex items-center justify-center transition-colors duration-200"
        style={{ background: "var(--bg-2)" }}
      >
        <Plus size={20} />
      </div>
      <span className="text-sm font-medium">New agent</span>
    </Link>
  );
}
