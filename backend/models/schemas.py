from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str
    user_id: str
    session_id: Optional[str] = None


class ToolCall(BaseModel):
    tool: str
    input: str
    output: str


class PendingAction(BaseModel):
    action_type: str
    payload: Dict[str, Any]
    confirmation_message: str
    action_id: str = Field(default_factory=lambda: str(uuid.uuid4()))


class ChatResponse(BaseModel):
    response: str
    tool_calls: List[ToolCall]
    pending_action: Optional[PendingAction] = None
    session_id: str


class ConfirmActionRequest(BaseModel):
    action_id: str
    confirmed: bool
    user_id: str


class ConfirmActionResponse(BaseModel):
    success: bool
    message: str


class UserInfo(BaseModel):
    user_id: str
    name: str
    role: str
    account_access: str
    can_escalate: bool = True


class UsersResponse(BaseModel):
    users: List[UserInfo]


class IngestResponse(BaseModel):
    chunks_ingested: int
    message: str


class InsightItem(BaseModel):
    type: str
    severity: str
    message: str
    ticket_id: Optional[str] = None
    account: Optional[str] = None


class InsightsResponse(BaseModel):
    insights: List[InsightItem]
