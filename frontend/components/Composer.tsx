"use client";

import {
  useRef,
  useState,
  useCallback,
  KeyboardEvent,
  useEffect,
} from "react";
import { Send } from "lucide-react";
import { cn } from "@/lib/cn";

interface ComposerProps {
  onSend: (message: string) => void;
  disabled?: boolean;
  placeholder?: string;
  autoFocus?: boolean;
}

const PLACEHOLDERS = [
  "Ask your coach anything…",
  "How was my last run?",
  "What should I train this week?",
];

export function Composer({ onSend, disabled, placeholder, autoFocus }: ComposerProps) {
  const ref = useRef<HTMLTextAreaElement>(null);
  const [value, setValue] = useState("");
  const [phIdx, setPhIdx] = useState(0);

  useEffect(() => {
    if (autoFocus) ref.current?.focus();
  }, [autoFocus]);

  useEffect(() => {
    if (placeholder) return;
    const interval = setInterval(() => {
      setPhIdx((i) => (i + 1) % PLACEHOLDERS.length);
    }, 4000);
    return () => clearInterval(interval);
  }, [placeholder]);

  function autoResize() {
    const el = ref.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = Math.min(el.scrollHeight, 200) + "px";
  }

  const handleSubmit = useCallback(() => {
    const msg = value.trim();
    if (!msg || disabled) return;
    onSend(msg);
    setValue("");
    if (ref.current) {
      ref.current.style.height = "auto";
    }
  }, [value, disabled, onSend]);

  function handleKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.metaKey && !e.ctrlKey && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  }

  const canSend = value.trim().length > 0 && !disabled;

  return (
    <div
      className="flex items-end gap-3 p-3 rounded-card"
      style={{
        background: "var(--bg-2)",
        border: "1px solid var(--stroke)",
      }}
    >
      <textarea
        ref={ref}
        value={value}
        onChange={(e) => {
          setValue(e.target.value);
          autoResize();
        }}
        onKeyDown={handleKeyDown}
        placeholder={placeholder ?? PLACEHOLDERS[phIdx]}
        disabled={disabled}
        rows={1}
        className={cn(
          "flex-1 bg-transparent resize-none outline-none text-sm leading-relaxed",
          "placeholder:text-fg-2 disabled:opacity-50"
        )}
        style={{
          color: "var(--fg-0)",
          fontFamily: "var(--font-sans)",
          maxHeight: 200,
        }}
        aria-label="Message input"
      />
      <button
        onClick={handleSubmit}
        disabled={!canSend}
        className={cn(
          "shrink-0 flex items-center justify-center w-8 h-8 rounded-md transition-all duration-150",
          canSend
            ? "opacity-100 hover:scale-105"
            : "opacity-30 cursor-not-allowed"
        )}
        style={{
          background: canSend ? "var(--accent)" : "var(--bg-3)",
          borderRadius: "var(--r-sm)",
        }}
        aria-label="Send message"
      >
        {disabled ? (
          <span className="w-3 h-3 rounded-full border-2 border-white/40 border-t-white/90 animate-spin block" />
        ) : (
          <Send size={14} color="white" />
        )}
      </button>
    </div>
  );
}
