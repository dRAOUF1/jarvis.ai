"use client";

import Link from "next/link";
import { cn } from "@/lib/cn";

interface AppShellProps {
  children: React.ReactNode;
  breadcrumb?: React.ReactNode;
}

const isMock = process.env.NEXT_PUBLIC_USE_MOCK === "true";

export function AppShell({ children, breadcrumb }: AppShellProps) {
  return (
    <div className="min-h-screen flex flex-col" style={{ background: "var(--bg-0)" }}>
      {/* Top bar */}
      <header
        className="sticky top-0 z-40 flex items-center h-14 px-8"
        style={{
          background: "var(--bg-1)",
          borderBottom: "1px solid var(--stroke)",
        }}
      >
        {/* Left: wordmark */}
        <Link
          href="/"
          className="text-fg-0 font-semibold text-base tracking-tight hover:text-accent transition-colors"
          style={{ color: "var(--fg-0)" }}
        >
          jarvis
          <span style={{ color: "var(--accent)" }}>.</span>
          <span style={{ color: "var(--fg-2)" }}>ai</span>
        </Link>

        {/* Center: breadcrumb */}
        <div className="flex-1 flex justify-center">
          {breadcrumb && (
            <span className="text-sm" style={{ color: "var(--fg-1)" }}>
              {breadcrumb}
            </span>
          )}
        </div>

        {/* Right: mode pill + avatar */}
        <div className="flex items-center gap-3">
          <span
            className={cn(
              "px-2 py-0.5 rounded-pill text-xs font-medium",
              isMock
                ? "bg-warn/10 text-warn"
                : "bg-ok/10 text-ok"
            )}
            style={{
              backgroundColor: isMock ? "rgba(210,153,34,0.12)" : "rgba(63,185,80,0.12)",
              color: isMock ? "var(--warn)" : "var(--ok)",
              borderRadius: "var(--r-pill)",
            }}
          >
            {isMock ? "mock" : "live"}
          </span>
          {/* Demo user avatar */}
          <div
            className="w-7 h-7 rounded-full flex items-center justify-center text-xs font-semibold"
            style={{ background: "var(--accent)", color: "white" }}
          >
            D
          </div>
        </div>
      </header>

      {/* Page content */}
      <main className="flex-1">
        <div className="max-w-[1200px] mx-auto px-8 py-8">{children}</div>
      </main>
    </div>
  );
}
