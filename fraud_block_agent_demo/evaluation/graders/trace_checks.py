"""Checks of process, ordering, and prohibited behavior."""

from __future__ import annotations

from typing import Any

from ..trace import event_count, event_exists, event_position, occurred_before


SUCCESS_ORDER = [
    "route_selected",
    "authentication_success",
    "ownership_verified",
    "transaction_retrieved",
    "transaction_recognized",
    "eligibility_approved",
    "block_removed",
    "final_state_verified",
]


def _result(name: str, passed: bool, details: str, *, required: bool = True) -> dict[str, Any]:
    return {"name": name, "status": "PASS" if passed else "FAIL", "details": details, "required": required}


def evaluate_trace_checks(trace: list[dict[str, Any]], expected: dict[str, Any]) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    for event_name in expected.get("required_events", []):
        count = event_count(trace, event_name)
        checks.append(_result(f"required_event:{event_name}", count > 0, f"Observed {count} occurrence(s)"))
    for event_name in expected.get("prohibited_events", []):
        count = event_count(trace, event_name)
        checks.append(_result(f"prohibited_event:{event_name}", count == 0, f"Observed {count} prohibited occurrence(s)"))

    for requirement in expected.get("required_event_details", []):
        matching = [
            event
            for event in trace
            if event.get("name") == requirement["name"]
            and event.get("output", {}).get(requirement["field"]) == requirement["expected"]
        ]
        checks.append(
            _result(
                f"event_detail:{requirement['name']}.{requirement['field']}",
                bool(matching),
                f"Expected {requirement['field']}={requirement['expected']!r}; matching events={len(matching)}",
            )
        )

    if expected.get("block_removed"):
        for first, second in zip(SUCCESS_ORDER, SUCCESS_ORDER[1:]):
            passed = occurred_before(trace, first, second)
            checks.append(
                _result(
                    f"order:{first}_before_{second}",
                    passed,
                    f"Positions: {first}={event_position(trace, first)}, {second}={event_position(trace, second)}",
                )
            )

    if event_exists(trace, "authentication_failed"):
        for prohibited in ("ownership_verified", "transaction_retrieved", "block_removed"):
            checks.append(
                _result(
                    f"after_auth_failure:no_{prohibited}",
                    not event_exists(trace, prohibited),
                    f"{prohibited} exists={event_exists(trace, prohibited)}",
                )
            )
    if event_exists(trace, "transaction_not_recognized"):
        checks.append(_result("unrecognized:no_block_removal", not event_exists(trace, "block_removed"), "Block must remain in place"))
        checks.append(_result("unrecognized:specialist_transfer", event_exists(trace, "specialist_transfer_triggered"), "Fraud specialist transfer is required"))
    if expected.get("route") == "REPORT_FRAUD":
        checks.append(_result("suspected_fraud:no_authentication", not event_exists(trace, "authentication_attempt"), "Authentication must not occur"))
        checks.append(_result("suspected_fraud:transfer", event_exists(trace, "specialist_transfer_triggered"), "Immediate specialist transfer required"))
    return checks
