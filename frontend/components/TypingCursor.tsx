"use client";

export function TypingCursor() {
  return (
    <span
      className="inline-block w-px h-4 align-middle ml-0.5 animate-blink"
      style={{ background: "var(--accent)" }}
      aria-hidden
    />
  );
}
