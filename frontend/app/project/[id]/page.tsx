"use client";

import { useCallback } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { toast } from "sonner";
import { Settings } from "lucide-react";
import { AppShell } from "@/components/AppShell";
import { AgentAvatar } from "@/components/AgentAvatar";
import { StatusDot } from "@/components/StatusDot";
import { ChatThread } from "@/components/ChatThread";
import { Composer } from "@/components/Composer";
import { SidePanel } from "@/components/SidePanel";
import { api } from "@/lib/api";
import { useAgentStream, type StreamAction } from "@/lib/useAgentStream";

export default function ProjectChatPage() {
  const { id } = useParams<{ id: string }>();

  const { data: projectData } = useQuery({
    queryKey: ["project", id],
    queryFn: () => api.getProject(id),
    enabled: !!id,
  });

  const { data: memoryData } = useQuery({
    queryKey: ["memory", id],
    queryFn: () => api.getMemory(id),
    enabled: !!id,
    staleTime: 30000,
  });

  const project = projectData?.project;
  const memory = memoryData?.memory ?? [];

  const handleAction = useCallback((action: StreamAction) => {
    toast(action.label, {
      description: action.detail ?? undefined,
      duration: 4000,
    });
  }, []);

  const { messages, streamingText, actions, status, send } = useAgentStream(
    id,
    handleAction
  );

  const breadcrumb = project ? (
    <span style={{ color: "var(--fg-1)" }}>{project.name}</span>
  ) : null;

  return (
    <AppShell breadcrumb={breadcrumb}>
      {/* Project header */}
      <div
        className="flex items-center gap-3 pb-5 mb-5"
        style={{ borderBottom: "1px solid var(--stroke)" }}
      >
        <AgentAvatar
          seed={project?.avatar_seed ?? project?.name ?? "agent"}
          size={40}
          ring
        />
        <div className="flex-1 min-w-0">
          <h2 className="truncate" style={{ color: "var(--fg-0)", fontSize: 18 }}>
            {project?.name ?? "Loading…"}
          </h2>
          {project?.goal && (
            <p className="text-sm truncate" style={{ color: "var(--fg-1)" }}>
              {project.goal}
            </p>
          )}
        </div>
        <div className="flex items-center gap-3">
          <StatusDot state={project?.status ?? "ready"} />
          <Link
            href={`/project/${id}/connections`}
            className="flex items-center gap-1.5 text-xs transition-colors"
            style={{ color: "var(--fg-2)" }}
            onMouseEnter={(e) =>
              ((e.currentTarget as HTMLElement).style.color = "var(--fg-1)")
            }
            onMouseLeave={(e) =>
              ((e.currentTarget as HTMLElement).style.color = "var(--fg-2)")
            }
          >
            <Settings size={14} />
            Manage apps
          </Link>
        </div>
      </div>

      {/* Two-pane layout */}
      <div className="flex gap-6 h-[calc(100vh-240px)]">
        {/* Left: chat */}
        <div className="flex-[7] min-w-0 flex flex-col">
          <ChatThread
            messages={messages}
            streamingText={streamingText}
            agentName={project?.name}
            agentSeed={project?.avatar_seed ?? project?.name ?? "agent"}
            loading={status === "loading"}
          />
          <div className="shrink-0 mt-3">
            <Composer
              onSend={send}
              disabled={status === "streaming"}
              placeholder={`Ask ${project?.name ?? "your agent"} anything…`}
              autoFocus
            />
          </div>
        </div>

        {/* Right: side panel */}
        <div
          className="flex-[3] min-w-0 pt-1"
          style={{ borderLeft: "1px solid var(--stroke)", paddingLeft: 24 }}
        >
          <SidePanel memory={memory} actions={actions} />
        </div>
      </div>
    </AppShell>
  );
}
