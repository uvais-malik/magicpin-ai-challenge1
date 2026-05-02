"""Trigger classification and urgency rules."""

from __future__ import annotations

from config.mappings import TRIGGER_CLASSIFICATION


def classify_trigger(kind: str) -> tuple[str, str]:
    return TRIGGER_CLASSIFICATION.get(kind, ("general", "info"))


def normalized_urgency(trigger: dict) -> int:
    try:
        return max(1, min(5, int(trigger.get("urgency", 1))))
    except (TypeError, ValueError):
        return 1

