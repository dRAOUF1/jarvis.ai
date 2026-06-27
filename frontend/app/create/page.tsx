"use client";

import { useState } from "react";
import { AppShell } from "@/components/AppShell";
import { ShapingChat } from "@/components/ShapingChat";
import { SpecCard } from "@/components/SpecCard";
import type { ProjectSpec } from "@/lib/types.gen";

export default function CreatePage() {
  const [partialSpec, setPartialSpec] = useState<Partial<ProjectSpec> | null>(null);
  const [suggestedApps, setSuggestedApps] = useState<string[]>([]);

  return (
    <AppShell breadcrumb="New agent">
      <div className="flex gap-6 h-[calc(100vh-120px)]">
        {/* Left: Shaping chat */}
        <div className="flex-[3] min-w-0">
          <ShapingChat
            onSpecUpdate={setPartialSpec}
            onSuggestedApps={setSuggestedApps}
          />
        </div>

        {/* Right: live spec card */}
        <div className="flex-[2] sticky top-20 hidden lg:block self-start max-h-[calc(100vh-130px)] overflow-y-auto">
          <SpecCard spec={partialSpec} suggestedApps={suggestedApps} />
        </div>
      </div>
    </AppShell>
  );
}
