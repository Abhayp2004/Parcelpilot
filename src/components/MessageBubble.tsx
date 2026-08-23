import type { Message } from "../types";
import { ToolCallBadge } from "./ToolCallBadge";

function renderContent(content: string) {
  return content.split(/(\[[^\]]+\])/g).map((part, index) => {
    if (part.startsWith("[") && part.endsWith("]")) {
      return (
        <span
          key={`${part}-${index}`}
          className="inline-flex rounded-full border border-blue-200 bg-blue-50 px-2 py-1 text-xs font-medium text-blue-700"
        >
          {part}
        </span>
      );
    }

    return (
      <span key={`${part}-${index}`} className="whitespace-pre-wrap">
        {part}
      </span>
    );
  });
}

export function MessageBubble({ message }: { message: Message }) {
  const isAssistant = message.role === "assistant";
  const hasWarning = /⚠|WARNING|CONFLICT/i.test(message.content);
  const hasUncertainty = /uncertain|not sure|human review/i.test(message.content);

  return (
    <article
      className={[
        "relative rounded-3xl border bg-white/95 p-6 shadow-glow backdrop-blur",
        isAssistant ? "border-slate-200" : "border-blue-100",
        hasWarning ? "border-amber-300 bg-amber-50" : "",
        hasUncertainty ? "ring-1 ring-blue-100" : "",
      ].join(" ")}
    >
      <div className="flex gap-5">
        <div
          className={[
            "flex h-12 w-12 shrink-0 items-center justify-center rounded-full text-sm font-semibold",
            isAssistant ? "bg-blue-50 text-blue-600" : "bg-blue-100 text-blue-700",
          ].join(" ")}
        >
          {isAssistant ? <span aria-hidden="true">✦</span> : "You"}
        </div>
        <div className="min-w-0 flex-1">
          <div className="mb-3 flex items-center justify-between gap-3">
            <span className="text-sm font-semibold text-ink">
              {isAssistant ? "ParcelPilot Support" : "You"}
            </span>
            <time className="text-xs text-ink">
              {new Date(message.timestamp).toLocaleTimeString([], {
                hour: "2-digit",
                minute: "2-digit",
              })}
            </time>
          </div>

          <div
            className={[
              "space-y-3 text-sm leading-7 text-ink",
              hasWarning ? "text-amber-900" : "",
              hasUncertainty ? "text-slate-800" : "",
            ].join(" ")}
          >
            {renderContent(message.content)}
          </div>

          {message.toolCalls?.length ? (
            <details className="mt-5 rounded-2xl border border-slate-200 bg-white p-4">
              <summary className="cursor-pointer list-none text-sm font-medium text-ink focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2">
                Tool calls
              </summary>
              <div className="mt-3 space-y-3">
                {message.toolCalls.map((toolCall, index) => (
                  <ToolCallBadge key={`${toolCall.tool}-${index}`} toolCall={toolCall} />
                ))}
              </div>
            </details>
          ) : null}
        </div>
      </div>
    </article>
  );
}
