"use client";

import { AgentAvatar } from "./AgentAvatar";
import type { ProjectSpec } from "@/lib/types.gen";

interface SpecCardProps {
  spec: Partial<ProjectSpec> | null;
  suggestedApps?: string[];
}

function FieldRow({
  label,
  value,
  italic,
}: {
  label: string;
  value?: string;
  italic?: boolean;
}) {
  return (
    <div className="mb-3">
      <div
        className="text-xs font-medium uppercase tracking-wide mb-1"
        style={{ color: "var(--fg-2)" }}
      >
        {label}
      </div>
      {value ? (
        <div
          className="text-sm leading-relaxed"
          style={{ color: "var(--fg-0)", fontStyle: italic ? "italic" : undefined }}
        >
          {value}
        </div>
      ) : (
        <div
          className="h-4 rounded shimmer"
          style={{ background: "var(--bg-2)", width: "70%" }}
        />
      )}
    </div>
  );
}

export function SpecCard({ spec, suggestedApps }: SpecCardProps) {
  const hasAny = spec && Object.keys(spec).length > 0;

  return (
    <div
      className="rounded-card p-5 h-full"
      style={{
        background: "var(--bg-1)",
        border: "1px solid var(--stroke)",
      }}
    >
      {/* Header */}
      <div
        className="text-xs font-medium uppercase tracking-wide mb-4"
        style={{ color: "var(--fg-2)" }}
      >
        Agent spec
      </div>

      {/* Avatar + name */}
      <div className="flex items-center gap-3 mb-5">
        <AgentAvatar seed={spec?.avatar_seed ?? spec?.name ?? "agent"} size={40} />
        <div>
          {spec?.name ? (
            <div className="font-semibold text-sm" style={{ color: "var(--fg-0)" }}>
              {spec.name}
            </div>
          ) : (
            <div className="h-4 rounded shimmer w-28" style={{ background: "var(--bg-2)" }} />
          )}
        </div>
      </div>

      <FieldRow label="Goal" value={spec?.goal} />
      <FieldRow label="Persona" value={spec?.persona} italic />

      {/* Tasks */}
      <div className="mb-3">
        <div
          className="text-xs font-medium uppercase tracking-wide mb-2"
          style={{ color: "var(--fg-2)" }}
        >
          Tasks
        </div>
        {spec?.tasks && spec.tasks.length > 0 ? (
          <ul className="space-y-1.5">
            {spec.tasks.map((t, i) => (
              <li key={i} className="flex items-start gap-2 text-sm" style={{ color: "var(--fg-1)" }}>
                <span style={{ color: "var(--accent)", marginTop: 2 }}>✓</span>
                <span>{t.title}</span>
              </li>
            ))}
          </ul>
        ) : (
          <div className="space-y-1.5">
            {[60, 75, 50].map((w, i) => (
              <div key={i} className="h-3.5 rounded shimmer" style={{ background: "var(--bg-2)", width: `${w}%` }} />
            ))}
          </div>
        )}
      </div>

      {/* Success criteria */}
      {spec?.success_criteria && spec.success_criteria.length > 0 && (
        <div className="mb-3">
          <div
            className="text-xs font-medium uppercase tracking-wide mb-2"
            style={{ color: "var(--fg-2)" }}
          >
            Success criteria
          </div>
          <ul className="space-y-1">
            {spec.success_criteria.map((c, i) => (
              <li key={i} className="text-sm flex items-start gap-2" style={{ color: "var(--fg-1)" }}>
                <span>•</span>
                <span>{c}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Suggested apps */}
      {suggestedApps && suggestedApps.length > 0 && (
        <div>
          <div
            className="text-xs font-medium uppercase tracking-wide mb-2"
            style={{ color: "var(--fg-2)" }}
          >
            Suggested integrations
          </div>
          <div className="flex flex-wrap gap-1.5">
            {suggestedApps.map((app) => (
              <span
                key={app}
                className="text-xs px-2 py-0.5"
                style={{
                  background: "var(--accent-soft)",
                  color: "var(--accent)",
                  borderRadius: "var(--r-pill)",
                }}
              >
                {app}
              </span>
            ))}
          </div>
        </div>
      )}

      {!hasAny && (
        <div className="text-sm mt-6 text-center" style={{ color: "var(--fg-2)" }}>
          Your agent spec will appear here as we chat…
        </div>
      )}
    </div>
  );
}
