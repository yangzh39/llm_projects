"""Provider-configurable language-model calls for conversational routing.

The historical DeepSeek environment variables remain supported so existing
local setups continue to work. Shared users can instead configure the generic
``LLM_*`` variables documented in ``.env.example``.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from time import perf_counter
from typing import Any


SYSTEM_PROMPT = """You are the conversational routing layer for a bank's Fraud Department.
Interpret the customer's latest message using any conversation context supplied. Do not use scripted questions: write the most useful response for this specific customer.

Return exactly one JSON object with two top-level keys:

1. human_message: a warm, concise message shown directly to the customer. It must contain the question or next-step explanation needed for the selected action.
2. chatbot_message: structured instructions for the orchestrator or a future specialist subagent, containing:
   - goal: BLOCK_REMOVAL, REPORT_FRAUD, NON_FRAUD, or UNCLEAR
   - service: short service name, such as fraud block removal or GIC rates
   - department: the best destination in natural language, such as Fraud, Investments, Rewards, Payments, Card Services, or General Customer Service
   - understood: true or false
   - next_action: one of ASK_CLARIFICATION, CONFIRM_BLOCK_REMOVAL, START_AUTHENTICATION, OFFER_TRANSFER_OR_FRAUD_HELP, or TRANSFER_TO_FRAUD
   - collected_facts: a JSON array of short facts learned from the customer
   - reason: one short routing reason

Rules:
- The latest customer message has highest priority. Customers may change topics completely; never force a new request to fit an older topic.
- A customer who only says their card is blocked or not working has not yet chosen between block removal and reporting suspected fraud. Use BLOCK_REMOVAL with CONFIRM_BLOCK_REMOVAL. In plain language, say you are sorry the card was blocked, explain that you can help remove the block if the transaction was theirs, and explain that you will transfer them to a fraud specialist if they suspect fraud. Do not ask customers to distinguish between technical terms such as "fraud alert" and "unauthorized activity."
- When the customer explicitly asks to remove a block or unblock the card, and does not report suspected fraud, use BLOCK_REMOVAL with START_AUTHENTICATION. Acknowledge the request and explain that identity authentication is the next step. Do not ask them to confirm the removal request again.
- If information is missing, use ASK_CLARIFICATION and make human_message ask a specific, natural follow-up based on what is missing.
- If the customer reports unauthorized activity, use TRANSFER_TO_FRAUD and explain the immediate transfer.
- If a clear request belongs elsewhere, use OFFER_TRANSFER_OR_FRAUD_HELP and name the most appropriate department without relying on a fixed department list. human_message must politely say the Fraud Department cannot handle that request, offer a transfer, and ask whether the customer has a fraud-related issue instead. Do not ask for product details that Fraud cannot use. For example, a GIC-rate question is already clear enough to offer Investments.
- Never request card number, DOB, or other credentials. Deterministic tools handle those later.
- Output JSON only, with no Markdown fences."""


ALLOWED_GOALS = {"BLOCK_REMOVAL", "REPORT_FRAUD", "NON_FRAUD", "UNCLEAR"}
ALLOWED_ACTIONS = {"ASK_CLARIFICATION", "CONFIRM_BLOCK_REMOVAL", "START_AUTHENTICATION", "OFFER_TRANSFER_OR_FRAUD_HELP", "TRANSFER_TO_FRAUD"}

RESPONSE_SYSTEM_PROMPT = """Interpret a customer's response to a specific question in a banking workflow.
Understand natural language such as polite confirmations, refusals, corrections, uncertainty, and indirect answers. Do not rely on exact phrase matching.

Return exactly one JSON object with:
- human_message: a short, natural acknowledgement or a helpful clarification question shown to the customer
- chatbot_message:
  - response_meaning: AFFIRMATIVE, NEGATIVE, FRAUD_REQUEST, NEW_REQUEST, or UNCLEAR
  - next_action: CONTINUE, STOP, START_FRAUD_SESSION, RECLASSIFY, or ASK_CLARIFICATION
  - interpreted_response: a concise paraphrase
  - reason: one short explanation

