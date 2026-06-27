"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { AgentAvatar } from "./AgentAvatar";
import type { ProjectSpec } from "@/lib/types.gen";

interface ProposalCardProps {
  spec: ProjectSpec;
  suggestedApps: string[];
}

export function ProposalCard({ spec, suggestedApps }: ProposalCardProps) {
  const router = useRouter();
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleCreate() {
    setCreating(true);
    setError(null);
    try {
      const { project } = await api.createProject(spec, []);
      router.push(`/project/${project.id}/provisioning`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create project");
      setCreating(false);
    }
  }

  return (
    <div
      className="rounded-card p-5 mt-3"
      style={{
        background: "var(--bg-2)",
        border: "1px solid var(--stroke-strong)",
      }}
    >
      {/* Header */}
      <div
        className="text-xs font-medium uppercase tracking-wide mb-4"
        style={{ color: "var(--ok)" }}
      >
        ✓ Agent spec ready
      </div>

      {/* Agent identity */}
      <div className="flex items-center gap-3 mb-4">
        <AgentAvatar seed={spec.avatar_seed ?? spec.name} size={40} ring />
        <div>
          <div className="font-semibold" style={{ color: "var(--fg-0)" }}>
            {spec.name}
          </div>
          <div className="text-sm" style={{ color: "var(--fg-1)" }}>
            {spec.goal}
          </div>
        </div>
      </div>

      {/* Tasks */}
      <ul className="space-y-1 mb-4">
        {spec.tasks.slice(0, 3).map((t, i) => (
          <li
            key={i}
            className="text-sm flex items-center gap-2"
            style={{ color: "var(--fg-1)" }}
          >
            <span style={{ color: "var(--accent)" }}>✓</span>
            {t.title}
          </li>
        ))}
        {spec.tasks.length > 3 && (
          <li className="text-sm" style={{ color: "var(--fg-2)" }}>
            +{spec.tasks.length - 3} more…
          </li>
        )}
      </ul>

      {/* Suggested apps */}
      {suggestedApps.length > 0 && (
        <div className="flex flex-wrap gap-1.5 mb-4">
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
      )}

      {error && (
        <p className="text-sm mb-3" style={{ color: "var(--err)" }}>
          {error}
        </p>
      )}

      {/* Create button */}
      <button
        onClick={handleCreate}
        disabled={creating}
        className="w-full py-2.5 text-sm font-medium rounded-md transition-colors disabled:opacity-60"
        style={{
          background: creating ? "var(--accent-hover)" : "var(--accent)",
          color: "white",
          borderRadius: "var(--r-md)",
        }}
      >
        {creating ? "Creating agent…" : "Create agent →"}
      </button>
    </div>
  );
}
