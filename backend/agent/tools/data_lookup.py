from __future__ import annotations

import ast
import json
import re
from typing import Any

from langchain_core.tools import Tool

from backend.auth.mock_auth import can_access_account, get_user
from backend.data.structured import StructuredData


ACTION_ALIASES = {
    "get_order_details": "get_order",
    "get_order_detail": "get_order",
    "get_account_details": "get_account",
    "get_ticket_details": "get_ticket",
    "check_cancellation_eligibility": "get_order_cancellation_eligibility",
    "get_cancellation_eligibility": "get_order_cancellation_eligibility",
    "assess_cancellation": "get_order_cancellation_eligibility",
    "check_failed_pickup_credit": "get_failed_pickup_credit_assessment",
}


def _infer_query_from_text(text: str) -> dict[str, Any] | None:
    order_match = re.search(r"\bORD-\d+\b", text, flags=re.IGNORECASE)
    ticket_match = re.search(r"\bTKT-\d+\b", text, flags=re.IGNORECASE)
    account_match = re.search(r"\bACCT-\d+\b", text, flags=re.IGNORECASE)
    lowered = text.lower()

    if order_match:
        order_id = order_match.group(0).upper()
        if "cancel" in lowered or "fee" in lowered or "eligib" in lowered:
            return {"action": "get_order_cancellation_eligibility", "params": {"order_id": order_id}}
        return {"action": "get_order", "params": {"order_id": order_id}}

    if ticket_match:
        return {"action": "get_ticket", "params": {"ticket_id": ticket_match.group(0).upper()}}

    if account_match:
        account_id = account_match.group(0).upper()
        if "credit" in lowered or "pickup" in lowered:
            return {"action": "get_failed_pickup_credit_assessment", "params": {"account_id": account_id}}
        return {"action": "get_account", "params": {"account_id": account_id}}

    if "open ticket" in lowered:
        return {"action": "get_open_tickets", "params": {}}

    return None


def _parse_query(query_input: Any) -> dict[str, Any] | None:
    if isinstance(query_input, dict):
        query = query_input
    else:
        text = str(query_input).strip()
        try:
            query = json.loads(text)
        except json.JSONDecodeError:
            try:
                parsed = ast.literal_eval(text)
                query = parsed if isinstance(parsed, dict) else {}
            except (SyntaxError, ValueError):
                inferred = _infer_query_from_text(text)
                return inferred

    action = ACTION_ALIASES.get(str(query.get("action", "")), query.get("action"))
    params = query.get("params") if isinstance(query.get("params"), dict) else {}
    for key in ("order_id", "ticket_id", "account_id", "sla_breached"):
        if key in query and key not in params:
            params[key] = query[key]
    return {"action": action, "params": params}


def build_lookup_data_tool(structured_data: StructuredData, user_id: str) -> Tool:
    def lookup_data_func(query_input: Any) -> str:
        query = _parse_query(query_input)
        if not query:
            return (
                "ERROR: Could not understand lookup request. Use JSON like "
                "{\"action\":\"get_order\",\"params\":{\"order_id\":\"ORD-1001\"}}."
            )

        action = query.get("action")
        params = query.get("params", {})
        user = get_user(user_id)
        if not user:
            return "ERROR: User not found"

        def deny_if_needed(account_id: str) -> str | None:
            if not can_access_account(user, account_id):
                return "ACCESS DENIED: You do not have permission to view this account."
            return None

        def dump(payload: Any) -> str:
            return json.dumps(payload, indent=2, default=str)

        if action == "get_order":
            order = structured_data.get_order(str(params.get("order_id", "")))
            if not order:
                return "Order not found."
            denied = deny_if_needed(str(order["account_id"]))
            return denied or dump(order)

        if action == "get_orders_by_account":
            account_id = str(params.get("account_id", ""))
            denied = deny_if_needed(account_id)
            return denied or dump(structured_data.get_orders_by_account(account_id))

        if action == "get_account":
            account_id = str(params.get("account_id", ""))
            denied = deny_if_needed(account_id)
            if denied:
                return denied
            return dump(structured_data.get_account(account_id))

        if action == "get_all_accounts":
            return dump(structured_data.get_all_accounts())

        if action == "get_ticket":
            ticket = structured_data.get_ticket(str(params.get("ticket_id", "")))
            if not ticket:
                return "Ticket not found."
            denied = deny_if_needed(str(ticket["account_id"]))
            return denied or dump(ticket)

        if action == "get_tickets_by_account":
            account_id = str(params.get("account_id", ""))
            denied = deny_if_needed(account_id)
            return denied or dump(structured_data.get_tickets_by_account(account_id))

        if action == "get_open_tickets":
            tickets = structured_data.get_open_tickets(params.get("sla_breached"))
            visible = [ticket for ticket in tickets if can_access_account(user, str(ticket["account_id"]))]
            return dump(visible)

        if action == "get_order_cancellation_eligibility":
            order = structured_data.get_order(str(params.get("order_id", "")))
            if not order:
                return "Order not found."
            denied = deny_if_needed(str(order["account_id"]))
            return denied or dump(structured_data.get_order_cancellation_eligibility(str(order["order_id"])))

        if action == "get_failed_pickup_credit_assessment":
            account_id = str(params.get("account_id", ""))
            denied = deny_if_needed(account_id)
            return denied or dump(structured_data.get_failed_pickup_credit_assessment(account_id))

        if action == "get_dataset_snapshot_time":
            return dump({"snapshot_time": structured_data.get_dataset_snapshot_time()})

        return (
            "ERROR: Unknown action. Supported actions are get_order, get_orders_by_account, "
            "get_account, get_all_accounts, get_ticket, get_tickets_by_account, get_open_tickets, "
            "get_order_cancellation_eligibility, get_failed_pickup_credit_assessment, and get_dataset_snapshot_time."
        )

    return Tool(
        name="lookup_data",
        description=(
            "Look up ParcelPilot accounts, orders, tickets, SLA state, cancellation eligibility, "
            "and failed-pickup credits. Prefer JSON input. Examples: "
            "{\"action\":\"get_order\",\"params\":{\"order_id\":\"ORD-1001\"}}, "
            "{\"action\":\"get_order_cancellation_eligibility\",\"params\":{\"order_id\":\"ORD-1001\"}}, "
            "{\"action\":\"get_ticket\",\"params\":{\"ticket_id\":\"TKT-504\"}}."
        ),
        func=lookup_data_func,
    )
