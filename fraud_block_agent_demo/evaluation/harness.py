"""Benchmark harness: execute, trace, grade, measure, and persist one scenario."""

from __future__ import annotations

import json
from functools import partial
from pathlib import Path
from time import perf_counter
from typing import Any

from agent import FraudBlockAgent

from .benchmark import load_scenarios
from .graders.code_checks import evaluate_code_checks
from .graders.trace_checks import evaluate_trace_checks
from .metrics import collect_metrics


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = Path(__file__).with_name("outputs")


class ScenarioAnswers:
    def __init__(self, scenario: dict[str, Any]) -> None:
        self.scenario = scenario
        self.clarification_index = 0
        self.intent_confirmation_index = 0

    def __call__(self, kind: str, context: dict[str, Any]) -> str:
        answers = self.scenario.get("answers", {})
        if kind == "llm_clarification":
            values = answers.get("clarifications", [""])
            value = values[min(self.clarification_index, len(values) - 1)]
            self.clarification_index += 1
            return value
        if kind == "response_clarification":
            values = answers.get("response_clarifications", ["Please interpret my latest request."])
            return values[0]
        if kind == "block_removal_intent_confirmation":
            values = answers.get("intent_confirmations", ["yes, remove the block"])
            value = values[min(self.intent_confirmation_index, len(values) - 1)]
            self.intent_confirmation_index += 1
            return value
        if kind == "department_transfer_confirmation":
            return answers.get("department_transfer", "no")
        if kind in {"card_number", "date_of_birth"}:
            return answers[kind]
        if kind == "transaction_recognition":
            return answers.get("recognition", {}).get(context["transaction_id"], "no")
        raise ValueError(f"No recorded answer for prompt kind {kind!r}")


class RecordedModels:
    def __init__(self, scenario: dict[str, Any]) -> None:
        self.scenario = scenario
        self.classification_index = 0

    def classify(self, _message: str) -> dict[str, Any]:
        rows = self.scenario["classifications"]
        selected = rows[min(self.classification_index, len(rows) - 1)]
        self.classification_index += 1
        legacy_intent = selected["intent"]
        goal = "NON_FRAUD" if legacy_intent == "OTHER" else legacy_intent
        action = selected.get("next_action") or {
            "BLOCK_REMOVAL": "CONFIRM_BLOCK_REMOVAL",
            "REPORT_FRAUD": "TRANSFER_TO_FRAUD",
            "OTHER": "OFFER_TRANSFER_OR_FRAUD_HELP",
            "UNCLEAR": "ASK_CLARIFICATION",
        }[legacy_intent]
        department = selected.get("department", "Fraud")
        service = selected.get("service", legacy_intent.replace("_", " ").title())
        messages = {
            "START_AUTHENTICATION": "Certainly. I’ll authenticate your identity before removing the block.",
            "CONFIRM_BLOCK_REMOVAL": "I can help remove the block if the transaction was yours. Would you like to continue?",
            "TRANSFER_TO_FRAUD": "This may be fraud. I’m transferring you to a fraud specialist now.",
            "OFFER_TRANSFER_OR_FRAUD_HELP": f"The Fraud Department cannot handle {service}. I can transfer you to {department}, or help with a fraud-related issue.",
            "ASK_CLARIFICATION": "Could you tell me whether this concerns a blocked card, suspected fraud, or another service?",
        }
        return {
            "human_message": messages[action],
            "chatbot_message": {
                "goal": goal,
                "service": service,
                "department": department,
                "understood": legacy_intent != "UNCLEAR",
                "next_action": action,
                "collected_facts": [],
                "reason": "Recorded benchmark interpretation",
            },
        }

    def interpret(self, message: str, _context: dict[str, Any]) -> dict[str, Any]:
        normalized = message.strip().lower()
        configured = self.scenario.get("response_meanings", {}).get(normalized)
        affirmative = normalized in {"yes", "yes please", "y", "correct", "yes, remove the block", "please transfer me."}
        meaning = configured or ("AFFIRMATIVE" if affirmative else "NEGATIVE")
        action = {
            "AFFIRMATIVE": "CONTINUE",
            "NEGATIVE": "STOP",
            "FRAUD_REQUEST": "START_FRAUD_SESSION",
            "NEW_REQUEST": "RECLASSIFY",
            "UNCLEAR": "ASK_CLARIFICATION",
        }[meaning]
        return {
            "human_message": "Thank you; I understand your response.",
            "chatbot_message": {
                "response_meaning": meaning,
                "next_action": action,
                "interpreted_response": message,
                "reason": "Recorded benchmark response interpretation",
            },
        }


