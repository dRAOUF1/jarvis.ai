"use client";

import { useState, useCallback } from "react";
import { api } from "./api";
import { sseStream } from "./sse";
import type { ShapingEvent, ProjectSpec } from "./types.gen";

export interface ShapingMessage {
  role: "user" | "assistant";
  content: string;
}

export interface QuestionState {
  field: string;
  prompt: string;
  options: string[];
}

export type ShapingStatus = "idle" | "streaming" | "error";

export interface UseShapingStreamReturn {
  messages: ShapingMessage[];
  streamingText: string;
  currentQuestion: QuestionState | null;
  partialSpec: Partial<ProjectSpec> | null;
  proposal: ProjectSpec | null;
  suggestedApps: string[];
  status: ShapingStatus;
  error: string | null;
  send: (message: string) => Promise<void>;
}

function deepMerge(
  target: Partial<ProjectSpec>,
  patch: Record<string, unknown>
): Partial<ProjectSpec> {
  const result = { ...target };
  for (const key of Object.keys(patch) as (keyof ProjectSpec)[]) {
    const val = patch[key as string];
    if (Array.isArray(val)) {
      (result as Record<string, unknown>)[key] = val;
    } else if (val && typeof val === "object") {
      (result as Record<string, unknown>)[key] = {
        ...((result as Record<string, unknown>)[key] ?? {}),
        ...(val as object),
      };
    } else if (val !== undefined) {
      (result as Record<string, unknown>)[key] = val;
    }
  }
  return result;
}

export function useShapingStream(): UseShapingStreamReturn {
  const [messages, setMessages] = useState<ShapingMessage[]>([]);
  const [streamingText, setStreamingText] = useState("");
  const [currentQuestion, setCurrentQuestion] = useState<QuestionState | null>(null);
  const [partialSpec, setPartialSpec] = useState<Partial<ProjectSpec> | null>(null);
  const [proposal, setProposal] = useState<ProjectSpec | null>(null);
  const [suggestedApps, setSuggestedApps] = useState<string[]>([]);
  const [status, setStatus] = useState<ShapingStatus>("idle");
  const [error, setError] = useState<string | null>(null);
  const [history, setHistory] = useState<{ role: string; content: string }[]>([]);

  const send = useCallback(
    async (message: string) => {
      if (status === "streaming") return;

      const userMsg: ShapingMessage = { role: "user", content: message };
      setMessages((prev) => [...prev, userMsg]);
      setStreamingText("");
      setCurrentQuestion(null);
      setStatus("streaming");
      setError(null);

      const newHistory = [...history, { role: "user", content: message }];

      try {
        const res = await api.shapeStream(message, history);
        if (!res.ok) throw new Error(`Stream error: ${res.status}`);

        let accumulated = "";

        for await (const event of sseStream<ShapingEvent>(res)) {
          if (event.type === "delta") {
            accumulated += event.text;
            setStreamingText(accumulated);
          } else if (event.type === "question") {
            // Commit accumulated text as assistant message, then show question
            if (accumulated.trim()) {
              const assistantMsg: ShapingMessage = {
                role: "assistant",
                content: accumulated,
              };
              setMessages((prev) => [...prev, assistantMsg]);
              newHistory.push({ role: "assistant", content: accumulated });
              accumulated = "";
              setStreamingText("");
            }
            setCurrentQuestion(event.question);
          } else if (event.type === "spec_update") {
            setPartialSpec((prev) =>
              deepMerge(prev ?? {}, event.spec_update as Record<string, unknown>)
            );
          } else if (event.type === "proposal") {
            setProposal(event.spec);
            setSuggestedApps(event.suggested_apps ?? []);
            setPartialSpec(event.spec);
          } else if (event.type === "done") {
            // Flush remaining streaming text
            if (accumulated.trim()) {
              const assistantMsg: ShapingMessage = {
                role: "assistant",
                content: accumulated,
              };
              setMessages((prev) => [...prev, assistantMsg]);
              newHistory.push({ role: "assistant", content: accumulated });
            }
            setStreamingText("");
            setStatus("idle");
            setHistory(newHistory);
          }
        }

        // Stream ended without done event
        if (accumulated.trim()) {
          setMessages((prev) => [
            ...prev,
            { role: "assistant", content: accumulated },
          ]);
        }
        setStreamingText("");
        setStatus("idle");
        setHistory(newHistory);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Stream failed");
        setStatus("error");
        setStreamingText("");
      }
    },
    [status, history]
  );

  return {
    messages,
    streamingText,
    currentQuestion,
    partialSpec,
    proposal,
    suggestedApps,
    status,
    error,
    send,
  };
}