Use NEW_REQUEST and RECLASSIFY when the customer changes the subject or provides a different service request instead of answering the question. The newest message must not be interpreted as confirmation of the older topic.
For question_type non_fraud_transfer_or_fraud_help:
- Use AFFIRMATIVE/CONTINUE only when the customer clearly accepts the offered department transfer.
- Use FRAUD_REQUEST/START_FRAUD_SESSION when the customer states that they need help with fraud, a fraud alert, an unrecognized transaction, or a fraud-blocked card.
- Use NEGATIVE/STOP when they decline both transfer and fraud assistance.
- A bare yes that does not make clear whether they want transfer or fraud help is UNCLEAR; ask which option they want.
For question_type block_removal_intent_confirmation:
- Use AFFIRMATIVE/CONTINUE when the customer says they want the block removed or the card unblocked. This is sufficient consent to proceed to authentication; do not ask them to confirm again.
- Use FRAUD_REQUEST/START_FRAUD_SESSION when the customer says they suspect fraud or do not recognize the activity.
- Use NEGATIVE/STOP when they clearly do not want removal and do not report fraud.
Use UNCLEAR and ASK_CLARIFICATION only when the response is genuinely ambiguous. For AFFIRMATIVE, human_message must be a brief acknowledgement only. For NEGATIVE, human_message must be a polite closing statement with no question, transfer offer, or offer of additional help. Do not introduce an unrelated topic or ask a new product question. Do not make banking decisions and do not request credentials. Output JSON only."""

ALLOWED_RESPONSE_MEANINGS = {"AFFIRMATIVE", "NEGATIVE", "FRAUD_REQUEST", "NEW_REQUEST", "UNCLEAR"}
ALLOWED_RESPONSE_ACTIONS = {"CONTINUE", "STOP", "START_FRAUD_SESSION", "RECLASSIFY", "ASK_CLARIFICATION"}


class ApiCallLimitExceeded(RuntimeError):
    """Raised before an API request would exceed the session budget."""


class ApiCallBudget:
    def __init__(self, maximum_calls: int = 10) -> None:
        self.maximum_calls = maximum_calls
        self.calls_used = 0

    def consume(self) -> None:
        if self.calls_used >= self.maximum_calls:
            raise ApiCallLimitExceeded(f"The live evaluation reached its {self.maximum_calls}-call API limit.")
        self.calls_used += 1


@dataclass(frozen=True)
class ModelConfig:
    provider: str
    api_style: str
    api_key: str
    base_url: str
    model: str
    use_json_mode: bool


def _as_bool(value: str, default: bool) -> bool:
    if not value:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def load_model_config() -> ModelConfig:
    """Load generic model settings, falling back to the existing DeepSeek setup."""
    try:
        from dotenv import load_dotenv
    except ModuleNotFoundError:
        # Exported environment variables still work without python-dotenv.
        pass
    else:
        load_dotenv()

    provider = os.getenv("LLM_PROVIDER", "deepseek").strip().lower()
    presets = {
        "deepseek": ("openai", "https://api.deepseek.com", "deepseek-chat", "DEEPSEEK_API_KEY"),
        "openai": ("openai", "https://api.openai.com", "", "OPENAI_API_KEY"),
        "anthropic": ("anthropic", "https://api.anthropic.com", "", "ANTHROPIC_API_KEY"),
        "custom": ("openai", "", "", ""),
    }
    if provider not in presets:
        raise RuntimeError("LLM_PROVIDER must be deepseek, openai, anthropic, or custom.")

    default_style, default_base, default_model, provider_key_name = presets[provider]
    api_style = os.getenv("LLM_API_STYLE", default_style).strip().lower()
    if api_style not in {"openai", "anthropic"}:
        raise RuntimeError("LLM_API_STYLE must be openai or anthropic.")

    legacy_base = os.getenv("DEEPSEEK_BASE_URL", "") if provider == "deepseek" else ""
    legacy_model = os.getenv("DEEPSEEK_MODEL", "") if provider == "deepseek" else ""
    base_url = (os.getenv("LLM_BASE_URL", "").strip() or legacy_base or default_base).rstrip("/")
    model = os.getenv("LLM_MODEL", "").strip() or legacy_model or default_model
    api_key = os.getenv("LLM_API_KEY", "").strip()
    if not api_key and provider_key_name:
        api_key = os.getenv(provider_key_name, "").strip()

    if not base_url:
        raise RuntimeError("LLM_BASE_URL is required for a custom provider.")
    if not model:
        raise RuntimeError("LLM_MODEL is required for the selected provider.")
    if not api_key and provider != "custom":
        raise RuntimeError(f"No API key is configured for the {provider} provider.")

    return ModelConfig(
        provider=provider,
        api_style=api_style,
        api_key=api_key,
        base_url=base_url,
        model=model,
        use_json_mode=_as_bool(os.getenv("LLM_USE_JSON_MODE", ""), api_style == "openai"),
    )


def _openai_endpoint(base_url: str) -> str:
    if base_url.endswith("/chat/completions"):
        return base_url
    if base_url.endswith("/v1"):
        return f"{base_url}/chat/completions"
    return f"{base_url}/v1/chat/completions"


def _anthropic_endpoint(base_url: str) -> str:
    if base_url.endswith("/messages"):
        return base_url
    if base_url.endswith("/v1"):
        return f"{base_url}/messages"
    return f"{base_url}/v1/messages"


def _call_model(system_prompt: str, message: str, budget: ApiCallBudget | None = None) -> dict[str, Any]:
    import requests

    config = load_model_config()

    if budget:
        budget.consume()
    started_at = perf_counter()
    if config.api_style == "anthropic":
        response = requests.post(
            _anthropic_endpoint(config.base_url),
            headers={
                "x-api-key": config.api_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
            },
            json={
                "model": config.model,
                "max_tokens": 1200,
                "temperature": 0,
                "system": system_prompt,
                "messages": [{"role": "user", "content": message}],
            },
            timeout=60,
        )
    else:
        headers = {"Content-Type": "application/json"}
        if config.api_key:
            headers["Authorization"] = f"Bearer {config.api_key}"
        request_body: dict[str, Any] = {
            "model": config.model,
            "temperature": 0,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message},
            ],
        }
        if config.use_json_mode:
            request_body["response_format"] = {"type": "json_object"}
        response = requests.post(
            _openai_endpoint(config.base_url),
            headers=headers,
            json=request_body,
            timeout=60,
        )
    response.raise_for_status()
    payload = response.json()
    if config.api_style == "anthropic":
        content = "".join(block.get("text", "") for block in payload.get("content", []) if block.get("type") == "text")
        raw_usage = payload.get("usage") if isinstance(payload.get("usage"), dict) else None
        usage = None
        if raw_usage:
            usage = {
                **raw_usage,
                "prompt_tokens": raw_usage.get("input_tokens"),
                "completion_tokens": raw_usage.get("output_tokens"),
                "total_tokens": (raw_usage.get("input_tokens") or 0) + (raw_usage.get("output_tokens") or 0),
            }
    else:
        content = payload["choices"][0]["message"]["content"]
        usage = payload.get("usage") if isinstance(payload.get("usage"), dict) else None
    result = json.loads(content.strip())
    result["_api_metrics"] = {
        "provider": config.provider,
        "model": payload.get("model", config.model),
        "usage": usage,
        "latency_ms": (perf_counter() - started_at) * 1000,
    }
    return result


def classify_with_model(message: str, budget: ApiCallBudget | None = None) -> dict[str, Any]:
    result = _call_model(SYSTEM_PROMPT, message, budget)
    chatbot_message = result.get("chatbot_message", {})
    if not isinstance(result.get("human_message"), str) or not result["human_message"].strip():
        raise RuntimeError("The configured model did not return a customer-facing human_message.")
    if chatbot_message.get("goal") not in ALLOWED_GOALS:
        raise RuntimeError("The configured model returned an unsupported goal.")
    if chatbot_message.get("next_action") not in ALLOWED_ACTIONS:
        raise RuntimeError("The configured model returned an unsupported next_action.")
    return result


def interpret_response_with_model(
    message: str,
    context: dict[str, Any],
    budget: ApiCallBudget | None = None,
) -> dict[str, Any]:
    prompt = (
        f"Question type: {context['question_type']}\n"
        f"Question asked: {context['question']}\n"
        f"Relevant workflow context: {json.dumps(context.get('details', {}))}\n"
        f"Customer response: {message}"
    )
    result = _call_model(RESPONSE_SYSTEM_PROMPT, prompt, budget)
    chatbot_message = result.get("chatbot_message", {})
    if not isinstance(result.get("human_message"), str) or not result["human_message"].strip():
        raise RuntimeError("The configured model did not return a response acknowledgement.")
    if chatbot_message.get("response_meaning") not in ALLOWED_RESPONSE_MEANINGS:
        raise RuntimeError("The configured model returned an unsupported response meaning.")
    if chatbot_message.get("next_action") not in ALLOWED_RESPONSE_ACTIONS:
        raise RuntimeError("The configured model returned an unsupported response action.")
    valid_pair = {
        "AFFIRMATIVE": "CONTINUE",
        "NEGATIVE": "STOP",
        "FRAUD_REQUEST": "START_FRAUD_SESSION",
        "NEW_REQUEST": "RECLASSIFY",
        "UNCLEAR": "ASK_CLARIFICATION",
    }
    if valid_pair[chatbot_message["response_meaning"]] != chatbot_message["next_action"]:
        raise RuntimeError("The configured model returned inconsistent response instructions.")
    return result


# Backward-compatible names for existing notebooks or imports.
classify_with_deepseek = classify_with_model
interpret_response_with_deepseek = interpret_response_with_model
