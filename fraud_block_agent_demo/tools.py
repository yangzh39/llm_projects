"""Deterministic mock banking tools backed by separate local tables."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class MockBankTools:
    def __init__(self, data_dir: Path, trace: list[dict[str, Any]]) -> None:
        self.customers = self._load(data_dir / "customers.json")
        self.cards = self._load(data_dir / "cards.json")
        self.cases = self._load(data_dir / "fraud_cases.json")
        self.transactions = self._load(data_dir / "transactions.json")
        self.trace = trace
        self.authenticated_customer_id: str | None = None
        self.authenticated_card_id: str | None = None
        self.approvals: dict[str, str] = {}

    @staticmethod
    def _load(path: Path) -> list[dict[str, Any]]:
        return json.loads(path.read_text(encoding="utf-8"))

    def _record(self, tool: str, inputs: dict[str, Any], output: Any) -> Any:
        self.trace.append({"type": "tool_call", "tool": tool, "input": inputs, "output": output})
        return output

    def authenticate_customer(self, card_number: str, date_of_birth: str) -> dict[str, Any]:
        card = next((item for item in self.cards if item["card_number"] == card_number), None)
        customer = next(
            (
                item
                for item in self.customers
                if card and item["customer_id"] == card["customer_id"] and item["date_of_birth"] == date_of_birth
            ),
            None,
        )
        if card and customer:
            self.authenticated_customer_id = customer["customer_id"]
            self.authenticated_card_id = card["card_id"]
        return self._record(
            "authenticate_customer",
            {"card_number": f"**** {card_number[-4:]}" if len(card_number) >= 4 else "<invalid>", "date_of_birth": "<redacted>"},
            {"authenticated": bool(card and customer), "customer_id": customer["customer_id"] if customer else None, "card_id": card["card_id"] if customer else None},
        )

    def get_customer_cards(self, customer_id: str) -> dict[str, Any]:
        authorized = self.authenticated_customer_id == customer_id
        cards = []
        if authorized:
            cards = [
                {"card_id": card["card_id"], "customer_id": card["customer_id"], "display_number": f"**** {card['last_four']}", "status": card["status"], "fraud_case_id": card["fraud_case_id"]}
                for card in self.cards
                if card["customer_id"] == customer_id
            ]
        return self._record("get_customer_cards", {"customer_id": customer_id}, {"authorized": authorized, "cards": cards})

    def get_blocked_card(self, customer_id: str, card_id: str) -> dict[str, Any]:
        card = next((item for item in self.cards if item["card_id"] == card_id), None)
        authorized = bool(
            card
            and self.authenticated_customer_id == customer_id
            and self.authenticated_card_id == card_id
            and card["customer_id"] == customer_id
        )
        safe_card = None
        if authorized and card["status"] == "fraud_blocked":
            safe_card = {"card_id": card_id, "customer_id": customer_id, "display_number": f"**** {card['last_four']}", "status": card["status"], "fraud_case_id": card["fraud_case_id"]}
        return self._record("get_blocked_card", {"customer_id": customer_id, "card_id": card_id}, {"authorized": authorized, "card": safe_card})

    def get_flagged_transactions(self, customer_id: str, card_id: str, case_id: str) -> dict[str, Any]:
        card = next((item for item in self.cards if item["card_id"] == card_id), None)
        authorized = bool(
            card
            and self.authenticated_customer_id == customer_id
            and self.authenticated_card_id == card_id
            and card["customer_id"] == customer_id
            and card["fraud_case_id"] == case_id
        )
        rows = [item.copy() for item in self.transactions if authorized and item["case_id"] == case_id]
        rows.sort(key=lambda item: item["date"], reverse=True)
        return self._record("get_flagged_transactions", {"customer_id": customer_id, "card_id": card_id, "case_id": case_id}, {"authorized": authorized, "transactions": rows})

    def check_removal_eligibility(
        self,
        customer_id: str,
        card_id: str,
        case_id: str,
        verified_transaction_ids: list[str],
        recognized_transaction_ids: list[str],
    ) -> dict[str, Any]:
        card = next((item for item in self.cards if item["card_id"] == card_id), None)
        case = next((item for item in self.cases if item["case_id"] == case_id), None)
        case_transactions = [item for item in self.transactions if item["case_id"] == case_id]
        latest = max(case_transactions, key=lambda item: item["date"], default=None)
        expected = {latest["transaction_id"]} if latest else set()
        checks = {
            "authenticated": self.authenticated_customer_id == customer_id,
            "card_owned_by_customer": bool(card and card["customer_id"] == customer_id and self.authenticated_card_id == card_id),
            "case_matches_card": bool(card and case and card["fraud_case_id"] == case_id and case["card_id"] == card_id),
            "most_recent_transaction_verified": set(verified_transaction_ids) == expected,
            "most_recent_transaction_recognized": set(recognized_transaction_ids) == expected,
            "case_eligible": bool(case and case["eligible"]),
        }
        eligible = all(checks.values())
        token = f"APPROVED-{case_id}-{card_id}" if eligible else None
        if token:
            self.approvals[card_id] = token
        return self._record(
            "check_removal_eligibility",
            {"customer_id": customer_id, "card_id": card_id, "case_id": case_id, "verified_transaction_ids": verified_transaction_ids, "recognized_transaction_ids": recognized_transaction_ids},
            {"eligible": eligible, "checks": checks, "reason": case["reason"] if case else "Case not found", "authorization_token": token},
        )

    def remove_fraud_block(self, customer_id: str, card_id: str, token: str | None) -> dict[str, Any]:
        card = next((item for item in self.cards if item["card_id"] == card_id), None)
        permitted = bool(
            card
            and self.authenticated_customer_id == customer_id
            and self.authenticated_card_id == card_id
            and card["customer_id"] == customer_id
            and token
            and self.approvals.get(card_id) == token
        )
        if permitted:
            card["status"] = "active"
        return self._record("remove_fraud_block", {"customer_id": customer_id, "card_id": card_id, "authorization_token_present": bool(token)}, {"removed": permitted, "new_status": card["status"] if card else "not_found"})

    def verify_card_status(self, customer_id: str, card_id: str) -> dict[str, Any]:
        card = next((item for item in self.cards if item["card_id"] == card_id), None)
        authorized = bool(card and self.authenticated_customer_id == customer_id and card["customer_id"] == customer_id)
        return self._record("verify_card_status", {"customer_id": customer_id, "card_id": card_id}, {"authorized": authorized, "card_id": card_id, "status": card["status"] if authorized else None})

    def escalate_to_human(self, reason: str) -> dict[str, Any]:
        return self._record("escalate_to_human", {"reason": reason}, {"escalated": True, "queue": "mock_fraud_specialist"})

    def transfer_to_department(self, department: str) -> dict[str, Any]:
        return self._record(
            "transfer_to_department",
            {"department": department},
            {"transferred": True, "department": department},
        )
