"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { AppShell } from "@/components/AppShell";
import { ProjectGrid } from "@/components/ProjectGrid";
import { api } from "@/lib/api";
import type { DbProject } from "@/lib/types.gen";

export default function DashboardPage() {
  const { data, isLoading, error } = useQuery({
    queryKey: ["projects"],
    queryFn: () => api.listProjects(),
    refetchInterval: 3000,
  });

  const projects: DbProject[] = data?.projects ?? [];

  return (
    <AppShell>
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 style={{ color: "var(--fg-0)" }}>Your agents</h1>
          {!isLoading && (
            <p className="text-sm mt-1" style={{ color: "var(--fg-2)" }}>
              {projects.length === 0
                ? "Get started by shaping your first agent"
                : `${projects.length} agent${projects.length !== 1 ? "s" : ""}`}
            </p>
          )}
        </div>
        <Link
          href="/create"
          className="flex items-center gap-2 px-4 py-2 text-sm font-medium transition-colors"
          style={{
            background: "var(--accent)",
            color: "white",
            borderRadius: "var(--r-md)",
          }}
          onMouseEnter={(e) =>
            ((e.currentTarget as HTMLElement).style.background = "var(--accent-hover)")
          }
          onMouseLeave={(e) =>
            ((e.currentTarget as HTMLElement).style.background = "var(--accent)")
          }
        >
          + New agent
        </Link>
      </div>

      {error ? (
        <div
          className="p-4 rounded-md text-sm"
          style={{ background: "rgba(248,81,73,0.08)", color: "var(--err)" }}
        >
          Failed to load agents. Check backend is running.{" "}
          <button
            onClick={() => window.location.reload()}
            className="underline"
          >
            Retry
          </button>
        </div>
      ) : (
        <ProjectGrid projects={projects} loading={isLoading} />
      )}
    </AppShell>
  );
}
