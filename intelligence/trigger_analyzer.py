"""Trigger analysis: type, urgency, and business intent."""

from __future__ import annotations

from rules.trigger_rules import classify_trigger, normalized_urgency


def analyze_trigger(trigger: dict | None) -> dict:
    trigger = trigger or {}
    trigger_type, intent = classify_trigger(trigger.get("kind", ""))
    urgency = normalized_urgency(trigger)
    return {
        "id": trigger.get("id") or trigger.get("trigger_id") or "trigger_unknown",
        "kind": trigger.get("kind", "unknown"),
        "type": trigger_type,
        "intent": intent,
        "urgency": urgency,
        "scope": trigger.get("scope", "merchant"),
        "source": trigger.get("source", "internal"),
        "payload": trigger.get("payload", {}),
        "expires_at": trigger.get("expires_at"),
    }

