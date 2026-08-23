from __future__ import annotations

from typing import Any, Dict, Optional


MOCK_USERS = {
    "staff_alice": {
        "user_id": "staff_alice",
        "name": "Alice (Support Agent)",
        "role": "support_agent",
        "account_access": "all"
    },
    "staff_bob": {
        "user_id": "staff_bob",
        "name": "Bob (Operations Lead)",
        "role": "ops_lead",
        "account_access": "all"
    },
    "staff_charlie": {
        "user_id": "staff_charlie",
        "name": "Charlie (Viewer)",
        "role": "viewer",
        "account_access": "all",
        "can_escalate": False
    }
}


def get_user(user_id: str) -> Optional[Dict[str, Any]]:
    return MOCK_USERS.get(user_id)


def can_take_action(user: Dict[str, Any] | None) -> bool:
    return bool(user) and user.get("can_escalate", True) and user.get("role") != "viewer"


def can_access_account(user: Dict[str, Any] | None, account_id: str) -> bool:
    if not user:
        return False
    access = user.get("account_access", "none")
    if access == "all":
        return True
    if isinstance(access, list):
        return account_id in access
    return False


def get_all_users() -> Dict[str, Dict[str, Any]]:
    return MOCK_USERS
