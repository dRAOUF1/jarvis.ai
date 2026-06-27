"use client";

import { cn } from "@/lib/cn";
import { Check, X } from "lucide-react";

type Stage =
  | "compiling"
  | "connecting"
  | "provisioning"
  | "ingesting"
  | "ready";

const STAGES: { key: Stage; label: string; sub: string }[] = [
  { key: "compiling", label: "Designing the agent", sub: "Writing its soul and skills" },
  { key: "connecting", label: "Linking your apps", sub: "Securing tool access" },
  { key: "provisioning", label: "Building the runtime", sub: "Spinning up a private gateway" },
  { key: "ingesting", label: "Learning about you", sub: "Reading your recent activity" },
  { key: "ready", label: "Ready", sub: "Say hello 👋" },
];

const ORDER = STAGES.map((s) => s.key);

interface ProvisioningProgressProps {
  status: string;
  failedStage?: string | null;
}

export function ProvisioningProgress({ status, failedStage }: ProvisioningProgressProps) {
  const currentIdx = ORDER.indexOf(status as Stage);
  const isFailed = status === "failed";

  return (
    <div className="flex flex-col gap-0">
      {STAGES.map((stage, i) => {
        const stageIdx = ORDER.indexOf(stage.key);
        const isDone = !isFailed && currentIdx > stageIdx;
        const isActive = !isFailed && currentIdx === stageIdx;
        const isFail = isFailed && failedStage === stage.key;
        const isPending = !isDone && !isActive && !isFail;

        return (
          <div key={stage.key} className="flex gap-4">
            {/* Node + connector */}
            <div className="flex flex-col items-center">
              {/* Node */}
              <div
                className={cn(
                  "w-7 h-7 rounded-full flex items-center justify-center shrink-0 border-2 transition-all duration-300",
                  isDone && "border-transparent",
                  isActive && "border-accent animate-pulse",
                  isFail && "border-transparent",
                  isPending && "border-stroke"
                )}
                style={{
                  background: isDone
                    ? "var(--ok)"
                    : isActive
                    ? "var(--accent-soft)"
                    : isFail
                    ? "var(--err)"
                    : "transparent",
                  borderColor: isActive ? "var(--accent)" : isPending ? "var(--stroke)" : "transparent",
                }}
              >
                {isDone && <Check size={14} color="white" strokeWidth={3} />}
                {isFail && <X size={14} color="white" strokeWidth={3} />}
                {isActive && (
                  <div
                    className="w-2.5 h-2.5 rounded-full"
                    style={{ background: "var(--accent)" }}
                  />
                )}
              </div>

              {/* Connector line */}
              {i < STAGES.length - 1 && (
                <div
                  className="w-px flex-1 mt-1 mb-1 min-h-[28px] transition-all duration-500"
                  style={{
                    background: isDone ? "var(--ok)" : "var(--stroke)",
                  }}
                />
              )}
            </div>

            {/* Text */}
            <div className="pb-6 pt-0.5">
              <div
                className="text-sm font-medium leading-snug"
                style={{
                  color: isDone
                    ? "var(--fg-0)"
                    : isActive
                    ? "var(--fg-0)"
                    : isFail
                    ? "var(--err)"
                    : "var(--fg-2)",
                }}
              >
                {stage.label}
              </div>
              <div className="text-xs mt-0.5" style={{ color: "var(--fg-2)" }}>
                {stage.sub}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
