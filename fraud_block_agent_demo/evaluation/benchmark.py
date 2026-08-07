"""Load the reusable validation set."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


SCENARIO_PATH = Path(__file__).with_name("scenarios.json")


def load_scenarios() -> dict[str, dict[str, Any]]:
    rows = json.loads(SCENARIO_PATH.read_text(encoding="utf-8"))
    return {row["scenario_id"]: row for row in rows}

