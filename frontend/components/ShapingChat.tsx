"use client";

import { useRef, useEffect } from "react";
import { useShapingStream } from "@/lib/useShapingStream";
import { Composer } from "./Composer";
import { QuestionChips } from "./QuestionChips";
import { ProposalCard } from "./ProposalCard";
import { TypingCursor } from "./TypingCursor";
import { cn } from "@/lib/cn";
import type { ProjectSpec } from "@/lib/types.gen";

interface ShapingChatProps {
  onSpecUpdate?: (spec: Partial<ProjectSpec> | null) => void;
  onSuggestedApps?: (apps: string[]) => void;
}

const EXAMPLE_CHIPS = [
  "A sports coach 🏃",
  "An inbox triager 📧",
  "A daily journal companion 📝",
];

export function ShapingChat({ onSpecUpdate, onSuggestedApps }: ShapingChatProps) {
  const {
    messages,
    streamingText,
    currentQuestion,
    partialSpec,
    proposal,
    suggestedApps,
    status,
    error,
    send,
  } = useShapingStream();

  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, streamingText]);

  useEffect(() => {
    onSpecUpdate?.(partialSpec);
  }, [partialSpec, onSpecUpdate]);

  useEffect(() => {
    onSuggestedApps?.(suggestedApps);
  }, [suggestedApps, onSuggestedApps]);

  const isEmpty = messages.length === 0 && !streamingText;

  return (
    <div className="flex flex-col h-full min-h-0">
      {/* Message area */}
      <div className="flex-1 overflow-y-auto pr-1 space-y-4 pb-4">
        {isEmpty && (
          <div className="flex flex-col items-center justify-center h-full pt-16 gap-6">
            <div className="text-center">
              <h2 className="mb-2" style={{ color: "var(--fg-0)" }}>
                What do you want an agent for?
              </h2>
              <p className="text-sm" style={{ color: "var(--fg-1)" }}>
                Describe your idea — we&apos;ll shape it into a ready agent together.
              </p>
            </div>
            <div className="flex flex-wrap gap-2 justify-center">
              {EXAMPLE_CHIPS.map((chip) => (
                <button
                  key={chip}
                  onClick={() => send(chip)}
                  className="px-3 py-1.5 text-sm rounded-pill border transition-colors hover:border-accent hover:text-accent"
                  style={{
                    borderColor: "var(--stroke)",
                    color: "var(--fg-1)",
                    borderRadius: "var(--r-pill)",
                  }}
                >
                  {chip}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg, i) => (
          <div
            key={i}
            className={cn(
              "flex",
              msg.role === "user" ? "justify-end" : "justify-start"
            )}
          >
            {msg.role === "user" ? (
              <div
                className="max-w-[78%] px-4 py-2.5 text-sm rounded-card leading-relaxed"
                style={{
                  background: "var(--bg-2)",
                  color: "var(--fg-0)",
                  borderRadius: "var(--r-md) var(--r-md) 4px var(--r-md)",
                }}
              >
                {msg.content}
              </div>
            ) : (
              <div className="max-w-[88%] text-sm leading-relaxed" style={{ color: "var(--fg-0)" }}>
                {msg.content}
                {/* Show question chips after this message if it's the last assistant msg */}
                {i === messages.length - 1 && currentQuestion && (
                  <QuestionChips
                    options={currentQuestion.options}
                    onPick={(opt) => send(opt)}
                  />
                )}
                {/* Show proposal card */}
                {i === messages.length - 1 && proposal && (
                  <ProposalCard spec={proposal} suggestedApps={suggestedApps} />
                )}
              </div>
            )}
          </div>
        ))}

        {/* Streaming assistant message */}
        {streamingText && (
          <div className="flex justify-start">
            <div
              className="max-w-[88%] text-sm leading-relaxed"
              style={{ color: "var(--fg-0)" }}
              aria-live="polite"
            >
              {streamingText}
              <TypingCursor />
            </div>
          </div>
        )}

        {/* Question chips when no messages yet (first turn) */}
        {!streamingText && currentQuestion && messages.length === 0 && (
          <div>
            <div className="text-sm mb-2" style={{ color: "var(--fg-1)" }}>
              {currentQuestion.prompt}
            </div>
            <QuestionChips
              options={currentQuestion.options}
              onPick={(opt) => send(opt)}
            />
          </div>
        )}

        {error && (
          <div
            className="text-sm px-4 py-2 rounded-md"
            style={{ background: "rgba(248,81,73,0.08)", color: "var(--err)" }}
          >
            {error} — type to retry.
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Composer */}
      {!proposal && (
        <div className="shrink-0 mt-4">
          <Composer
            onSend={send}
            disabled={status === "streaming"}
            placeholder="Describe the agent you want…"
            autoFocus
          />
          <p className="text-xs mt-2 text-center" style={{ color: "var(--fg-2)" }}>
            Enter to send · ⌘↵ for newline
          </p>
        </div>
      )}
    </div>
  );
}
