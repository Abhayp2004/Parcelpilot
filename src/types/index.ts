export interface ToolCall {
  tool: "search_documents" | "lookup_data" | "prepare_action" | string;
  input: string;
  output: string;
}

export interface PendingAction {
  action_type: string;
  payload: Record<string, unknown>;
  confirmation_message: string;
  action_id: string;
}

export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  toolCalls?: ToolCall[];
  pendingAction?: PendingAction | null;
  timestamp: string;
}

export interface UserInfo {
  user_id: string;
  name: string;
  role: string;
  account_access: string;
  can_escalate?: boolean;
}

export interface InsightItem {
  type: string;
  severity: "high" | "medium" | "info" | string;
  message: string;
  ticket_id?: string | null;
  account?: string | null;
}
