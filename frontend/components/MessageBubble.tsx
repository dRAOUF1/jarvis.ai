"use client";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { AgentAvatar } from "./AgentAvatar";
import { TypingCursor } from "./TypingCursor";
import { cn } from "@/lib/cn";

interface MessageBubbleProps {
  role: "user" | "assistant";
  content: string;
  streaming?: boolean;
  agentSeed?: string;
}

export function MessageBubble({ role, content, streaming, agentSeed }: MessageBubbleProps) {
  if (role === "user") {
    return (
      <div className="flex justify-end mb-4">
        <div
          className="max-w-[75%] px-4 py-2.5 text-sm leading-relaxed"
          style={{
            background: "var(--bg-2)",
            color: "var(--fg-0)",
            borderRadius: "var(--r-md) var(--r-md) 4px var(--r-md)",
          }}
        >
          {content}
        </div>
      </div>
    );
  }

  return (
    <div className="flex items-start gap-3 mb-4">
      <AgentAvatar seed={agentSeed ?? "agent"} size={32} />
      <div className="flex-1 min-w-0">
        <div
          className={cn(
            "text-sm leading-relaxed",
            "prose prose-invert prose-sm max-w-none",
            "[&_p]:mt-0 [&_p]:mb-2 [&_p:last-child]:mb-0",
            "[&_ul]:my-2 [&_ol]:my-2 [&_li]:my-0.5",
            "[&_code]:text-xs [&_code]:bg-bg-2 [&_code]:px-1 [&_code]:py-0.5 [&_code]:rounded",
            "[&_pre]:bg-bg-2 [&_pre]:p-3 [&_pre]:rounded-md [&_pre]:text-xs [&_pre]:overflow-x-auto",
            "[&_strong]:text-fg-0 [&_strong]:font-semibold",
            "[&_h1]:text-fg-0 [&_h2]:text-fg-0 [&_h3]:text-fg-0"
          )}
          style={{ color: "var(--fg-0)" }}
          aria-live={streaming ? "polite" : undefined}
        >
          <ReactMarkdown remarkPlugins={[remarkGfm]}>{content}</ReactMarkdown>
          {streaming && <TypingCursor />}
        </div>
      </div>
    </div>
  );
}
