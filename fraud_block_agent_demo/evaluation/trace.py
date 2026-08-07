"""Structured, privacy-aware run tracing."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


SENSITIVE_KEY_PARTS = ("password", "api_key", "authorization", "date_of_birth", "card_number")


def redact(value: Any, key: str = "") -> Any:
    lowered = key.lower()
    if any(part in lowered for part in SENSITIVE_KEY_PARTS):
        if lowered.endswith("_provided") or isinstance(value, bool):
            return bool(value)
        return "[REDACTED]"
    if isinstance(value, dict):
        return {str(item_key): redact(item_value, str(item_key)) for item_key, item_value in value.items()}
    if isinstance(value, list):
        return [redact(item) for item in value]
    if isinstance(value, tuple):
        return [redact(item) for item in value]
    return value


class RunTracer:
    """Appends structured events while retaining useful legacy aliases."""

    def __init__(self) -> None:
        self.events: list[dict[str, Any]] = []

    def record(
        self,
        event_type: str,
        name: str,
        *,
        status: str = "success",
        input: dict[str, Any] | None = None,
        output: Any = None,
        duration_ms: float = 0.0,
        legacy: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        event = {
            "sequence": len(self.events) + 1,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": event_type,
            "name": name,
            "status": status,
            "input": redact(input or {}),
            "output": redact(output if output is not None else {}),
            "duration_ms": round(max(0.0, duration_ms), 3),
        }
        if legacy:
            event.update(redact(legacy))
        self.events.append(event)
        return event


def event_exists(trace: list[dict[str, Any]], event_name: str) -> bool:
    return any(event.get("name") == event_name for event in trace)


def event_position(trace: list[dict[str, Any]], event_name: str) -> int | None:
    return next((index for index, event in enumerate(trace) if event.get("name") == event_name), None)


def event_count(trace: list[dict[str, Any]], event_name: str) -> int:
    return sum(event.get("name") == event_name for event in trace)


def occurred_before(trace: list[dict[str, Any]], first_event: str, second_event: str) -> bool:
    first = event_position(trace, first_event)
    second = event_position(trace, second_event)
    return first is not None and second is not None and first < second

