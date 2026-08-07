"""Small terminal and trace helpers shared by both entry points."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def print_trace(trace: list[dict[str, Any]]) -> None:
    for event in trace:
        if event.get("type") == "llm_call":
            chatbot_message = event["output"].get("chatbot_message", {})
            if event.get("purpose") == "customer_response_interpretation":
                print(f"  MODEL response interpretation -> {chatbot_message.get('response_meaning')} / {chatbot_message.get('next_action')}")
            else:
                print(f"  MODEL conversational routing -> {chatbot_message.get('goal')} / {chatbot_message.get('next_action')}")
        elif event.get("type") == "tool_call":
            output = event["output"]
            result = "ok"
            for key in ("authenticated", "eligible", "removed", "escalated", "transferred", "status"):
                if key in output:
                    result = str(output[key])
                    break
            print(f"  TOOL  {event['tool']:<31} -> {result}")
        elif event.get("step") == "transaction_verified":
            label = "recognized" if event["recognized"] else "NOT recognized"
            print(f"  CHECK {event['transaction_id']:<30} -> {label}")


def print_report(report: dict[str, Any]) -> None:
    print("\nEVALUATOR REPORT")
    print(f"  OUTCOME:          {report['outcome']}")
    print(f"  TRAJECTORY:       {report['trajectory']}")
    print(f"  SAFETY GATES:     {report['safety_gates']}")
    model_count = report["efficiency"]["model_calls"]
    tool_count = report["efficiency"]["tool_calls"]
    print(f"  EFFICIENCY:       {model_count} model call(s), {tool_count} tool call(s)")
    print(f"  CRITICAL FAILURE: {'YES' if report['critical_failure'] else 'NO'}")
    print(f"  OVERALL RESULT:   {report['overall_result']}")
    sections = (
        ("OUTCOME CHECKS", "outcome_checks", report["outcome_checks"]),
        ("TRAJECTORY CHECKS", "trajectory_checks", report["trajectory_checks"]),
        ("SAFETY GATE CHECKS", "gate_results", report["gate_results"]),
    )
    for title, evidence_key, checks in sections:
        print(f"\n  {title}")
        for name, passed in checks.items():
            status = "PASS" if passed else "FAIL"
            print(f"    [{status}] {name.replace('_', ' ')}")
            print(f"           Evidence: {report['evidence'][evidence_key][name]}")

    print("\n  EFFICIENCY DETAILS")
    for name, value in report["efficiency"].items():
        print(f"    {name.replace('_', ' ')}: {value}")


def save_trace(path: Path, name: str, trace: list[dict[str, Any]], report: dict[str, Any]) -> None:
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps({"run": name, "events": trace, "evaluation": report}, indent=2), encoding="utf-8")
