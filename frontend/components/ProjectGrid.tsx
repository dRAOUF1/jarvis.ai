"use client";

import { ProjectCard } from "./ProjectCard";
import { NewProjectCard } from "./NewProjectCard";
import Link from "next/link";
import type { DbProject } from "@/lib/types.gen";

interface ProjectGridProps {
  projects: DbProject[];
  loading?: boolean;
}

function SkeletonCard() {
  return (
    <div
      className="shimmer rounded-card p-5 min-h-[140px]"
      style={{ border: "1px solid var(--stroke)" }}
    />
  );
}

export function ProjectGrid({ projects, loading }: ProjectGridProps) {
  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-5">
        {Array.from({ length: 6 }).map((_, i) => (
          <SkeletonCard key={i} />
        ))}
      </div>
    );
  }

  if (projects.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-24 gap-4">
        <div
          className="w-16 h-16 rounded-card flex items-center justify-center text-3xl"
          style={{ background: "var(--bg-2)" }}
        >
          ✦
        </div>
        <h2 style={{ color: "var(--fg-0)" }}>No agents yet</h2>
        <p className="text-sm text-center max-w-xs" style={{ color: "var(--fg-1)" }}>
          Shape your first agent — describe what you need and we&apos;ll build it.
        </p>
        <Link
          href="/create"
          className="mt-2 px-5 py-2.5 rounded-md text-sm font-medium transition-colors"
          style={{
            background: "var(--accent)",
            color: "white",
            borderRadius: "var(--r-md)",
          }}
        >
          Shape your first agent →
        </Link>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-5">
      {projects.map((p) => (
        <ProjectCard key={p.id} project={p} />
      ))}
      <NewProjectCard />
    </div>
  );
}
