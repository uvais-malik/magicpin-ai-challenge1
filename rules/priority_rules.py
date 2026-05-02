"""Priority rules for proactive dispatch."""

from __future__ import annotations


KIND_PRIORITY = {
    "active_planning_intent": 100,
    "regulation_change": 95,
    "perf_dip": 90,
    "review_theme_emerged": 86,
    "renewal_due": 84,
    "recall_due": 80,
    "customer_lapsed_soft": 78,
    "customer_lapsed_hard": 78,
    "perf_spike": 74,
    "festival_upcoming": 72,
    "ipl_match_today": 72,
    "research_digest": 62,
    "curious_ask_due": 54,
}


def trigger_priority(trigger: dict, merchant_analysis: dict | None = None) -> int:
    base = KIND_PRIORITY.get(trigger.get("kind"), 50)
    urgency = int(trigger.get("urgency") or 1)
    severity = (merchant_analysis or {}).get("severity", 0)
    return base + urgency * 4 + int(severity / 10)

