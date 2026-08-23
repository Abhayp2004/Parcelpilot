from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_EXCEL_PATH = PROJECT_ROOT / "data" / "ParcelPilot_Assessment_Data.xlsx"


@dataclass(frozen=True)
class SlaPolicy:
    p1_minutes: int
    p2_minutes: int
    p3_minutes: int


ACCOUNT_SLA_OVERRIDES: Dict[str, SlaPolicy] = {
    "ACCT-001": SlaPolicy(p1_minutes=15, p2_minutes=60, p3_minutes=8 * 60),
    "ACCT-002": SlaPolicy(p1_minutes=2 * 60, p2_minutes=4 * 60, p3_minutes=2 * 24 * 60),
}

PLAN_SLA_DEFAULTS: Dict[str, SlaPolicy] = {
    "enterprise": SlaPolicy(p1_minutes=30, p2_minutes=2 * 60, p3_minutes=24 * 60),
    "growth": SlaPolicy(p1_minutes=2 * 60, p2_minutes=4 * 60, p3_minutes=2 * 24 * 60),
    "standard": SlaPolicy(p1_minutes=4 * 60, p2_minutes=24 * 60, p3_minutes=2 * 24 * 60),
}


class StructuredData:
    def __init__(self, excel_path: str | Path = DEFAULT_EXCEL_PATH):
        self.excel_path = Path(excel_path)
        if not self.excel_path.is_absolute():
            self.excel_path = PROJECT_ROOT / self.excel_path
        self._data: Dict[str, pd.DataFrame] = {}
        self._snapshot_time = "2026-08-16 11:00 Asia/Kolkata"
        self._load_all()

    def _load_all(self) -> None:
        workbook = pd.ExcelFile(self.excel_path)
        for sheet_name in workbook.sheet_names:
            if sheet_name.lower() == "readme":
                readme_df = pd.read_excel(workbook, sheet_name=sheet_name, header=None)
                self._data["readme"] = readme_df
                self._snapshot_time = self._extract_snapshot_time(readme_df)
            else:
                df = pd.read_excel(workbook, sheet_name=sheet_name)
                df.columns = [str(column).strip().lower() for column in df.columns]
                self._data[sheet_name.lower()] = df.where(pd.notna(df), None)

    def _extract_snapshot_time(self, readme_df: pd.DataFrame) -> str:
        for _, row in readme_df.iterrows():
            label = str(row.iloc[0]).strip().lower()
            if label == "dataset snapshot":
                return str(row.iloc[1]).strip()
        return self._snapshot_time

    def get_dataset_snapshot_time(self) -> str:
        return self._snapshot_time

    def _snapshot_datetime(self) -> datetime:
        value = self._snapshot_time.replace(" Asia/Kolkata", "").strip()
        return datetime.strptime(value, "%Y-%m-%d %H:%M")

    def _normalize_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        normalized: Dict[str, Any] = {}
        for key, value in record.items():
            if hasattr(value, "isoformat"):
                normalized[key] = value.isoformat()
            elif hasattr(value, "item"):
                normalized[key] = value.item()
            else:
                normalized[key] = value
        return normalized

    def _records(self, sheet: str) -> List[Dict[str, Any]]:
        frame = self._data.get(sheet.lower())
        if frame is None:
            return []
        return [self._normalize_record(record) for record in frame.to_dict("records")]

    def get_order(self, order_id: str) -> Dict[str, Any] | None:
        for order in self._records("orders"):
            if order.get("order_id") == order_id:
                return self._enrich_order(order)
        return None

    def get_orders_by_account(self, account_id: str) -> List[Dict[str, Any]]:
        return [
            self._enrich_order(order)
            for order in self._records("orders")
            if order.get("account_id") == account_id
        ]

    def get_account(self, account_id: str) -> Dict[str, Any] | None:
        for account in self._records("accounts"):
            if account.get("account_id") == account_id:
                account["premium_support"] = bool(int(account.get("premium_support") or 0))
                account["has_customer_agreement"] = bool(account.get("contract_file"))
                return account
        return None

    def get_all_accounts(self) -> List[Dict[str, Any]]:
        return [account for account in (self.get_account(item["account_id"]) for item in self._records("accounts")) if account]

    def get_ticket(self, ticket_id: str) -> Dict[str, Any] | None:
        for ticket in self._records("tickets"):
            if ticket.get("ticket_id") == ticket_id:
                return self._enrich_ticket(ticket)
        return None

    def get_tickets_by_account(self, account_id: str) -> List[Dict[str, Any]]:
        return [
            self._enrich_ticket(ticket)
            for ticket in self._records("tickets")
            if ticket.get("account_id") == account_id
        ]

    def get_open_tickets(self, sla_breached: Optional[bool] = None) -> List[Dict[str, Any]]:
        tickets = [
            self._enrich_ticket(ticket)
            for ticket in self._records("tickets")
            if str(ticket.get("status", "")).lower() == "open"
        ]
        if sla_breached is None:
            return tickets
        return [ticket for ticket in tickets if ticket["sla"]["breached"] is sla_breached]

    def _parse_dt(self, value: Any) -> Optional[datetime]:
        if not value:
            return None
        if isinstance(value, datetime):
            return value
        text = str(value).strip()
        for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S"):
            try:
                return datetime.strptime(text, fmt)
            except ValueError:
                continue
        return None

    def _enrich_order(self, order: Dict[str, Any]) -> Dict[str, Any]:
        account = self.get_account(str(order.get("account_id")))
        enriched = dict(order)
        enriched["shipment_fee_inr"] = float(enriched.get("shipment_fee_inr") or 0)
        enriched["carrier_fault"] = bool(int(enriched.get("carrier_fault") or 0))
        enriched["customer_fault"] = bool(int(enriched.get("customer_fault") or 0))
        enriched["account"] = account
        if account:
            enriched["contract_file"] = account.get("contract_file")
        return enriched

    def _classify_ticket_severity(self, ticket: Dict[str, Any]) -> str:
        text = f"{ticket.get('subject', '')} {ticket.get('description', '')}".lower()
        if "http 500" in text or "all shipment creation is failing" in text or "api key" in text or "credential" in text:
            return "P1"
        if "failing" in text or "fails" in text or "booked after driver pickup" in text or "bulk upload" in text:
            return "P2"
        return "P3"

    def _resolve_sla_policy(self, account: Dict[str, Any] | None) -> SlaPolicy:
        if account and account.get("account_id") in ACCOUNT_SLA_OVERRIDES:
            return ACCOUNT_SLA_OVERRIDES[account["account_id"]]
        plan = str((account or {}).get("plan", "standard")).lower()
        return PLAN_SLA_DEFAULTS.get(plan, PLAN_SLA_DEFAULTS["standard"])

    def _enrich_ticket(self, ticket: Dict[str, Any]) -> Dict[str, Any]:
        account = self.get_account(str(ticket.get("account_id")))
        created_at = self._parse_dt(ticket.get("created_at"))
        snapshot = self._snapshot_datetime()
        severity = self._classify_ticket_severity(ticket)
        policy = self._resolve_sla_policy(account)
        target_minutes = {
            "P1": policy.p1_minutes,
            "P2": policy.p2_minutes,
            "P3": policy.p3_minutes,
        }[severity]
        deadline = created_at + timedelta(minutes=target_minutes) if created_at else snapshot
        remaining = deadline - snapshot

        enriched = dict(ticket)
        enriched["status"] = str(enriched.get("status", "")).lower()
        enriched["account"] = account
        enriched["severity"] = severity
        enriched["sla"] = {
            "policy_source": account.get("contract_file") if account and account.get("contract_file") else "01_Support_Policy_v3_CURRENT.pdf",
            "response_target_minutes": target_minutes,
            "deadline": deadline.strftime("%Y-%m-%d %H:%M"),
            "minutes_remaining": int(remaining.total_seconds() // 60),
            "breached": remaining.total_seconds() < 0,
            "at_risk": 0 <= remaining.total_seconds() < 2 * 60 * 60,
        }
        return enriched

    def get_order_cancellation_eligibility(self, order_id: str) -> Dict[str, Any]:
        order = self.get_order(order_id)
        if not order:
            return {"eligible": False, "reason": f"Order {order_id} not found"}

        account = order.get("account") or self.get_account(str(order.get("account_id")))
        status = str(order.get("status", "")).upper()
        booked_at = self._parse_dt(order.get("booked_at"))
        cancellation_requested_at = self._parse_dt(order.get("cancellation_requested_at")) or self._snapshot_datetime()
        pickup_actual_at = self._parse_dt(order.get("pickup_actual_at"))
        minutes_since_booking = int((cancellation_requested_at - booked_at).total_seconds() // 60) if booked_at else None

        result: Dict[str, Any] = {
            "order_id": order_id,
            "account_id": order.get("account_id"),
            "snapshot_time": self.get_dataset_snapshot_time(),
        }

        if status == "PICKED_UP" or pickup_actual_at:
            result.update(
                {
                    "eligible": False,
                    "cancellation_outcome": "not_allowed",
                    "fee_inr": None,
                    "reason": "Order has already been picked up. Use the return-to-origin workflow.",
                    "policy_source": account.get("contract_file") if account and account.get("account_id") == "ACCT-001" else "03_Cancellation_and_Service_Credit_SOP_v4.pdf",
                }
            )
            return result

        if status == "DELIVERED":
            result.update(
                {
                    "eligible": False,
                    "cancellation_outcome": "not_allowed",
                    "fee_inr": None,
                    "reason": "Delivered orders cannot be cancelled.",
                    "policy_source": "03_Cancellation_and_Service_Credit_SOP_v4.pdf",
                }
            )
            return result

        if account and account.get("account_id") == "ACCT-001":
            result.update(
                {
                    "eligible": True,
                    "cancellation_outcome": "fee_free",
                    "fee_inr": 0,
                    "reason": "Northstar may cancel any BOOKED shipment before pickup with no cancellation fee.",
                    "minutes_since_booking": minutes_since_booking,
                    "policy_source": "05_Northstar_Logistics_Enterprise_Agreement.pdf",
                }
            )
            return result

        if status in {"DRAFT", "BOOKED"}:
            fee = 0 if (minutes_since_booking is not None and minutes_since_booking <= 30) else 250
            result.update(
                {
                    "eligible": True,
                    "cancellation_outcome": "fee_free" if fee == 0 else "fee_applies",
                    "fee_inr": fee,
                    "minutes_since_booking": minutes_since_booking,
                    "reason": "Default cancellation SOP applies.",
                    "policy_source": account.get("contract_file") if account and account.get("contract_file") else "03_Cancellation_and_Service_Credit_SOP_v4.pdf",
                }
            )
            return result

        result.update(
            {
                "eligible": False,
                "cancellation_outcome": "not_allowed",
                "fee_inr": None,
                "reason": f"Orders in status {status} cannot be cancelled under the current SOP.",
                "policy_source": "03_Cancellation_and_Service_Credit_SOP_v4.pdf",
            }
        )
        return result

    def get_failed_pickup_credit_assessment(self, account_id: str) -> List[Dict[str, Any]]:
        assessments: List[Dict[str, Any]] = []
        for order in self.get_orders_by_account(account_id):
            if order["status"] != "BOOKED":
                continue
            window_end = self._parse_dt(order.get("pickup_window_end"))
            if not window_end:
                continue
            hours_late = (self._snapshot_datetime() - window_end).total_seconds() / 3600
            if account_id == "ACCT-002":
                eligible = hours_late > 4 and order["carrier_fault"] and not order["customer_fault"]
                credit = 300 if eligible else 0
                policy_source = "06_LumenWorks_Service_Agreement.pdf"
            else:
                eligible = hours_late > 2 and order["carrier_fault"] and not order["customer_fault"]
                credit = min(500, round(order["shipment_fee_inr"] * 0.1, 2)) if eligible else 0
                policy_source = "03_Cancellation_and_Service_Credit_SOP_v4.pdf"
            assessments.append(
                {
                    "order_id": order["order_id"],
                    "eligible": eligible,
                    "credit_inr": credit,
                    "hours_past_window_end": round(hours_late, 2),
                    "policy_source": policy_source,
                }
            )
        return assessments

    def get_sla_risk_insights(self) -> List[Dict[str, Any]]:
        insights: List[Dict[str, Any]] = []
        for ticket in self.get_open_tickets():
            account = ticket.get("account") or {}
            if ticket["sla"]["at_risk"]:
                insights.append(
                    {
                        "type": "sla_risk",
                        "severity": "high" if ticket["severity"] == "P1" else "medium",
                        "message": f"{ticket['ticket_id']} for {account.get('account_name', ticket['account_id'])} has {ticket['sla']['minutes_remaining']} minutes until SLA breach.",
                        "ticket_id": ticket["ticket_id"],
                        "account": account.get("account_name", ticket["account_id"]),
                    }
                )
        return insights

    def get_repeated_issue_insights(self) -> List[Dict[str, Any]]:
        insights: List[Dict[str, Any]] = []
        for account in self.get_all_accounts():
            open_tickets = [ticket for ticket in self.get_tickets_by_account(account["account_id"]) if ticket["status"] == "open"]
            if len(open_tickets) >= 3:
                insights.append(
                    {
                        "type": "repeated_issues",
                        "severity": "medium",
                        "message": f"{account['account_name']} has {len(open_tickets)} open tickets and may need proactive outreach.",
                        "ticket_id": None,
                        "account": account["account_name"],
                    }
                )
        return insights

    def get_recent_spike_insights(self) -> List[Dict[str, Any]]:
        snapshot = self._snapshot_datetime()
        cutoff = snapshot - timedelta(hours=24)
        recent_open = [
            ticket
            for ticket in self._records("tickets")
            if self._parse_dt(ticket.get("created_at")) and self._parse_dt(ticket.get("created_at")) >= cutoff
        ]
        if len(recent_open) <= 5:
            return []
        return [
            {
                "type": "recent_spike",
                "severity": "info",
                "message": f"{len(recent_open)} tickets were created in the last 24 hours relative to the dataset snapshot.",
                "ticket_id": None,
                "account": None,
            }
        ]
