"use client";

import type { DbMemory } from "@/lib/types.gen";
import type { StreamAction } from "@/lib/useAgentStream";

const KIND_STYLES: Record<string, { bg: string; color: string; label: string }> = {
  fact: { bg: "var(--accent-soft)", color: "var(--accent)", label: "Fact" },
  preference: { bg: "rgba(88,166,255,0.1)", color: "var(--info)", label: "Preference" },
  scraped: { bg: "rgba(63,185,80,0.1)", color: "var(--ok)", label: "Scraped" },
  weakness: { bg: "rgba(248,81,73,0.1)", color: "var(--err)", label: "Weakness" },
};

interface SidePanelProps {
  memory: DbMemory[];
  actions: StreamAction[];
}

export function SidePanel({ memory, actions }: SidePanelProps) {
  return (
    <div className="flex flex-col gap-6 h-full overflow-y-auto pr-1">
      {/* Memory section */}
      <div>
        <div
          className="text-xs font-medium uppercase tracking-wide mb-3"
          style={{ color: "var(--fg-2)" }}
        >
          Memory
        </div>
        {memory.length === 0 ? (
          <p className="text-xs" style={{ color: "var(--fg-2)" }}>
            Memory entries will appear here after provisioning.
          </p>
        ) : (
          <div className="space-y-2">
            {memory.map((entry) => {
              const kindStyle =
                KIND_STYLES[entry.kind ?? "fact"] ?? KIND_STYLES.fact;
              return (
                <div
                  key={entry.id}
                  className="rounded-md p-2.5 text-xs leading-relaxed"
                  style={{
                    background: kindStyle.bg,
                    border: `1px solid ${kindStyle.color}30`,
                  }}
                >
                  <span
                    className="font-medium uppercase tracking-wide text-[10px] mr-1.5"
                    style={{ color: kindStyle.color }}
                  >
                    {kindStyle.label}
                  </span>
                  <span style={{ color: "var(--fg-1)" }}>{entry.content}</span>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Recent actions */}
      <div>
        <div
          className="text-xs font-medium uppercase tracking-wide mb-3"
          style={{ color: "var(--fg-2)" }}
        >
          Recent actions
        </div>
        {actions.length === 0 ? (
          <p className="text-xs" style={{ color: "var(--fg-2)" }}>
            Tool calls will appear here as your agent acts.
          </p>
        ) : (
          <div className="space-y-2">
            {actions.map((action, i) => (
              <div
                key={i}
                className="flex flex-col gap-0.5 rounded-md p-2.5 text-xs"
                style={{
                  background: "var(--bg-2)",
                  border: "1px solid var(--stroke)",
                }}
              >
                <span
                  className="font-medium"
                  style={{ color: "var(--fg-0)" }}
                >
                  {action.label}
                </span>
                {action.detail && (
                  <span style={{ color: "var(--fg-2)" }}>{action.detail}</span>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
