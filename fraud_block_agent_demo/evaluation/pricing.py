"""Configurable DeepSeek API pricing used for educational cost estimates.

Verified 2026-08-06 against:
https://api-docs.deepseek.com/quick_start/pricing

Prices are USD per one million tokens. DeepSeek may change prices; update this
configuration before relying on estimates in a later session.
"""

from __future__ import annotations

from typing import Any


PRICING_SOURCE = "https://api-docs.deepseek.com/quick_start/pricing"
PRICING_VERIFIED_DATE = "2026-08-06"

MODEL_PRICING: dict[str, dict[str, Any]] = {
    "deepseek-v4-flash": {
        "input_cache_hit_per_million": 0.0028,
        "input_cache_miss_per_million": 0.14,
        "output_per_million": 0.28,
        "currency": "USD",
    },
    "deepseek-v4-pro": {
        "input_cache_hit_per_million": 0.003625,
        "input_cache_miss_per_million": 0.435,
        "output_per_million": 0.87,
        "currency": "USD",
    },
}

# DeepSeek's current documentation identifies these as compatibility names for
# the non-thinking and thinking modes of V4 Flash.
MODEL_ALIASES = {
    "deepseek-chat": "deepseek-v4-flash",
    "deepseek-reasoner": "deepseek-v4-flash",
}


def pricing_for_model(model: str) -> dict[str, Any] | None:
    canonical = MODEL_ALIASES.get(model, model)
    pricing = MODEL_PRICING.get(canonical)
    if not pricing:
        return None
    return {**pricing, "requested_model": model, "priced_as": canonical}

