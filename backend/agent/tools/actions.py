from __future__ import annotations

import json
import re
import uuid
from typing import Any, Dict

from langchain_core.tools import StructuredTool, Tool

from backend.auth.mock_auth import can_take_action, get_user

pending_actions: Dict[str, Dict[str, Any]] = {}


ACTION_TYPES = {
    "create_escalation": "Create a new escalation ticket",
    "update_ticket_status": "Update an existing ticket's status",
    "create_followup_task": "Create a follow-up task linked to a ticket"
}

ACTION_ALIASES = {
    "escalate": "create_escalation",
    "escalate_ticket": "create_escalation",
    "create_ticket_escalation": "create_escalation",
    "create_escalation_ticket": "create_escalation",
    "update_status": "update_ticket_status",
    "set_ticket_status": "update_ticket_status",
    "change_ticket_status": "update_ticket_status",
    "follow_up": "create_followup_task",
    "create_follow_up": "create_followup_task",
    "followup_task": "create_followup_task",
}

KNOWN_STATUSES = ("open", "pending", "escalated", "resolved", "closed")


def _normalize_action_type(action_type: Any) -> str | None:
    if not action_type:
        return None
    normalized = str(action_type).strip().lower().replace("-", "_").replace(" ", "_")
    return ACTION_ALIASES.get(normalized, normalized)


def _extract_ticket_id(text: str) -> str | None:
    match = re.search(r"\bTKT-\d+\b", text, flags=re.IGNORECASE)
    return match.group(0).upper() if match else None


def _extract_status(text: str) -> str | None:
    lowered = text.lower()
    for status in KNOWN_STATUSES:
        if re.search(rf"\b{status}\b", lowered):
            return status
    return None


def _parse_action_query(query_input: Any) -> Dict[str, Any]:
    if isinstance(query_input, dict):
        query = dict(query_input)
    else:
        raw = str(query_input or "").strip()
        try:
            query = json.loads(raw)
        except json.JSONDecodeError:
            query = {"raw_text": raw}

    action_type = _normalize_action_type(query.get("action_type") or query.get("action"))
    payload = query.get("payload") if isinstance(query.get("payload"), dict) else {}

    for key in ("ticket_id", "status", "priority"):
        if key in query and key not in payload:
            payload[key] = query[key]

    raw_text = str(query.get("raw_text") or query_input or "")
    if raw_text:
        if not action_type:
            lowered = raw_text.lower()
            if "escalat" in lowered:
                action_type = "create_escalation"
            elif "follow" in lowered:
                action_type = "create_followup_task"
            elif "status" in lowered:
                action_type = "update_ticket_status"

        payload.setdefault("ticket_id", _extract_ticket_id(raw_text))
        if action_type == "update_ticket_status":
            payload.setdefault("status", _extract_status(raw_text))
        if action_type == "create_escalation" and re.search(r"\b(sla|breach|high|urgent)\b", raw_text, re.IGNORECASE):
            payload.setdefault("priority", "high")

    query["action_type"] = action_type
    query["payload"] = {key: value for key, value in payload.items() if value is not None}
    return query


def build_prepare_action_tool(user_id: str) -> Tool:
    def prepare_action_func(
        query_input: Any = None,
        action_type: str | None = None,
        payload: Any = None,
        reason: str = "",
    ) -> str:
        user = get_user(user_id)
        if not user:
            return "ERROR: User not found."
        if not can_take_action(user):
            return "ERROR: You do not have permission to take actions (viewer role)."

        if action_type or payload:
            if isinstance(payload, str):
                try:
                    payload = json.loads(payload)
                except json.JSONDecodeError:
                    payload = {"raw_text": payload}
            query_input = {
                "action_type": action_type,
                "payload": payload or {},
                "reason": reason,
            }
        query = _parse_action_query(query_input)
        action_type = query.get("action_type")
        payload = query.get("payload", {})
        if action_type not in ACTION_TYPES:
            return f"ERROR: Unknown action type '{action_type}'."

        action_id = str(uuid.uuid4())
        ticket_id = payload.get("ticket_id", "unknown")
        confirmation_message = {
            "create_escalation": f"This will create an escalation for {ticket_id}. Are you sure?",
            "update_ticket_status": f"This will update {ticket_id} to status {payload.get('status', 'unknown')}. Are you sure?",
            "create_followup_task": f"This will create a follow-up task linked to {ticket_id}. Are you sure?",
        }[action_type]

        pending_actions[action_id] = {
            "status": "pending_confirmation",
            "action_type": action_type,
            "payload": payload,
            "reason": query.get("reason", ""),
            "confirmation_message": confirmation_message,
            "user_id": user_id,
        }

        return json.dumps(
            {
                "status": "pending_confirmation",
                "action_type": action_type,
                "payload": payload,
                "confirmation_message": confirmation_message,
                "action_id": action_id,
            },
            indent=2,
        )

    return StructuredTool.from_function(
        func=prepare_action_func,
        name="prepare_action",
        description="Prepare a support action such as creating an escalation ticket, updating ticket status, or creating a follow-up task. This tool ONLY prepares the action — it does NOT execute it. The action will be shown to the user for confirmation before anything happens.",
    )


def execute_action(action_id: str, user_id: str) -> Dict[str, Any]:
    """Execute a confirmed action."""
    if action_id not in pending_actions:
        return {"success": False, "message": "Action not found or expired."}

    action = pending_actions[action_id]
    if action["user_id"] != user_id:
        return {"success": False, "message": "Not authorized to confirm this action."}

    user = get_user(user_id)
    if not user or not can_take_action(user):
        return {"success": False, "message": "Permission denied."}

    action_type = action["action_type"]
    payload = action["payload"]
    del pending_actions[action_id]

    if action_type == "create_escalation":
        return {"success": True, "message": f"Escalation created for {payload.get('ticket_id', 'unknown')}."}
    if action_type == "update_ticket_status":
        return {"success": True, "message": f"Ticket {payload.get('ticket_id', 'unknown')} status updated to {payload.get('status', 'unknown')}."}
    if action_type == "create_followup_task":
        return {"success": True, "message": f"Follow-up task created for {payload.get('ticket_id', 'unknown')}."}

    return {"success": False, "message": "Unknown action type."}
