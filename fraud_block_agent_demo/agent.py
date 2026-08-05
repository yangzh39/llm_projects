"""One orchestrating agent; language handles intent, tools enforce decisions."""

from __future__ import annotations

import json
from pathlib import Path
import re
from typing import Any, Callable

from tools import MockBankTools


AnswerProvider = Callable[[str, dict[str, Any]], str]
IntentClassifier = Callable[[str], dict[str, Any]]
ResponseInterpreter = Callable[[str, dict[str, Any]], dict[str, Any]]
OutputPresenter = Callable[[str, dict[str, Any]], None]


class FraudBlockAgent:
    def __init__(self, data_dir: Path) -> None:
        self.trace: list[dict[str, Any]] = []
        self.tools = MockBankTools(data_dir, self.trace)

    def _step(self, step: str, **details: Any) -> None:
        self.trace.append({"type": "workflow_step", "step": step, **details})

    def _finish(self, message: str, disposition: str) -> dict[str, Any]:
        self.trace.append({"type": "final_response", "message": message, "disposition": disposition})
        return {"message": message, "disposition": disposition, "trace": self.trace}

    def _escalate(self, reason: str, message: str) -> dict[str, Any]:
        self.tools.escalate_to_human(reason)
        return self._finish(message, "escalated")

    def run(
        self,
        request: str,
        classify_intent: IntentClassifier,
        interpret_customer_response: ResponseInterpreter,
        answer: AnswerProvider,
        present_llm_output: OutputPresenter | None = None,
        *,
        flawed: bool = False,
    ) -> dict[str, Any]:
        present = present_llm_output or (lambda _human, _chatbot: None)

        def interpret_reply(
            raw_response: str,
            *,
            question_type: str,
            question: str,
            details: dict[str, Any] | None = None,
        ) -> tuple[str | None, str]:
            response = raw_response
            for response_attempt in range(1, 4):
                interpretation = interpret_customer_response(
                    response,
                    {"question_type": question_type, "question": question, "details": details or {}},
                )
                chatbot_message = interpretation.get("chatbot_message", {})
                meaning = chatbot_message.get("response_meaning", "UNCLEAR")
                self.trace.append(
                    {
                        "type": "llm_call",
                        "purpose": "customer_response_interpretation",
                        "attempt": response_attempt,
                        "input": response,
                        "context": {"question_type": question_type},
                        "output": interpretation,
                    }
                )
                self._step("customer_response_interpreted", question_type=question_type, meaning=meaning)
                if meaning in {"AFFIRMATIVE", "NEGATIVE", "FRAUD_REQUEST", "NEW_REQUEST"}:
                    return meaning, response
                present(str(interpretation.get("human_message", "")).strip(), chatbot_message)
                if response_attempt < 3:
                    response = answer("response_clarification", {"prompt": "Customer: ", "question_type": question_type})
            return None, response

        current_message = request
        conversation_history: list[dict[str, str]] = [{"role": "customer", "message": request}]
        classification: dict[str, Any] = {}
        goal = "UNCLEAR"
        attempt = 0
        while attempt < 3:
            attempt += 1
            classification = classify_intent(current_message)
            human_message = str(classification.get("human_message", "")).strip()
            chatbot_message = classification.get("chatbot_message", {})
            goal = chatbot_message.get("goal", "UNCLEAR")
            action = chatbot_message.get("next_action", "ASK_CLARIFICATION")
            service = chatbot_message.get("service", "Unclear")
            raw_department = str(chatbot_message.get("department", "General Customer Service"))
            department = re.sub(r"[^A-Za-z0-9 &-]", "", raw_department).strip()[:60] or "General Customer Service"
            self.trace.append(
                {
                    "type": "llm_call",
                    "purpose": "intent_classification",
                    "attempt": attempt,
                    "input": current_message,
                    "output": classification,
                }
            )
            self._step("intent_interpreted", attempt=attempt, goal=goal, service=service, action=action)
            present(human_message, chatbot_message)
            conversation_history.append({"role": "assistant", "message": human_message})

            valid_pair = (
                action == "ASK_CLARIFICATION"
                or (action == "CONFIRM_BLOCK_REMOVAL" and goal == "BLOCK_REMOVAL")
                or (action == "START_AUTHENTICATION" and goal == "BLOCK_REMOVAL")
                or (action == "OFFER_TRANSFER_OR_FRAUD_HELP" and goal == "NON_FRAUD")
                or (action == "TRANSFER_TO_FRAUD" and goal == "REPORT_FRAUD")
            )
            if not valid_pair:
                return self._escalate(
                    "LLM routing goal and action were inconsistent",
                    "I could not safely route this request. I’m transferring you to a fraud specialist.",
                )

            if action == "TRANSFER_TO_FRAUD":
                return self._escalate(
                    "Customer reports actual or unrecognized fraud",
                    human_message,
                )

            if action == "START_AUTHENTICATION":
                self._step("intent_detected", intent="BLOCK_REMOVAL", attempts=attempt)
                break

            if action == "OFFER_TRANSFER_OR_FRAUD_HELP":
                self._step("department_transfer_offered", department=department)
                raw_response = answer("department_transfer_confirmation", {"prompt": "Customer: ", "department": department})
                response_meaning, interpreted_response = interpret_reply(
                    raw_response,
                    question_type="non_fraud_transfer_or_fraud_help",
                    question=human_message,
                    details={"department": department},
                )
                accepted = response_meaning == "AFFIRMATIVE"
                self._step("department_transfer_confirmation", department=department, confirmed=accepted)
                if accepted:
                    self.tools.transfer_to_department(department)
                    return self._finish(f"I’m transferring you to {department} now.", "transferred")
                if response_meaning == "NEW_REQUEST":
                    conversation_history.append({"role": "customer", "message": interpreted_response})
                    current_message = json.dumps(
                        {"instruction": "Route the customer's latest message; it may replace the earlier topic.", "conversation": conversation_history}
                    )
                    continue
                if response_meaning == "FRAUD_REQUEST":
                    conversation_history.append({"role": "customer", "message": interpreted_response})
                    current_message = json.dumps(
                        {
                            "instruction": "Start a fresh fraud-only routing chain from the customer's latest fraud request.",
                            "conversation": conversation_history,
                        }
                    )
                    attempt = 0
                    self._step("fraud_routing_chain_started", reason="Customer requested fraud help after a non-fraud inquiry")
                    continue
                if response_meaning is None:
                    return self._escalate("Transfer consent remained unclear", "I could not confirm your transfer choice. I’m transferring you to a fraud specialist for help.")
                return self._finish("Thank you for contacting the Fraud Department. Take care.", "safe_stop")

            clarification = ""
            if action == "CONFIRM_BLOCK_REMOVAL":
                confirmation_response = answer("block_removal_intent_confirmation", {"prompt": "Customer: "})
                response_meaning, interpreted_response = interpret_reply(
                    confirmation_response,
                    question_type="block_removal_intent_confirmation",
                    question=human_message,
                    details={"service": service},
                )
                confirmed = response_meaning == "AFFIRMATIVE"
                self._step("intent_confirmation", attempt=attempt, confirmed=confirmed)
                if confirmed:
                    self._step("intent_detected", intent="BLOCK_REMOVAL", attempts=attempt)
                    goal = "BLOCK_REMOVAL"
                    break
                if response_meaning == "NEW_REQUEST":
                    conversation_history.append({"role": "customer", "message": interpreted_response})
                    current_message = json.dumps(
                        {"instruction": "Route the customer's latest message; it may replace the earlier topic.", "conversation": conversation_history}
                    )
                    continue
                if response_meaning == "FRAUD_REQUEST":
                    conversation_history.append({"role": "customer", "message": interpreted_response})
                    current_message = json.dumps(
                        {
                            "instruction": "Start a fresh fraud-only routing chain because the customer now suspects fraud.",
                            "conversation": conversation_history,
                        }
                    )
                    attempt = 0
                    self._step("fraud_routing_chain_started", reason="Customer reported suspected fraud during block-removal routing")
                    continue
                if response_meaning is None:
                    return self._escalate("Block-removal intent confirmation remained unclear", "I could not safely confirm your request. I’m transferring you to a fraud specialist.")
                clarification = confirmation_response

            if attempt == 3:
                return self._escalate(
                    "Intent remained unresolved after three LLM turns",
                    "I’m sorry I could not identify the right service after three attempts. I’m transferring you to a fraud specialist.",
                )

            if action == "ASK_CLARIFICATION":
                clarification = answer(
                    "llm_clarification",
                    {"prompt": "Customer: ", "attempt": attempt + 1},
                ).strip()
            conversation_history.append({"role": "customer", "message": clarification})
            current_message = json.dumps(
                {
                    "instruction": "Route the customer's latest message; it may clarify or completely replace the earlier topic.",
                    "conversation": conversation_history,
                }
            )

        if goal != "BLOCK_REMOVAL":
            return self._escalate(
                "Intent loop ended without an executable route",
                "I could not safely route this request. I’m transferring you to a fraud specialist.",
            )

        card_number = answer(
            "card_number",
            {
                "prompt": "Assistant: Certainly. Before I remove the block, I need to authenticate your identity. Please enter the full fake card number: "
            },
        ).strip()
        date_of_birth = answer("date_of_birth", {"prompt": "Assistant: Please enter your date of birth (YYYY-MM-DD): "}).strip()
        auth = self.tools.authenticate_customer(card_number, date_of_birth)
        if not auth["authenticated"]:
            return self._escalate(
                "Authentication failed; no account data disclosed",
                "I could not verify your identity. No account details were accessed. I’m transferring you to a specialist.",
            )

        customer_id = auth["customer_id"]
        card_id = auth["card_id"]
        self._step("customer_authenticated", customer_id=customer_id, card_id=card_id)
        cards = self.tools.get_customer_cards(customer_id)
        if not any(card["card_id"] == card_id for card in cards["cards"]):
            return self._escalate("Authenticated card was not owned by customer", "I could not verify card ownership. I’m transferring you to a specialist.")

        blocked = self.tools.get_blocked_card(customer_id, card_id)
        card = blocked["card"]
        if not card:
            return self._escalate("Selected card has no active fraud block", "That card does not have an active fraud block. No change was made.")
        self._step("blocked_card_selected", card_id=card_id, display_number=card["display_number"])

        transaction_result = self.tools.get_flagged_transactions(customer_id, card_id, card["fraud_case_id"])
        transactions = transaction_result["transactions"]
        if not transactions:
            return self._escalate("No flagged transactions found for the case", "I could not retrieve the fraud-case transactions. I’m transferring you to a specialist.")

        verified_ids: list[str] = []
        recognized_ids: list[str] = []
        # Transactions are sorted newest-first by the tool. Only the newest one
        # is used for customer verification in the current business workflow.
        transactions_to_ask = transactions[1:2] if flawed and len(transactions) > 1 else transactions[:1]
        for index, transaction in enumerate(transactions_to_ask):
            response = answer(
                "transaction_recognition",
                {
                    "prompt": f"Assistant: Do you recognize {transaction['date']} | {transaction['merchant']} | ${transaction['amount']:.2f}? (yes/no): ",
                    "transaction_id": transaction["transaction_id"],
                    "is_latest": index == 0,
                },
            )
            response_meaning, _interpreted_response = interpret_reply(
                response,
                question_type="transaction_recognition",
                question=f"Do you recognize the {transaction['date']} transaction at {transaction['merchant']} for ${transaction['amount']:.2f}?",
                details={"transaction_id": transaction["transaction_id"]},
            )
            if response_meaning in {None, "NEW_REQUEST"}:
                return self._escalate("Transaction recognition remained unclear", "I could not confirm whether you recognize the transaction. I’m transferring you to a fraud specialist.")
            recognized = response_meaning == "AFFIRMATIVE"
            self._step("transaction_verified", transaction_id=transaction["transaction_id"], recognized=recognized)
            verified_ids.append(transaction["transaction_id"])
            if recognized:
                recognized_ids.append(transaction["transaction_id"])

        if len(recognized_ids) != len(verified_ids):
            return self._escalate(
                "Customer did not recognize every flagged transaction",
                "The block will remain in place. I’m transferring you to a fraud specialist to review the transaction.",
            )

        if flawed:
            # Deliberate defect: confirms an older transaction but claims the
            # newest transaction was confirmed when calling the eligibility tool.
            verified_ids = [transactions[0]["transaction_id"]]
            recognized_ids = verified_ids.copy()
            self._step("flawed_shortcut", detail="Agent claimed the newest transaction was verified")

        eligibility = self.tools.check_removal_eligibility(
            customer_id, card_id, card["fraud_case_id"], verified_ids, recognized_ids
        )
        if not eligibility["eligible"]:
            return self._escalate(
                "Automatic removal eligibility checks failed",
                "This case is not eligible for automatic removal. I’m transferring you to a fraud specialist.",
            )

        removal = self.tools.remove_fraud_block(customer_id, card_id, eligibility["authorization_token"])
        if not removal["removed"]:
            return self._escalate("Removal tool rejected the action", "The block could not be removed. I’m transferring you to a specialist.")
        final_state = self.tools.verify_card_status(customer_id, card_id)
        if final_state["status"] != "active":
            return self._escalate("Final state was not active", "I could not verify the card status. I’m transferring you to a specialist.")
        return self._finish(f"Your card {card['display_number']} is active again. The fraud block was removed.", "completed")
