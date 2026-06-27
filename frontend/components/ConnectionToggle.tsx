"use client";

import { useState } from "react";
import { Check, Loader2, ChevronDown, ChevronUp } from "lucide-react";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { cn } from "@/lib/cn";
import type { CatalogApp } from "@/lib/api";
import type { Connection } from "@/lib/types.gen";

const APP_COLORS: Record<string, string> = {
  strava: "#FC4C02",
  gmail: "#EA4335",
  apple_health: "#FF2D55",
  github: "#8B949E",
  notion: "#E3E3E0",
  slack: "#4A154B",
  google_calendar: "#4285F4",
  spotify: "#1DB954",
};

interface ConnectionToggleProps {
  app: CatalogApp;
  connection?: Connection;
  recommended?: boolean;
  onConnected?: (conn: Connection) => void;
}

export function ConnectionToggle({
  app,
  connection: initialConn,
  recommended,
  onConnected,
}: ConnectionToggleProps) {
  const [conn, setConn] = useState<Connection | undefined>(initialConn);
  const [connecting, setConnecting] = useState(false);
  const [expanded, setExpanded] = useState(false);

  const brandColor = APP_COLORS[app.app] ?? "var(--accent)";
  const isConnected = conn?.status === "connected";
  const isError = conn?.status === "error";

  async function handleConnect() {
    if (isConnected || connecting) return;
    setConnecting(true);
    try {
      const result = await api.connect(app.app);
      if (result.redirect_url) {
        window.location.href = result.redirect_url;
        return;
      }
      setConn(result.connection);
      onConnected?.(result.connection);
      toast.success(`${app.display_name} connected!`);
    } catch (err) {
      toast.error(`Failed to connect ${app.display_name}`);
    } finally {
      setConnecting(false);
    }
  }

  return (
    <div
      className="rounded-card p-4 transition-all duration-150"
      style={{
        background: "var(--bg-1)",
        border: `1px solid ${isConnected ? "var(--ok)" : "var(--stroke)"}`,
        opacity: isConnected ? 1 : 1,
      }}
    >
      <div className="flex items-center gap-4">
        {/* App icon */}
        <div
          className="w-10 h-10 rounded-md flex items-center justify-center text-xl shrink-0"
          style={{
            background: `${brandColor}18`,
            border: `1px solid ${brandColor}30`,
          }}
        >
          {app.icon}
        </div>

        {/* Info */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium" style={{ color: "var(--fg-0)" }}>
              {app.display_name}
            </span>
            {recommended && (
              <span
                className="text-xs px-1.5 py-0.5"
                style={{
                  background: "var(--accent-soft)",
                  color: "var(--accent)",
                  borderRadius: "var(--r-pill)",
                }}
              >
                Recommended
              </span>
            )}
          </div>
          <p className="text-xs mt-0.5 truncate" style={{ color: "var(--fg-2)" }}>
            {app.description}
          </p>
        </div>

        {/* Connect button / status */}
        <div className="flex items-center gap-2 shrink-0">
          {isConnected ? (
            <>
              <button
                onClick={() => setExpanded((e) => !e)}
                className="flex items-center gap-1.5 text-xs transition-colors"
                style={{ color: "var(--ok)" }}
              >
                <Check size={14} strokeWidth={3} />
                <span>Connected</span>
                {conn?.available_tools && conn.available_tools.length > 0 && (
                  expanded ? <ChevronUp size={12} /> : <ChevronDown size={12} />
                )}
              </button>
            </>
          ) : (
            <button
              onClick={handleConnect}
              disabled={connecting}
              className={cn(
                "px-3 py-1.5 text-xs font-medium rounded-md transition-all",
                connecting && "opacity-70"
              )}
              style={{
                background: connecting ? "var(--bg-3)" : "var(--accent)",
                color: "white",
                borderRadius: "var(--r-sm)",
              }}
            >
              {connecting ? (
                <Loader2 size={12} className="animate-spin" />
              ) : isError ? (
                "Retry"
              ) : (
                "Connect"
              )}
            </button>
          )}
        </div>
      </div>

      {/* Expanded tools */}
      {isConnected && expanded && conn?.available_tools && conn.available_tools.length > 0 && (
        <div className="mt-3 pt-3" style={{ borderTop: "1px solid var(--stroke)" }}>
          <div className="flex flex-wrap gap-1.5">
            {conn.available_tools.map((tool) => (
              <span
                key={tool}
                className="text-xs px-2 py-0.5 font-mono"
                style={{
                  background: "var(--bg-2)",
                  color: "var(--fg-1)",
                  borderRadius: "var(--r-sm)",
                  border: "1px solid var(--stroke)",
                }}
              >
                {tool}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
