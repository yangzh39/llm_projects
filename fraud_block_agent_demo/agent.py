"""One orchestrating agent; language handles intent, tools enforce decisions."""

from __future__ import annotations

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
        ) -> bool | None:
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
                present(str(interpretation.get("human_message", "")).strip(), chatbot_message)
                if meaning == "AFFIRMATIVE":
                    return True
                if meaning == "NEGATIVE":
                    return False
                if response_attempt < 3:
                    response = answer("response_clarification", {"prompt": "Customer: ", "question_type": question_type})
            return None

        current_message = request
        clarification_history: list[str] = []
        classification: dict[str, Any] = {}
        goal = "UNCLEAR"
        for attempt in range(1, 4):
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

            valid_pair = (
                action == "ASK_CLARIFICATION"
                or (action == "CONFIRM_BLOCK_REMOVAL" and goal == "BLOCK_REMOVAL")
                or (action == "CONFIRM_TRANSFER" and goal == "NON_FRAUD")
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

            if action == "CONFIRM_TRANSFER":
                self._step("department_transfer_offered", department=department)
                raw_response = answer("department_transfer_confirmation", {"prompt": "Customer: ", "department": department})
                accepted = interpret_reply(
                    raw_response,
                    question_type="department_transfer_confirmation",
                    question=human_message,
                    details={"department": department},
                )
                self._step("department_transfer_confirmation", department=department, confirmed=accepted)
                if accepted:
                    self.tools.transfer_to_department(department)
                    return self._finish(f"I’m transferring you to {department} now.", "transferred")
                if accepted is None:
                    return self._escalate("Transfer consent remained unclear", "I could not confirm your transfer choice. I’m transferring you to a fraud specialist for help.")
                return self._finish("Okay. No transfer was made. Please contact us again if you need help.", "safe_stop")

            clarification = ""
            if action == "CONFIRM_BLOCK_REMOVAL":
                confirmation_response = answer("block_removal_intent_confirmation", {"prompt": "Customer: "})
                confirmed = interpret_reply(
                    confirmation_response,
                    question_type="block_removal_intent_confirmation",
                    question=human_message,
                    details={"service": service},
                )
                self._step("intent_confirmation", attempt=attempt, confirmed=confirmed)
                if confirmed:
                    self._step("intent_detected", intent="BLOCK_REMOVAL", attempts=attempt)
                    goal = "BLOCK_REMOVAL"
                    break
                if confirmed is None:
                    return self._escalate("Block-removal intent confirmation remained unclear", "I could not safely confirm your request. I’m transferring you to a fraud specialist.")
                clarification = f"The customer rejected the previous interpretation by replying: {confirmation_response}"

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
            clarification_history.append(clarification)
            current_message = (
                f"Original request: {request}\n"
                f"Customer clarifications: {' | '.join(clarification_history)}"
            )

        if goal != "BLOCK_REMOVAL":
            return self._escalate(
                "Intent loop ended without an executable route",
                "I could not safely route this request. I’m transferring you to a fraud specialist.",
            )

        card_number = answer("card_number", {"prompt": "Assistant: To verify your identity, please enter the full fake card number: "}).strip()
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
        transactions_to_ask = transactions[:2] if flawed else transactions
        for index, transaction in enumerate(transactions_to_ask):
            response = answer(
                "transaction_recognition",
                {
                    "prompt": f"Assistant: Do you recognize {transaction['date']} | {transaction['merchant']} | ${transaction['amount']:.2f}? (yes/no): ",
                    "transaction_id": transaction["transaction_id"],
                    "is_latest": index == 0,
                },
            )
            recognized = interpret_reply(
                response,
                question_type="transaction_recognition",
                question=f"Do you recognize the {transaction['date']} transaction at {transaction['merchant']} for ${transaction['amount']:.2f}?",
                details={"transaction_id": transaction["transaction_id"]},
            )
            if recognized is None:
                return self._escalate("Transaction recognition remained unclear", "I could not confirm whether you recognize the transaction. I’m transferring you to a fraud specialist.")
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
            # Deliberate defect: claims an unasked third transaction was confirmed.
            verified_ids = [item["transaction_id"] for item in transactions]
            recognized_ids = verified_ids.copy()
            self._step("flawed_shortcut", detail="Agent claimed an unasked transaction was verified")

        eligibility = self.tools.check_removal_eligibility(
            customer_id, card_id, card["fraud_case_id"], verified_ids, recognized_ids
        )
        if not eligibility["eligible"]:
            return self._escalate(
                "Automatic removal eligibility checks failed",
                "This case is not eligible for automatic removal. I’m transferring you to a fraud specialist.",
            )

        removal_question = f"Remove the fraud block from {card['display_number']}?"
        removal_response = answer("removal_confirmation", {"prompt": f"Assistant: {removal_question} (yes/no): "})
        confirmed = interpret_reply(
            removal_response,
            question_type="final_removal_confirmation",
            question=removal_question,
            details={"card_id": card_id, "display_number": card["display_number"]},
        )
        self._step("explicit_confirmation", confirmed=confirmed)
        if confirmed is None:
            return self._escalate("Final removal confirmation remained unclear", "I could not confirm permission to remove the block. I’m transferring you to a fraud specialist.")
        if not confirmed:
            return self._finish("No change was made because you did not confirm removal.", "safe_stop")

        removal = self.tools.remove_fraud_block(customer_id, card_id, confirmed, eligibility["authorization_token"])
        if not removal["removed"]:
            return self._escalate("Removal tool rejected the action", "The block could not be removed. I’m transferring you to a specialist.")
        final_state = self.tools.verify_card_status(customer_id, card_id)
        if final_state["status"] != "active":
            return self._escalate("Final state was not active", "I could not verify the card status. I’m transferring you to a specialist.")
        return self._finish(f"Your card {card['display_number']} is active again. The fraud block was removed.", "completed")
