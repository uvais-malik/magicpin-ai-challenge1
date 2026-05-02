"""Small local scoring helper for deterministic sanity checks."""

from __future__ import annotations

import re


def heuristic_score(message: dict) -> dict:
    body = message.get("body", "")
    numbers = len(re.findall(r"\d+", body))
    has_cta = bool(message.get("cta"))
    has_fact_flow = all(token in body for token in ["Fact:", "Insight:", "Action:"])
    return {
        "specificity": min(10, 4 + numbers),
        "engagement_compulsion": 8 if has_cta else 4,
        "structure": 10 if has_fact_flow else 5,
        "notes": "Heuristic only; judge_simulator.py remains the real evaluator.",
    }

