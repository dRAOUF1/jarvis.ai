"use client";

import { useEffect, useRef, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { AppShell } from "@/components/AppShell";
import { AgentAvatar } from "@/components/AgentAvatar";
import { ProvisioningProgress } from "@/components/ProvisioningProgress";
import { api } from "@/lib/api";
import { cn } from "@/lib/cn";

const MIN_CINEMATIC_MS = 2500;

export default function ProvisioningPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const startTs = useRef(Date.now());
  const [ready, setReady] = useState(false);

  const { data: statusData } = useQuery({
    queryKey: ["status", id],
    queryFn: () => api.getStatus(id),
    refetchInterval: (q) => {
      const s = q.state.data?.status;
      if (s === "ready" || s === "failed") return false;
      return 900;
    },
    enabled: !!id,
  });

  const { data: projectData } = useQuery({
    queryKey: ["project", id],
    queryFn: () => api.getProject(id),
    enabled: !!id,
  });

  const status = statusData?.status ?? "compiling";
  const failedStage = statusData?.failed_stage ?? null;
  const project = projectData?.project;

  useEffect(() => {
    if (status === "ready" && !ready) {
      const elapsed = Date.now() - startTs.current;
      const remaining = Math.max(0, MIN_CINEMATIC_MS - elapsed);
      const timer = setTimeout(() => {
        setReady(true);
        setTimeout(() => router.push(`/project/${id}`), 1200);
      }, remaining);
      return () => clearTimeout(timer);
    }
  }, [status, ready, id, router]);

  const isInFlight = status !== "ready" && status !== "failed";

  return (
    <AppShell breadcrumb={project?.name ?? "Agent"}>
      <div className="flex flex-col items-center justify-center min-h-[calc(100vh-180px)] gap-10">
        {/* Avatar with breathing halo */}
        <div className="relative flex items-center justify-center">
          {isInFlight && (
            <div
              className="absolute rounded-card animate-halo-pulse"
              style={{
                inset: -20,
                background: "radial-gradient(circle, var(--accent-soft) 0%, transparent 70%)",
                borderRadius: "var(--r-lg)",
              }}
            />
          )}
          {ready && (
            <div
              className="absolute rounded-card transition-all duration-700"
              style={{
                inset: -16,
                boxShadow: "var(--shadow-glow)",
                borderRadius: "var(--r-lg)",
              }}
            />
          )}
          <AgentAvatar
            seed={project?.avatar_seed ?? project?.name ?? "agent"}
            size={96}
            ring={ready}
          />
        </div>

        {/* Status copy */}
        <div className="text-center">
          {status === "failed" ? (
            <>
              <h2 style={{ color: "var(--err)" }}>Something went wrong</h2>
              {failedStage && (
                <p className="text-sm mt-2" style={{ color: "var(--fg-1)" }}>
                  Failed at: {failedStage}
                </p>
              )}
            </>
          ) : ready ? (
            <>
              <h2 style={{ color: "var(--fg-0)" }}>
                {project?.name ?? "Your agent"} is ready
              </h2>
              <p className="text-sm mt-2" style={{ color: "var(--fg-1)" }}>
                Redirecting you to chat…
              </p>
            </>
          ) : (
            <>
              <h2 style={{ color: "var(--fg-0)" }}>
                Building {project?.name ?? "your agent"}…
              </h2>
              <p className="text-sm mt-2" style={{ color: "var(--fg-1)" }}>
                This takes about 20–40 seconds
              </p>
            </>
          )}
        </div>

        {/* FSM timeline */}
        <div className="w-64">
          <ProvisioningProgress status={status} failedStage={failedStage} />
        </div>

        {/* CTA buttons */}
        {ready && (
          <button
            onClick={() => router.push(`/project/${id}`)}
            className="px-6 py-3 rounded-md font-medium text-sm transition-transform hover:scale-105"
            style={{ background: "var(--accent)", color: "white", borderRadius: "var(--r-md)" }}
          >
            Start chatting →
          </button>
        )}

        {status === "failed" && (
          <div className="flex gap-3">
            <button
              onClick={() => router.push("/")}
              className="px-5 py-2.5 rounded-md text-sm border transition-colors"
              style={{
                borderColor: "var(--stroke)",
                color: "var(--fg-1)",
                borderRadius: "var(--r-md)",
              }}
            >
              Back to dashboard
            </button>
          </div>
        )}
      </div>
    </AppShell>
  );
}