def _card_state(agent: FraudBlockAgent) -> dict[str, str]:
    return {card["card_id"]: card["status"] for card in agent.tools.cards}


def run_scenario(
    scenario_id: str,
    *,
    live: bool = False,
    save_output: bool = True,
) -> dict[str, Any]:
    scenarios = load_scenarios()
    scenario = scenarios[scenario_id]
    agent = FraudBlockAgent(ROOT / "data")
    initial_state = _card_state(agent)
    answers = ScenarioAnswers(scenario)
    if live:
        from deepseek_intent import ApiCallBudget, classify_with_deepseek, interpret_response_with_deepseek

        budget = ApiCallBudget(maximum_calls=10)
        classifier = partial(classify_with_deepseek, budget=budget)
        interpreter = partial(interpret_response_with_deepseek, budget=budget)
    else:
        recorded = RecordedModels(scenario)
        classifier = recorded.classify
        interpreter = recorded.interpret

    started_at = perf_counter()
    result = agent.run(
        scenario["customer_inputs"][0],
        classifier,
        interpreter,
        answers,
        flawed=bool(scenario.get("demo_only_flawed")),
    )
    end_to_end_ms = (perf_counter() - started_at) * 1000
    agent.tracer.record(
        "run",
        "run_completed",
        output={"scenario_id": scenario_id, "live_api": live},
        duration_ms=end_to_end_ms,
    )
    final_state = _card_state(agent)
    expected = {**scenario["expected"], "initial_card_id": scenario.get("initial_state", {}).get("card_id")}
    code_checks = evaluate_code_checks(agent.trace, expected, final_state)
    trace_checks = evaluate_trace_checks(agent.trace, expected)
    metrics = collect_metrics(agent.trace, expected.get("metric_thresholds"))
    code_failures = [check for check in code_checks if check.get("required", True) and check["status"] == "FAIL"]
    trace_failures = [check for check in trace_checks if check.get("required", True) and check["status"] == "FAIL"]
    failure_reasons = [f"code check failed: {check['name']}" for check in code_failures]
    failure_reasons.extend(f"trace check failed: {check['name']}" for check in trace_failures)
    report = {
        "scenario": {
            "scenario_id": scenario_id,
            "description": scenario["description"],
            "initial_state": scenario.get("initial_state", {}),
            "expected": scenario["expected"],
            "live_api": live,
        },
        "agent_result": {
            "message": result["message"],
            "disposition": result["disposition"],
            "initial_card_state": initial_state,
            "final_card_state": final_state,
        },
        "trace": agent.trace,
        "code_checks": code_checks,
        "trace_checks": trace_checks,
        "metrics": metrics,
        "overall_result": "FAIL" if code_failures or trace_failures else "PASS",
        "failure_reasons": failure_reasons,
    }
    if save_output:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        suffix = "_live" if live else ""
        path = OUTPUT_DIR / f"{scenario_id}{suffix}.json"
        path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        report["output_path"] = str(path)
    return report


def run_all(*, save_output: bool = True) -> list[dict[str, Any]]:
    return [run_scenario(scenario_id, save_output=save_output) for scenario_id in load_scenarios()]
