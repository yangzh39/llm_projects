"""Reproducible evaluation entry point; no network or API key required."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from agent import FraudBlockAgent
from evaluation.benchmark import load_scenarios
from evaluation.harness import run_all as run_benchmark_all
from evaluation.harness import run_scenario as run_benchmark_scenario
from evaluation.report import print_benchmark_summary, print_scenario_report
from evaluator import evaluate
from reporting import print_report, print_trace, save_trace
from scenarios import EVALUATION_CASES


ROOT = Path(__file__).resolve().parent


class RecordedAnswers:
    def __init__(self, scenario: dict[str, Any]) -> None:
        self.scenario = scenario
        self.intent_confirmation_index = 0
        self.clarification_index = 0

    def __call__(self, kind: str, context: dict[str, Any]) -> str:
        if kind == "block_removal_intent_confirmation":
            answers = self.scenario.get("intent_confirmations", ["yes"])
            answer = answers[min(self.intent_confirmation_index, len(answers) - 1)]
            self.intent_confirmation_index += 1
            return answer
        if kind == "llm_clarification":
            clarifications = self.scenario.get("clarifications", [""])
            answer = clarifications[min(self.clarification_index, len(clarifications) - 1)]
            self.clarification_index += 1
            return answer
        if kind == "card_number":
            return self.scenario["card_number"]
        if kind == "date_of_birth":
            return self.scenario["date_of_birth"]
        if kind == "transaction_recognition":
            return self.scenario.get("recognition", {}).get(context["transaction_id"], "no")
        if kind == "removal_confirmation":
            return self.scenario.get("confirmation", "no")
        if kind == "department_transfer_confirmation":
            return self.scenario.get("department_transfer", "no")
        raise ValueError(f"Unexpected prompt kind: {kind}")


def run_case(name: str) -> dict[str, Any]:
    scenario = EVALUATION_CASES[name]
    print("\n" + "=" * 72)
    print(f"SCENARIO: {scenario['title']}")
    print("=" * 72)
    print(f"CUSTOMER: {scenario['request']}")

    classification_index = 0

    def recorded_classifier(_message: str) -> dict[str, Any]:
        nonlocal classification_index
        classifications = scenario.get("classifications") or [
            {
                "intent": scenario["intent"],
                "service": scenario.get("service", scenario["intent"].replace("_", " ").title()),
                "summary": scenario.get("summary", scenario["request"]),
                "department": scenario.get("department", "FRAUD"),
            }
        ]
        selected = classifications[min(classification_index, len(classifications) - 1)].copy()
        classification_index += 1
        legacy_intent = selected["intent"]
        goal = "NON_FRAUD" if legacy_intent == "OTHER" else legacy_intent
        action = selected.get("next_action") or {
            "BLOCK_REMOVAL": "CONFIRM_BLOCK_REMOVAL",
            "REPORT_FRAUD": "TRANSFER_TO_FRAUD",
            "OTHER": "OFFER_TRANSFER_OR_FRAUD_HELP",
            "UNCLEAR": "ASK_CLARIFICATION",
        }[legacy_intent]
        department = selected.get("department", scenario.get("department", "Fraud")).replace("_", " ").title()
        summary = selected.get("summary", scenario.get("summary", scenario["request"]))
        human_messages = {
            "CONFIRM_BLOCK_REMOVAL": f"I understand that {summary}. Is that correct?",
            "START_AUTHENTICATION": "Certainly, I can help remove the block. I’ll first authenticate your identity.",
            "TRANSFER_TO_FRAUD": "This may involve unauthorized activity. I’m transferring you to a fraud specialist now.",
            "OFFER_TRANSFER_OR_FRAUD_HELP": f"The Fraud Department does not handle {summary}. I can transfer you to {department}. Before that, is there a fraud-related service I can help you with?",
            "ASK_CLARIFICATION": f"I want to make sure I direct you correctly. {summary}. Could you tell me a little more?",
        }
        return {
            "human_message": human_messages[action],
            "chatbot_message": {
                "goal": goal,
                "service": selected.get("service", legacy_intent.replace("_", " ").title()),
                "department": department,
                "understood": legacy_intent != "UNCLEAR",
                "next_action": action,
                "collected_facts": [],
                "reason": "Recorded result for reproducible evaluation",
            },
        }

    def recorded_response_interpreter(message: str, _context: dict[str, Any]) -> dict[str, Any]:
        normalized = message.strip().lower()
        configured_meaning = scenario.get("response_meanings", {}).get(normalized)
        affirmative = normalized in {"yes", "yes please", "y", "correct"}
        meaning = configured_meaning or ("AFFIRMATIVE" if affirmative else "NEGATIVE")
        next_action = {
            "AFFIRMATIVE": "CONTINUE",
            "NEGATIVE": "STOP",
            "FRAUD_REQUEST": "START_FRAUD_SESSION",
            "NEW_REQUEST": "RECLASSIFY",
            "UNCLEAR": "ASK_CLARIFICATION",
        }[meaning]
        return {
            "human_message": "Thank you. I’ll route your latest request correctly.",
            "chatbot_message": {
                "response_meaning": meaning,
                "next_action": next_action,
                "interpreted_response": message,
                "reason": "Recorded interpretation for reproducible evaluation",
            },
        }

    agent = FraudBlockAgent(ROOT / "data")
    result = agent.run(
        scenario["request"],
        recorded_classifier,
        recorded_response_interpreter,
        RecordedAnswers(scenario),
        flawed=scenario.get("flawed", False),
    )
    print_trace(result["trace"])
    print(f"\nASSISTANT: {result['message']}")
    report = evaluate(result["trace"], scenario["expected_disposition"])
    print_report(report)
    path = ROOT / "traces" / f"evaluation_{name}.json"
    save_trace(path, name, result["trace"], report)
    print(f"  TRACE:            {path.relative_to(ROOT)}")
    return {"result": result, "evaluation": report}


def main() -> None:
    benchmark_scenarios = load_scenarios()
    parser = argparse.ArgumentParser(description="Run the fraud-agent evaluation benchmark.")
    parser.add_argument("--scenario", choices=["all", *benchmark_scenarios], default="all")
    parser.add_argument(
        "--live",
        action="store_true",
        help="Use DeepSeek for one selected scenario, with a hard maximum of 10 API calls.",
    )
    args = parser.parse_args()
    if args.live and args.scenario == "all":
        parser.error("--live requires one explicit --scenario to prevent unexpected API spending")
    if args.scenario == "all":
        reports = run_benchmark_all()
        for report in reports:
            print_scenario_report(report)
        print_benchmark_summary(reports)
        return
    report = run_benchmark_scenario(args.scenario, live=args.live)
    print_scenario_report(report)


if __name__ == "__main__":
    main()
