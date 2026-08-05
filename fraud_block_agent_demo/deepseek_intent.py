"""The demo's single DeepSeek call: classify the opening customer message."""

from __future__ import annotations

import json
import os
from typing import Any

import requests
from dotenv import load_dotenv


SYSTEM_PROMPT = """You are the conversational routing layer for a bank's Fraud Department.
Interpret the customer's latest message using any conversation context supplied. Do not use scripted questions: write the most useful response for this specific customer.

Return exactly one JSON object with two top-level keys:

1. human_message: a warm, concise message shown directly to the customer. It must contain the question or next-step explanation needed for the selected action.
2. chatbot_message: structured instructions for the orchestrator or a future specialist subagent, containing:
   - goal: BLOCK_REMOVAL, REPORT_FRAUD, NON_FRAUD, or UNCLEAR
   - service: short service name, such as fraud block removal or GIC rates
   - department: the best destination in natural language, such as Fraud, Investments, Rewards, Payments, Card Services, or General Customer Service
   - understood: true or false
   - next_action: one of ASK_CLARIFICATION, CONFIRM_BLOCK_REMOVAL, CONFIRM_TRANSFER, or TRANSFER_TO_FRAUD
   - collected_facts: a JSON array of short facts learned from the customer
   - reason: one short routing reason

Rules:
- If information is missing, use ASK_CLARIFICATION and make human_message ask a specific, natural follow-up based on what is missing.
- If the customer appears to want a fraud block removed, use CONFIRM_BLOCK_REMOVAL and ask them to confirm that interpretation.
- If the customer reports unauthorized activity, use TRANSFER_TO_FRAUD and explain the immediate transfer.
- If a clear request belongs elsewhere, use CONFIRM_TRANSFER, name the most appropriate department without relying on a fixed department list, and ask permission to transfer.
- Never request card number, DOB, or other credentials. Deterministic tools handle those later.
- Output JSON only, with no Markdown fences."""


ALLOWED_GOALS = {"BLOCK_REMOVAL", "REPORT_FRAUD", "NON_FRAUD", "UNCLEAR"}
ALLOWED_ACTIONS = {"ASK_CLARIFICATION", "CONFIRM_BLOCK_REMOVAL", "CONFIRM_TRANSFER", "TRANSFER_TO_FRAUD"}

RESPONSE_SYSTEM_PROMPT = """Interpret a customer's response to a specific question in a banking workflow.
Understand natural language such as polite confirmations, refusals, corrections, uncertainty, and indirect answers. Do not rely on exact phrase matching.

Return exactly one JSON object with:
- human_message: a short, natural acknowledgement or a helpful clarification question shown to the customer
- chatbot_message:
  - response_meaning: AFFIRMATIVE, NEGATIVE, or UNCLEAR
  - next_action: CONTINUE, STOP, or ASK_CLARIFICATION
  - interpreted_response: a concise paraphrase
  - reason: one short explanation

Use UNCLEAR and ASK_CLARIFICATION when the response is ambiguous. Do not make banking decisions and do not request credentials. Output JSON only."""

ALLOWED_RESPONSE_MEANINGS = {"AFFIRMATIVE", "NEGATIVE", "UNCLEAR"}
ALLOWED_RESPONSE_ACTIONS = {"CONTINUE", "STOP", "ASK_CLARIFICATION"}


def _call_deepseek(system_prompt: str, message: str) -> dict[str, Any]:
    load_dotenv()
    api_key = os.getenv("DEEPSEEK_API_KEY", "").strip()
    base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com").strip().rstrip("/")
    model = os.getenv("DEEPSEEK_MODEL", "deepseek-chat").strip()
    if not api_key:
        raise RuntimeError("DEEPSEEK_API_KEY is missing. Add it to the repo's existing .env file.")

    response = requests.post(
        f"{base_url}/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={
            "model": model,
            "temperature": 0,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message},
            ],
        },
        timeout=60,
    )
    response.raise_for_status()
    return json.loads(response.json()["choices"][0]["message"]["content"].strip())


def classify_with_deepseek(message: str) -> dict[str, Any]:
    result = _call_deepseek(SYSTEM_PROMPT, message)
    chatbot_message = result.get("chatbot_message", {})
    if not isinstance(result.get("human_message"), str) or not result["human_message"].strip():
        raise RuntimeError("DeepSeek did not return a customer-facing human_message.")
    if chatbot_message.get("goal") not in ALLOWED_GOALS:
        raise RuntimeError("DeepSeek returned an unsupported goal.")
    if chatbot_message.get("next_action") not in ALLOWED_ACTIONS:
        raise RuntimeError("DeepSeek returned an unsupported next_action.")
    return result


def interpret_response_with_deepseek(message: str, context: dict[str, Any]) -> dict[str, Any]:
    prompt = (
        f"Question type: {context['question_type']}\n"
        f"Question asked: {context['question']}\n"
        f"Relevant workflow context: {json.dumps(context.get('details', {}))}\n"
        f"Customer response: {message}"
    )
    result = _call_deepseek(RESPONSE_SYSTEM_PROMPT, prompt)
    chatbot_message = result.get("chatbot_message", {})
    if not isinstance(result.get("human_message"), str) or not result["human_message"].strip():
        raise RuntimeError("DeepSeek did not return a response acknowledgement.")
    if chatbot_message.get("response_meaning") not in ALLOWED_RESPONSE_MEANINGS:
        raise RuntimeError("DeepSeek returned an unsupported response meaning.")
    if chatbot_message.get("next_action") not in ALLOWED_RESPONSE_ACTIONS:
        raise RuntimeError("DeepSeek returned an unsupported response action.")
    valid_pair = {
        "AFFIRMATIVE": "CONTINUE",
        "NEGATIVE": "STOP",
        "UNCLEAR": "ASK_CLARIFICATION",
    }
    if valid_pair[chatbot_message["response_meaning"]] != chatbot_message["next_action"]:
        raise RuntimeError("DeepSeek returned inconsistent response instructions.")
    return result
