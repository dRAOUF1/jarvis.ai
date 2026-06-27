"use client";

import { cn } from "@/lib/cn";

type ProvisioningState =
  | "draft" | "compiling" | "connecting" | "provisioning" | "ingesting" | "ready" | "failed";
type ConnectionStatus = "pending" | "connected" | "error";

interface StatusDotProps {
  state: ProvisioningState | ConnectionStatus | string;
  label?: string;
  pulse?: boolean;
  className?: string;
}

const COLORS: Record<string, string> = {
  draft: "var(--fg-2)",
  compiling: "var(--accent)",
  connecting: "var(--accent)",
  provisioning: "var(--accent)",
  ingesting: "var(--accent)",
  ready: "var(--ok)",
  failed: "var(--err)",
  pending: "var(--warn)",
  connected: "var(--ok)",
  error: "var(--err)",
};

const LABELS: Record<string, string> = {
  draft: "Draft",
  compiling: "Designing…",
  connecting: "Linking apps…",
  provisioning: "Building…",
  ingesting: "Learning…",
  ready: "Ready",
  failed: "Failed",
  pending: "Pending",
  connected: "Connected",
  error: "Error",
};

const TRANSIENT = new Set(["compiling", "connecting", "provisioning", "ingesting", "pending"]);

export function StatusDot({ state, label, pulse, className }: StatusDotProps) {
  const color = COLORS[state] ?? "var(--fg-2)";
  const shouldPulse = pulse ?? TRANSIENT.has(state);
  const displayLabel = label ?? LABELS[state] ?? state;

  return (
    <span className={cn("inline-flex items-center gap-1.5", className)}>
      <span
        className={cn("inline-block rounded-full shrink-0", shouldPulse && "animate-pulse")}
        style={{
          width: 7,
          height: 7,
          background: color,
          boxShadow: shouldPulse ? `0 0 6px ${color}` : undefined,
        }}
        aria-hidden
      />
      {displayLabel && (
        <span
          className="text-xs font-medium"
          style={{ color: color === "var(--ok)" ? "var(--ok)" : "var(--fg-2)" }}
        >
          {displayLabel}
        </span>
      )}
    </span>
  );
}
