"""Concise, presentation-friendly terminal reporting."""

from __future__ import annotations

from typing import Any


def _print_checks(title: str, checks: list[dict[str, Any]]) -> None:
    print(f"\n{title}")
    for check in checks:
        marker = "✓" if check["status"] == "PASS" else "✗"
        print(f"  {marker} [{check['status']}] {check['name']}")
        if check.get("details"):
            print(f"      {check['details']}")


def print_scenario_report(report: dict[str, Any]) -> None:
    print("\n" + "=" * 78)
    print("SCENARIO")
    print(f"  {report['scenario']['scenario_id']}: {report['scenario']['description']}")
    print("\nAGENT RESULT")
    print(f"  Disposition: {report['agent_result']['disposition']}")
    print(f"  Message: {report['agent_result']['message']}")
    _print_checks("CODE CHECKS", report["code_checks"])
    _print_checks("TRACE CHECKS", report["trace_checks"])
    metrics = report["metrics"]
    print("\nMETRICS")
    print(f"  LLM calls: {metrics['llm_calls']}")
    print(f"  Input / output tokens: {metrics['input_tokens']} / {metrics['output_tokens']}")
    cost = metrics["estimated_api_cost_usd"]
    print(f"  Estimated API cost: {'N/A (recorded model outputs)' if cost is None else f'${cost:.8f}'}")
    print(f"  Tool calls: {metrics['tool_calls']}")
    print(f"  Clarification turns / retries: {metrics['clarification_turns']} / {metrics['retries']}")
    print(f"  LLM / tool / end-to-end latency: {metrics['llm_latency_ms']:.1f} / {metrics['tool_latency_ms']:.1f} / {metrics['total_latency_ms']:.1f} ms")
    print(f"  Specialist transfer: {metrics['specialist_transfer_occurred']}")
    print("\nOVERALL DECISION")
    print(f"  {report['overall_result']} — {'; '.join(report['failure_reasons']) if report['failure_reasons'] else 'all required code and trace checks passed'}")


def print_benchmark_summary(reports: list[dict[str, Any]]) -> None:
    passed = sum(report["overall_result"] == "PASS" for report in reports)
    print("\n" + "=" * 78)
    print("BENCHMARK SUMMARY")
    for report in reports:
        print(
            f"  [{report['overall_result']}] {report['scenario']['scenario_id']:<42} "
            f"LLM={report['metrics']['llm_calls']:<2} tools={report['metrics']['tool_calls']:<2} "
            f"cost={report['metrics']['estimated_api_cost_usd']}"
        )
    print(f"\n  Expected-valid scenarios passed: {passed}/{len(reports)}")
    print("  Note: hidden_workflow_failure is expected to receive OVERALL FAIL.")

