import { useEffect, useState } from "react";
import type { InsightItem, Message, PendingAction, ToolCall, UserInfo } from "../types";

const API_BASE =
  import.meta.env.VITE_API_BASE_URL ?? `${window.location.protocol}//${window.location.hostname}:8000`;

function nowIso(): string {
  return new Date().toISOString();
}

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

export function useChat(selectedUser: UserInfo | null) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [sessionId, setSessionId] = useState<string>(() => crypto.randomUUID());
  const [pendingAction, setPendingAction] = useState<PendingAction | null>(null);
  const [insights, setInsights] = useState<InsightItem[]>([]);
  const [isSending, setIsSending] = useState(false);
  const [isConfirmingAction, setIsConfirmingAction] = useState(false);
  const [isLoadingInsights, setIsLoadingInsights] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!selectedUser) {
      setMessages([]);
      setPendingAction(null);
      setSessionId(crypto.randomUUID());
    }
  }, [selectedUser]);

  const fetchInsights = async () => {
    setIsLoadingInsights(true);
    try {
      const response = await fetch(`${API_BASE}/insights`);
      if (!response.ok) {
        throw new Error(await getErrorMessage(response, "Could not load insights."));
      }
      const payload = (await response.json()) as { insights: InsightItem[] };
      setInsights(payload.insights);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown insights error.");
    } finally {
      setIsLoadingInsights(false);
    }
  };

  useEffect(() => {
    void fetchInsights();
  }, []);

  const sendMessage = async (content: string) => {
    if (!selectedUser || !content.trim()) {
      return;
    }

    const userMessage: Message = {
      id: crypto.randomUUID(),
      role: "user",
      content,
      timestamp: nowIso(),
    };

    setMessages((current) => [...current, userMessage]);
    setIsSending(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: content,
          user_id: selectedUser.user_id,
          session_id: sessionId,
        }),
      });

      if (!response.ok) {
        throw new Error(await getErrorMessage(response, "Chat request failed."));
      }

      const payload = (await response.json()) as {
        response: string;
        tool_calls: ToolCall[];
        pending_action: PendingAction | null;
        session_id: string;
      };

      const assistantMessage: Message = {
        id: crypto.randomUUID(),
        role: "assistant",
        content: payload.response,
        toolCalls: payload.tool_calls,
        pendingAction: payload.pending_action,
        timestamp: nowIso(),
      };

      setMessages((current) => [...current, assistantMessage]);
      setSessionId(payload.session_id);
      setPendingAction(payload.pending_action);
      void fetchInsights();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown chat error.");
    } finally {
      setIsSending(false);
    }
  };

  const confirmAction = async (confirmed: boolean) => {
    if (!selectedUser || !pendingAction) {
      return;
    }

    setIsConfirmingAction(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE}/confirm_action`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          action_id: pendingAction.action_id,
          confirmed,
          user_id: selectedUser.user_id,
        }),
      });

      if (!response.ok) {
        throw new Error(await getErrorMessage(response, "Could not confirm action."));
      }

      const payload = (await response.json()) as { success: boolean; message: string };
      setMessages((current) => [
        ...current,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          content: payload.message,
          timestamp: nowIso(),
        },
      ]);
      setPendingAction(null);
      void fetchInsights();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown confirmation error.");
    } finally {
      setIsConfirmingAction(false);
    }
  };

  const resetSession = () => {
    setMessages([]);
    setPendingAction(null);
    setSessionId(crypto.randomUUID());
    setError(null);
  };

  return {
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
    refreshInsights: fetchInsights,
  };
}
