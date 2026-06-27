"use client";

import { useState, useCallback, useEffect } from "react";
import { api } from "./api";
import { sseStream } from "./sse";
import type { RuntimeEvent, DbMessage } from "./types.gen";

export interface StreamAction {
  label: string;
  detail: string | null;
  ts: number;
}

export type AgentStatus = "idle" | "loading" | "streaming" | "error";

export interface UseAgentStreamReturn {
  messages: DbMessage[];
  streamingText: string;
  actions: StreamAction[];
  status: AgentStatus;
  error: string | null;
  send: (message: string) => Promise<void>;
}

export function useAgentStream(
  projectId: string,
  onAction?: (action: StreamAction) => void
): UseAgentStreamReturn {
  const [messages, setMessages] = useState<DbMessage[]>([]);
  const [streamingText, setStreamingText] = useState("");
  const [actions, setActions] = useState<StreamAction[]>([]);
  const [status, setStatus] = useState<AgentStatus>("loading");
  const [error, setError] = useState<string | null>(null);

  // Load history on mount
  useEffect(() => {
    if (!projectId) return;
    api
      .getMessages(projectId)
      .then(({ messages: msgs }) => {
        setMessages(msgs);
        setStatus("idle");
      })
      .catch(() => setStatus("idle"));
  }, [projectId]);

  const send = useCallback(
    async (message: string) => {
      if (status === "streaming") return;

      const optimisticMsg: DbMessage = {
        id: `optimistic-${Date.now()}`,
        project_id: projectId,
        role: "user",
        content: message,
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, optimisticMsg]);
      setStreamingText("");
      setError(null);
      setStatus("streaming");

      try {
        const res = await api.chatStream(projectId, message);
        if (!res.ok) throw new Error(`Stream error: ${res.status}`);

        let accumulated = "";

        for await (const event of sseStream<RuntimeEvent>(res)) {
          if (event.type === "delta") {
            accumulated += event.text;
            setStreamingText(accumulated);
          } else if (event.type === "action") {
            const action: StreamAction = {
              label: event.label,
              detail: event.detail ?? null,
              ts: Date.now(),
            };
            setActions((prev) => [action, ...prev]);
            onAction?.(action);
          } else if (event.type === "done") {
            if (accumulated.trim()) {
              const assistantMsg: DbMessage = {
                id: `assistant-${Date.now()}`,
                project_id: projectId,
                role: "assistant",
                content: accumulated,
                created_at: new Date().toISOString(),
              };
              setMessages((prev) => [...prev, assistantMsg]);
            }
            setStreamingText("");
            setStatus("idle");
            accumulated = "";
          } else if (event.type === "error") {
            setError(event.message);
            setStatus("error");
            setStreamingText("");
            return;
          }
        }

        // Stream ended without done
        if (accumulated.trim()) {
          setMessages((prev) => [
            ...prev,
            {
              id: `assistant-${Date.now()}`,
              project_id: projectId,
              role: "assistant",
              content: accumulated,
              created_at: new Date().toISOString(),
            },
          ]);
        }
        setStreamingText("");
        setStatus("idle");
      } catch (err) {
        setError(err instanceof Error ? err.message : "Stream failed");
        setStatus("error");
        setStreamingText("");
      }
    },
    [projectId, status, onAction]
  );

  return { messages, streamingText, actions, status, error, send };
}
