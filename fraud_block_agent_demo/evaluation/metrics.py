"""Operational metrics and configurable API-cost calculation."""

from __future__ import annotations

from typing import Any

from .pricing import PRICING_SOURCE, PRICING_VERIFIED_DATE, pricing_for_model
from .trace import event_count


DEFAULT_THRESHOLDS = {
    "max_llm_calls": 10,
    "max_clarification_turns": 3,
    "max_tool_calls": 10,
    "max_total_latency_ms": 15000,
}


def calculate_api_cost(usage: dict[str, int], model: str) -> float | None:
    pricing = pricing_for_model(model)
    required = {"prompt_cache_hit_tokens", "prompt_cache_miss_tokens", "completion_tokens"}
    if not pricing or not required.issubset(usage):
        return None
    return (
        usage["prompt_cache_hit_tokens"] / 1_000_000 * pricing["input_cache_hit_per_million"]
        + usage["prompt_cache_miss_tokens"] / 1_000_000 * pricing["input_cache_miss_per_million"]
        + usage["completion_tokens"] / 1_000_000 * pricing["output_per_million"]
    )


def collect_metrics(trace: list[dict[str, Any]], thresholds: dict[str, Any] | None = None) -> dict[str, Any]:
    completed_llm = [
        event
        for event in trace
        if event.get("event_type") == "llm_call"
        and event.get("name") == "llm_interpretation_completed"
        and event.get("status") == "success"
    ]
    tool_calls = [event for event in trace if event.get("event_type") == "tool_call"]
    usage_available = bool(completed_llm) and all(isinstance(event.get("output", {}).get("usage"), dict) for event in completed_llm)
    models = {event.get("output", {}).get("model") for event in completed_llm if event.get("output", {}).get("model")}
    model = next(iter(models)) if len(models) == 1 else None
    usage = None
    estimated_cost = None
    if usage_available:
        usage = {
            "prompt_tokens": sum(int(event["output"]["usage"].get("prompt_tokens", 0)) for event in completed_llm),
            "prompt_cache_hit_tokens": sum(int(event["output"]["usage"].get("prompt_cache_hit_tokens", 0)) for event in completed_llm),
            "prompt_cache_miss_tokens": sum(int(event["output"]["usage"].get("prompt_cache_miss_tokens", 0)) for event in completed_llm),
            "completion_tokens": sum(int(event["output"]["usage"].get("completion_tokens", 0)) for event in completed_llm),
            "total_tokens": sum(int(event["output"]["usage"].get("total_tokens", 0)) for event in completed_llm),
        }
        if model:
            estimated_cost = calculate_api_cost(usage, model)

    applied_thresholds = {**DEFAULT_THRESHOLDS, **(thresholds or {})}
    run_completed = [event for event in trace if event.get("name") == "run_completed"]
    total_latency = (
        float(run_completed[-1].get("duration_ms", 0))
        if run_completed
        else sum(float(event.get("duration_ms", 0)) for event in trace)
    )
    metrics = {
        "llm_calls": len(completed_llm),
        "input_tokens": usage["prompt_tokens"] if usage else None,
        "input_cache_hit_tokens": usage["prompt_cache_hit_tokens"] if usage else None,
        "input_cache_miss_tokens": usage["prompt_cache_miss_tokens"] if usage else None,
        "output_tokens": usage["completion_tokens"] if usage else None,
        "total_tokens": usage["total_tokens"] if usage else None,
        "estimated_api_cost_usd": round(estimated_cost, 8) if estimated_cost is not None else None,
        "pricing_model": pricing_for_model(model)["priced_as"] if model and pricing_for_model(model) else None,
        "pricing_source": PRICING_SOURCE,
        "pricing_verified_date": PRICING_VERIFIED_DATE,
        "tool_calls": len(tool_calls),
        "clarification_turns": event_count(trace, "clarification_requested"),
        "retries": event_count(trace, "tool_retry"),
        "llm_latency_ms": round(sum(float(event.get("duration_ms", 0)) for event in completed_llm), 3),
        "tool_latency_ms": round(sum(float(event.get("duration_ms", 0)) for event in tool_calls), 3),
        "total_latency_ms": round(total_latency, 3),
        "specialist_transfer_occurred": event_count(trace, "specialist_transfer_triggered") > 0,
        "non_fraud_transfer_occurred": event_count(trace, "non_fraud_transfer_triggered") > 0,
        "thresholds": applied_thresholds,
    }
    metrics["threshold_results"] = {
        "llm_calls": metrics["llm_calls"] <= applied_thresholds["max_llm_calls"],
        "clarification_turns": metrics["clarification_turns"] <= applied_thresholds["max_clarification_turns"],
        "tool_calls": metrics["tool_calls"] <= applied_thresholds["max_tool_calls"],
        "total_latency_ms": metrics["total_latency_ms"] <= applied_thresholds["max_total_latency_ms"],
    }
    return metrics
