"use client";

import { useMemo } from "react";
import { cn } from "@/lib/cn";

interface AgentAvatarProps {
  seed: string;
  size?: number;
  ring?: boolean;
  className?: string;
}

export function AgentAvatar({ seed, size = 48, ring = false, className }: AgentAvatarProps) {
  const dataUri = useMemo(() => {
    try {
      // Generate a deterministic gradient from the seed
      let hash = 0;
      for (let i = 0; i < seed.length; i++) {
        hash = (hash << 5) - hash + seed.charCodeAt(i);
        hash |= 0;
      }
      const h1 = Math.abs(hash % 360);
      const h2 = (h1 + 60) % 360;
      return `linear-gradient(135deg, hsl(${h1}, 70%, 45%), hsl(${h2}, 80%, 35%))`;
    } catch {
      return "linear-gradient(135deg, #6D5EF7, #5B4DE0)";
    }
  }, [seed]);

  const initial = seed
    .replace(/[^a-zA-Z]/g, "")
    .charAt(0)
    .toUpperCase() || "J";

  return (
    <div
      className={cn(
        "flex items-center justify-center shrink-0 font-semibold select-none transition-shadow duration-200",
        ring && "shadow-glow",
        className
      )}
      style={{
        width: size,
        height: size,
        borderRadius: "var(--r-md)",
        background: dataUri,
        color: "rgba(255,255,255,0.9)",
        fontSize: Math.max(12, size * 0.35),
        boxShadow: ring ? "var(--shadow-glow)" : undefined,
      }}
      aria-label={`Avatar for ${seed}`}
    >
      {initial}
    </div>
  );
}
