"use client";

import { useEffect } from "react";
import { useParams, useSearchParams } from "next/navigation";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { AppShell } from "@/components/AppShell";
import { ConnectionToggle } from "@/components/ConnectionToggle";
import { api } from "@/lib/api";

export default function ConnectionsPage() {
  const { id } = useParams<{ id: string }>();
  const searchParams = useSearchParams();
  const qc = useQueryClient();

  // Handle OAuth callback
  const callbackConnId = searchParams.get("connection_id");
  useEffect(() => {
    if (callbackConnId) {
      qc.invalidateQueries({ queryKey: ["connections"] });
      toast.success("App connected successfully!");
    }
  }, [callbackConnId, qc]);

  const { data: projectData } = useQuery({
    queryKey: ["project", id],
    queryFn: () => api.getProject(id),
    enabled: !!id,
  });

  const { data: catalogData, isLoading: catalogLoading } = useQuery({
    queryKey: ["catalog"],
    queryFn: () => api.getCatalog(),
    staleTime: 60000,
  });

  const { data: connsData, isLoading: connsLoading } = useQuery({
    queryKey: ["connections"],
    queryFn: () => api.listConnections(),
    refetchOnWindowFocus: true,
  });

  const project = projectData?.project;
  const catalog = catalogData ?? [];
  const connections = connsData ?? [];
  const isLoading = catalogLoading || connsLoading;

  // Float recommended apps to top
  const requiredApps = new Set(
    (project?.spec as { tool_requirements?: { app: string }[] } | null)
      ?.tool_requirements?.map((r) => r.app) ?? []
  );

  const sorted = [...catalog].sort((a, b) => {
    const aRec = requiredApps.has(a.app) ? 0 : 1;
    const bRec = requiredApps.has(b.app) ? 0 : 1;
    return aRec - bRec;
  });

  return (
    <AppShell breadcrumb={project?.name ?? "Connect apps"}>
      <div className="max-w-xl mx-auto">
        <div className="mb-8">
          <h1 style={{ color: "var(--fg-0)" }}>Connect your apps</h1>
          <p className="text-sm mt-2" style={{ color: "var(--fg-1)" }}>
            Authorize once — reused across all your agents.
          </p>
        </div>

        {isLoading ? (
          <div className="space-y-3">
            {Array.from({ length: 5 }).map((_, i) => (
              <div
                key={i}
                className="shimmer h-16 rounded-card"
                style={{ border: "1px solid var(--stroke)" }}
              />
            ))}
          </div>
        ) : (
          <div className="space-y-3">
            {sorted.map((app) => {
              const conn = connections.find((c) => c.app === app.app);
              return (
                <ConnectionToggle
                  key={app.app}
                  app={app}
                  connection={conn}
                  recommended={requiredApps.has(app.app)}
                  onConnected={() =>
                    qc.invalidateQueries({ queryKey: ["connections"] })
                  }
                />
              );
            })}
          </div>
        )}
      </div>
    </AppShell>
  );
}
