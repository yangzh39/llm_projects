"""Interactive DeepSeek-powered entry point for live exploration."""

from __future__ import annotations

from getpass import getpass
from pathlib import Path
from typing import Any

from agent import FraudBlockAgent
from deepseek_intent import classify_with_deepseek, interpret_response_with_deepseek
from evaluator import evaluate
from reporting import save_trace


ROOT = Path(__file__).resolve().parent


def interactive_answer(_kind: str, context: dict[str, Any]) -> str:
    if _kind in {"card_number", "date_of_birth"}:
        return getpass(context["prompt"])
    return input(context["prompt"])


def display_llm_output(human_message: str, _chatbot_message: dict[str, Any]) -> None:
    print(f"\nAssistant: {human_message}")


def main() -> None:
    print("Fraud Block Agent — interactive demo")
    print("Use only the fake profiles listed in README.md. Type Ctrl+C to stop.\n")
    request = input("Customer: ").strip()
    if not request:
        print("Please enter a customer message.")
        return

    agent = FraudBlockAgent(ROOT / "data")
    try:
        result = agent.run(
            request,
            classify_with_deepseek,
            interpret_response_with_deepseek,
            interactive_answer,
            display_llm_output,
        )
    except Exception as error:
        print(f"\nIntent service unavailable: {error}")
        print("No banking tools were called. Please try again or transfer to a specialist.")
        return

    print(f"\nAssistant: {result['message']}")
    report = evaluate(result["trace"])
    path = ROOT / "traces" / "explore.json"
    save_trace(path, "interactive_exploration", result["trace"], report)


if __name__ == "__main__":
    main()
