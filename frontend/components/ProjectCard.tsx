"use client";

import { useRouter } from "next/navigation";
import { AgentAvatar } from "./AgentAvatar";
import { StatusDot } from "./StatusDot";
import { cn } from "@/lib/cn";
import type { DbProject } from "@/lib/types.gen";

const PROVISIONING_TRANSIENT = new Set([
  "compiling", "connecting", "provisioning", "ingesting",
]);

interface ProjectCardProps {
  project: DbProject;
}

export function ProjectCard({ project }: ProjectCardProps) {
  const router = useRouter();
  const isTransient = PROVISIONING_TRANSIENT.has(project.status);

  function handleClick() {
    if (project.status === "ready") {
      router.push(`/project/${project.id}`);
    } else {
      router.push(`/project/${project.id}/provisioning`);
    }
  }

  return (
    <button
      onClick={handleClick}
      className={cn(
        "group relative w-full text-left overflow-hidden transition-all duration-200",
        "hover:-translate-y-0.5 focus-visible:ring-2"
      )}
      style={{
        background: "var(--bg-1)",
        border: "1px solid var(--stroke)",
        borderRadius: "var(--r-card)",
        padding: "20px",
        boxShadow: "var(--shadow-1)",
        cursor: "pointer",
      }}
      onMouseEnter={(e) => {
        (e.currentTarget as HTMLElement).style.borderColor = "var(--stroke-strong)";
        (e.currentTarget as HTMLElement).style.boxShadow = "var(--shadow-2)";
      }}
      onMouseLeave={(e) => {
        (e.currentTarget as HTMLElement).style.borderColor = "var(--stroke)";
        (e.currentTarget as HTMLElement).style.boxShadow = "var(--shadow-1)";
      }}
    >
      {/* Top: avatar + name + goal */}
      <div className="flex items-start gap-3 mb-4">
        <AgentAvatar
          seed={project.avatar_seed ?? project.name}
          size={48}
          ring={project.status === "ready"}
        />
        <div className="flex-1 min-w-0">
          <h3
            className="font-semibold truncate leading-snug"
            style={{ color: "var(--fg-0)", fontSize: 15 }}
          >
            {project.name}
          </h3>
          <p
            className="text-sm mt-0.5 line-clamp-2 leading-relaxed"
            style={{ color: "var(--fg-1)" }}
          >
            {project.goal ?? "No goal set"}
          </p>
        </div>
      </div>

      {/* Bottom: status */}
      <div className="flex items-center justify-between">
        <StatusDot state={project.status} />
      </div>

      {/* Provisioning accent bar at bottom */}
      {isTransient && (
        <div
          className="absolute bottom-0 left-0 right-0 h-0.5 animate-pulse"
          style={{ background: "var(--accent)" }}
        />
      )}
    </button>
  );
}
