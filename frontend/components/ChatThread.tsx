"use client";

import { useRef, useEffect, useState } from "react";
import { MessageBubble } from "./MessageBubble";
import type { DbMessage } from "@/lib/types.gen";

interface ChatThreadProps {
  messages: DbMessage[];
  streamingText: string;
  agentName?: string;
  agentSeed?: string;
  loading?: boolean;
}

export function ChatThread({
  messages,
  streamingText,
  agentName,
  agentSeed,
  loading,
}: ChatThreadProps) {
  const bottomRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [userScrolled, setUserScrolled] = useState(false);
  const [newMessages, setNewMessages] = useState(false);

  function scrollToBottom() {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
    setNewMessages(false);
  }

  useEffect(() => {
    if (!userScrolled) {
      scrollToBottom();
    } else {
      setNewMessages(true);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [messages.length, streamingText]);

  function handleScroll() {
    const el = containerRef.current;
    if (!el) return;
    const atBottom = el.scrollTop + el.clientHeight >= el.scrollHeight - 60;
    setUserScrolled(!atBottom);
    if (atBottom) setNewMessages(false);
  }

  if (loading) {
    return (
      <div className="flex-1 space-y-4 py-4">
        {[80, 60, 90].map((w, i) => (
          <div key={i} className="flex items-start gap-3">
            <div className="w-8 h-8 rounded-md shimmer shrink-0" style={{ background: "var(--bg-2)" }} />
            <div className="space-y-2 flex-1">
              <div className="h-3.5 rounded shimmer" style={{ background: "var(--bg-2)", width: `${w}%` }} />
              <div className="h-3.5 rounded shimmer" style={{ background: "var(--bg-2)", width: `${w - 20}%` }} />
            </div>
          </div>
        ))}
      </div>
    );
  }

  const isEmpty = messages.length === 0 && !streamingText;

  return (
    <div className="relative flex-1 min-h-0">
      <div
        ref={containerRef}
        className="h-full overflow-y-auto py-4 pr-2"
        onScroll={handleScroll}
      >
        {isEmpty && (
          <div className="flex flex-col items-center justify-center h-full gap-4 py-12">
            <div className="text-3xl">👋</div>
            <div className="text-center">
              <p className="text-sm font-medium" style={{ color: "var(--fg-0)" }}>
                {agentName ?? "Your agent"} is ready
              </p>
              <p className="text-sm mt-1" style={{ color: "var(--fg-1)" }}>
                Ask anything — it knows your context.
              </p>
            </div>
          </div>
        )}

        {messages.map((msg) => (
          <MessageBubble
            key={msg.id}
            role={msg.role as "user" | "assistant"}
            content={msg.content}
            agentSeed={agentSeed}
          />
        ))}

        {streamingText && (
          <MessageBubble
            role="assistant"
            content={streamingText}
            streaming
            agentSeed={agentSeed}
          />
        )}

        <div ref={bottomRef} />
      </div>

      {/* New messages pill */}
      {userScrolled && newMessages && (
        <button
          onClick={scrollToBottom}
          className="absolute bottom-2 left-1/2 -translate-x-1/2 px-3 py-1.5 text-xs font-medium rounded-pill shadow-shadow-2 transition-all"
          style={{
            background: "var(--accent)",
            color: "white",
            borderRadius: "var(--r-pill)",
          }}
        >
          ↓ New message
        </button>
      )}
    </div>
  );
}
