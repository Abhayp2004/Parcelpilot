import { useEffect, useState } from "react";
import { ChatWindow } from "./components/ChatWindow";
import { ConfirmationModal } from "./components/ConfirmationModal";
import { LoginScreen } from "./components/LoginScreen";
import { useChat } from "./hooks/useChat";
import type { InsightItem, UserInfo } from "./types";

const API_BASE =
  import.meta.env.VITE_API_BASE_URL ?? `${window.location.protocol}//${window.location.hostname}:8000`;

async function getErrorMessage(response: Response, fallback: string): Promise<string> {
  try {
    const payload = (await response.json()) as { detail?: unknown; message?: unknown };
    if (typeof payload.detail === "string") {
      return payload.detail;
    }
    if (typeof payload.message === "string") {
      return payload.message;
    }
  } catch {
    return fallback;
  }

  return fallback;
}

function severityTone(severity: InsightItem["severity"]) {
  if (severity === "high") {
    return "border-rose-200 bg-rose-50 text-rose-800";
  }
  if (severity === "medium") {
    return "border-amber-200 bg-amber-50 text-amber-800";
  }
  return "border-blue-200 bg-blue-50 text-blue-800";
}

export default function App() {
  const [users, setUsers] = useState<UserInfo[]>([]);
  const [selectedUserId, setSelectedUserId] = useState("");
  const [isLoadingUsers, setIsLoadingUsers] = useState(true);
  const [userLoadError, setUserLoadError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<"chat" | "insights">("chat");

  const selectedUser = users.find((user) => user.user_id === selectedUserId) ?? null;
  const {
    messages,
    sessionId,
    pendingAction,
    insights,
    isSending,
    isConfirmingAction,
    isLoadingInsights,
    error,
    sendMessage,
    confirmAction,
    resetSession,
    refreshInsights,
  } = useChat(selectedUser);

  const fetchUsers = async () => {
    setIsLoadingUsers(true);
    setUserLoadError(null);
    try {
      const response = await fetch(`${API_BASE}/users`);
      if (!response.ok) {
        throw new Error(await getErrorMessage(response, "Could not load mock users."));
      }
      const payload = (await response.json()) as { users: UserInfo[] };
      setUsers(payload.users);
    } catch (err) {
      setUserLoadError(err instanceof Error ? err.message : "Unknown user loading error.");
    } finally {
      setIsLoadingUsers(false);
    }
  };

  useEffect(() => {
    void fetchUsers();
  }, []);

  return (
    <div className="min-h-screen bg-slate-50 text-ink">
      <div className="mx-auto grid min-h-screen max-w-[1600px] lg:grid-cols-[356px_minmax(0,1fr)]">
        <aside className="border-b border-slate-200 bg-white/90 backdrop-blur lg:min-h-screen lg:border-b-0 lg:border-r">
          <div className="sticky top-0 flex min-h-screen flex-col gap-7 px-7 py-8">
            <header className="space-y-10">
              <div className="flex items-center gap-4">
                <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-blue-600 text-white shadow-glow">
                  <span className="-rotate-45 text-2xl" aria-hidden="true">➤</span>
                </div>
                <div>
                  <p className="text-lg font-bold leading-tight text-ink">ParcelPilot</p>
                  <p className="text-sm text-ink">Support</p>
                </div>
              </div>

              <div>
                <h1 className="max-w-[15rem] text-2xl font-bold leading-tight tracking-[-0.03em] text-ink">
                  Policy-aware AI support operations
                </h1>
                <p className="mt-4 max-w-[18rem] text-sm leading-7 text-ink">
                  Internal-only assistant for policy lookups, operational data, and controlled ticket actions.
                </p>
              </div>
            </header>

            <LoginScreen
              users={users}
              selectedUserId={selectedUserId}
              onSelect={setSelectedUserId}
              isLoading={isLoadingUsers}
              error={userLoadError}
              onRetry={() => void fetchUsers()}
            />

            <section className="border-t border-slate-200 pt-7">
              <div className="mb-4 flex items-start justify-between gap-4">
                <div>
                  <p className="font-mono text-xs font-medium uppercase tracking-[0.22em] text-blue-600">
                    Session
                  </p>
                  <p className="mt-3 max-w-[13rem] break-all text-xs leading-5 text-ink">{sessionId}</p>
                  <p className="mt-1 text-xs text-ink">Started just now</p>
                </div>
                <button
                  type="button"
                  onClick={resetSession}
                  className="min-h-11 rounded-2xl border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-ink shadow-sm transition hover:border-blue-200 hover:bg-blue-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2"
                >
                  New session
                </button>
              </div>

              <nav className="mt-7 space-y-2" aria-label="Primary navigation">
                {(["chat", "insights"] as const).map((tab) => (
                  <button
                    key={tab}
                    type="button"
                    onClick={() => setActiveTab(tab)}
                    className={[
                      "flex min-h-12 w-full items-center gap-3 rounded-xl px-4 text-left text-sm font-medium transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2",
                      activeTab === tab
                        ? "border-l-2 border-blue-600 bg-blue-50 text-blue-700"
                        : "text-ink hover:bg-slate-50 hover:text-ink",
                    ].join(" ")}
                  >
                    <span aria-hidden="true">{tab === "chat" ? "▢" : "▥"}</span>
                    {tab === "chat" ? "Chat" : "Insights"}
                  </button>
                ))}
              </nav>
            </section>

            {activeTab === "insights" ? (
              <section className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <p className="font-mono text-xs font-medium uppercase tracking-[0.2em] text-blue-600">
                      Insights
                    </p>
                    <h2 className="mt-1 text-base font-semibold text-ink">Issue detection</h2>
                  </div>
                  <button
                    type="button"
                    onClick={() => void refreshInsights()}
                    className="min-h-10 rounded-xl border border-slate-200 px-3 text-sm font-medium text-ink transition hover:bg-slate-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2"
                  >
                    Refresh
                  </button>
                </div>
                <div className="mt-4 space-y-3">
                  {isLoadingInsights ? (
                    <div className="space-y-3" aria-busy="true">
                      <div className="h-20 animate-pulse rounded-2xl bg-slate-100" />
                      <div className="h-20 animate-pulse rounded-2xl bg-slate-100" />
                    </div>
                  ) : insights.length === 0 ? (
                    <div className="rounded-2xl border border-dashed border-slate-200 bg-slate-50 p-4 text-sm leading-6 text-ink">
                      All caught up. No current risk flags from the snapshot.
                    </div>
                  ) : (
                    insights.map((insight, index) => (
                      <article
                        key={`${insight.type}-${index}`}
                        className={`rounded-2xl border p-4 ${severityTone(insight.severity)}`}
                      >
                        <p className="font-mono text-[11px] font-medium uppercase tracking-[0.18em]">
                          {insight.type.replace(/_/g, " ")}
                        </p>
                        <p className="mt-2 text-sm leading-6">{insight.message}</p>
                      </article>
                    ))
                  )}
                </div>
              </section>
            ) : (
              <section className="mt-auto rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
                <div className="mb-3 flex h-9 w-9 items-center justify-center rounded-full bg-blue-50 text-blue-600">
                  <span aria-hidden="true">♢</span>
                </div>
                <p className="text-sm font-semibold text-ink">Tip</p>
                <p className="mt-3 text-sm leading-7 text-ink">
                  Ask a question or request an escalation. Review tool calls before taking action.
                </p>
              </section>
            )}
          </div>
        </aside>

        <main className="min-w-0 bg-slate-50">
          {error ? (
            <div className="mx-6 mt-6 rounded-2xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-800 lg:mx-12">
              {error}
            </div>
          ) : null}
          <ChatWindow
            messages={messages}
            isSending={isSending}
            onSend={sendMessage}
            disabled={!selectedUser}
          />
        </main>
      </div>

      <ConfirmationModal
        pendingAction={pendingAction}
        isConfirming={isConfirmingAction}
        onCancel={() => void confirmAction(false)}
        onConfirm={() => void confirmAction(true)}
      />
    </div>
  );
}
