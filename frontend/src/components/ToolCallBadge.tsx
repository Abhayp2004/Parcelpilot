import { useState } from "react";
import type { ToolCall } from "../types";

const COLOR_MAP: Record<string, string> = {
  search_documents: "border-blue-200 bg-blue-50 text-blue-800",
  lookup_data: "border-emerald-200 bg-emerald-50 text-emerald-800",
  prepare_action: "border-amber-200 bg-amber-50 text-amber-800",
};

export function ToolCallBadge({ toolCall }: { toolCall: ToolCall }) {
  const [expanded, setExpanded] = useState(false);
  const tone = COLOR_MAP[toolCall.tool] ?? "border-slate-200 bg-slate-50 text-slate-800";

  return (
    <div className={`overflow-hidden rounded-2xl border ${tone}`}>
      <button
        type="button"
        className="flex min-h-12 w-full items-center justify-between gap-3 px-4 py-3 text-left text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2"
        onClick={() => setExpanded((value) => !value)}
      >
        <span className="flex items-center gap-3 font-semibold">
          <span className="flex h-8 w-8 items-center justify-center rounded-xl bg-white/70 text-ink" aria-hidden="true">
            ◇
          </span>
          {toolCall.tool}
        </span>
        <span className="font-mono text-xs font-medium uppercase tracking-[0.18em] text-blue-600">
          {expanded ? "Hide" : "View"} ›
        </span>
      </button>
      {expanded ? (
        <div className="space-y-3 border-t border-current/10 bg-white/70 px-4 py-4 text-xs text-ink">
          <div>
            <p className="mb-1 font-mono font-medium uppercase tracking-[0.16em] text-ink">Input</p>
            <pre className="overflow-x-auto whitespace-pre-wrap rounded-xl bg-slate-950 p-3 font-mono text-slate-100">
              {toolCall.input}
            </pre>
          </div>
          <div>
            <p className="mb-1 font-mono font-medium uppercase tracking-[0.16em] text-ink">Output</p>
            <pre className="max-h-64 overflow-auto whitespace-pre-wrap rounded-xl bg-slate-950 p-3 font-mono text-slate-100">
              {toolCall.output}
            </pre>
          </div>
        </div>
      ) : null}
    </div>
  );
}
