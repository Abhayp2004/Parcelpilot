import type { FormEvent, KeyboardEvent } from "react";
import { useState } from "react";
import type { Message } from "../types";
import { MessageBubble } from "./MessageBubble";

export function ChatWindow({
  messages,
  isSending,
  onSend,
  disabled,
}: {
  messages: Message[];
  isSending: boolean;
  onSend: (message: string) => Promise<void>;
  disabled: boolean;
}) {
  const [draft, setDraft] = useState("");

  const submitDraft = async () => {
    const trimmed = draft.trim();
    if (!trimmed || disabled || isSending) {
      return;
    }
    setDraft("");
    await onSend(trimmed);
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    await submitDraft();
  };

  const handleKeyDown = async (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      await submitDraft();
    }
  };

  return (
    <section className="flex min-h-screen flex-col">
      <header className="flex flex-col gap-4 border-b border-slate-200 bg-white/80 px-6 py-7 backdrop-blur lg:flex-row lg:items-center lg:justify-between lg:px-12">
        <div>
          <p className="font-mono text-xs font-medium uppercase tracking-[0.24em] text-blue-600">
            Internal Support Agent
          </p>
          <h2 className="mt-2 text-2xl font-semibold tracking-[-0.03em] text-ink">
            Investigate and act with traceability
          </h2>
        </div>
        <div className="inline-flex min-h-11 w-fit items-center gap-3 rounded-full border border-slate-200 bg-white px-5 text-sm font-medium text-ink shadow-sm">
          <span className="h-2.5 w-2.5 rounded-full bg-emerald-400" aria-hidden="true" />
          Sources & tool calls stay attached
        </div>
      </header>

      <div className="scenic-hero relative h-52 shrink-0 overflow-hidden border-b border-slate-200" aria-hidden="true" />

      <div className="-mt-20 flex-1 space-y-5 px-6 pb-6 lg:px-12">
        {messages.length === 0 ? (
          <div className="relative rounded-3xl border border-dashed border-slate-200 bg-white/90 p-8 text-sm leading-7 text-ink shadow-glow backdrop-blur">
            <p className="text-base font-semibold text-ink">Start with a policy or operations question.</p>
            <p className="mt-2 max-w-2xl">
              Try cancellation eligibility, SLA risk, service credits, or an action that requires confirmation.
            </p>
            <div className="mt-5 grid gap-3 md:grid-cols-2">
              {[
                "Can Northstar cancel ORD-1001 without a fee?",
                "Create an escalation for TKT-504 because it is close to SLA breach.",
              ].map((example) => (
                <button
                  key={example}
                  type="button"
                  onClick={() => setDraft(example)}
                  className="min-h-12 rounded-2xl border border-slate-200 bg-white px-4 py-3 text-left text-sm font-medium text-ink transition hover:border-blue-200 hover:bg-blue-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2"
                >
                  {example}
                </button>
              ))}
            </div>
          </div>
        ) : (
          messages.map((message) => <MessageBubble key={message.id} message={message} />)
        )}

        {isSending ? (
          <div className="rounded-3xl border border-blue-100 bg-white/90 p-5 shadow-sm" aria-busy="true">
            <div className="flex items-center gap-4">
              <div className="flex h-11 w-11 items-center justify-center rounded-full bg-blue-50 text-blue-600 ambient-shift">
                <span aria-hidden="true">✦</span>
              </div>
              <div className="flex-1 space-y-2">
                <div className="h-3 w-48 animate-pulse rounded-full bg-slate-200" />
                <div className="h-3 w-72 max-w-full animate-pulse rounded-full bg-slate-100" />
              </div>
            </div>
          </div>
        ) : null}
      </div>

      <form className="sticky bottom-0 mx-6 mb-6 rounded-3xl border border-slate-200 bg-white/95 p-4 shadow-glow backdrop-blur lg:mx-12" onSubmit={handleSubmit}>
        <label className="sr-only" htmlFor="chat-input">
          Ask ParcelPilot Support
        </label>
        <textarea
          id="chat-input"
          value={draft}
          onChange={(event) => setDraft(event.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={disabled ? "Choose a staff user to start..." : "Ask a support question or request an escalation..."}
          disabled={disabled || isSending}
          rows={3}
          className="min-h-24 w-full resize-none border-0 bg-transparent px-2 py-2 text-sm leading-7 text-ink placeholder:text-ink focus-visible:outline-none disabled:cursor-not-allowed disabled:opacity-75"
        />
        <div className="mt-2 flex items-center justify-between gap-3">
          <span className="text-xs text-ink">Shift + Enter for newline</span>
          <button
            type="submit"
            disabled={disabled || isSending || !draft.trim()}
            aria-label="Send message"
            className="flex min-h-14 min-w-14 items-center justify-center rounded-full bg-blue-600 px-5 text-sm font-semibold text-white shadow-sm transition hover:bg-blue-500 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:bg-slate-300"
          >
            <span className="-rotate-45 text-xl" aria-hidden="true">➤</span>
          </button>
        </div>
      </form>
    </section>
  );
}
