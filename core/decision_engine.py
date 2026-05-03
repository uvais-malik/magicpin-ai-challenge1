"""Explicit reasoning layer for strategy selection."""

from __future__ import annotations

from config.constants import (
    STRATEGY_CURIOSITY,
    STRATEGY_LOSS_AVERSION,
    STRATEGY_OPPORTUNITY,
    STRATEGY_REACTIVATION,
    STRATEGY_URGENCY,
)


def decide_strategy(category_profile: dict, merchant_analysis: dict, trigger_analysis: dict, customer_profile: dict) -> dict:
    kind = trigger_analysis["kind"]
    trigger_type = trigger_analysis["type"]
    intent = trigger_analysis["intent"]

    if trigger_type in {"recall", "refill", "reactivation", "renewal"} or kind in {"winback_eligible", "customer_lapsed_hard", "customer_lapsed_soft", "dormant_with_vera"}:
        angle = STRATEGY_REACTIVATION
        goal = "recover a known customer or merchant relationship with one low-friction action"
    elif trigger_type == "planning":
        angle = STRATEGY_OPPORTUNITY
        goal = "convert the merchant's stated intent into an executable campaign"
    elif trigger_type in {"performance_drop", "review_theme", "competition", "profile_verification"} or merchant_analysis["performance_dip"]:
        angle = STRATEGY_LOSS_AVERSION
        goal = "recover lost calls, views, or conversion before it compounds"
    elif trigger_type in {"festival", "event", "compliance", "supply_alert"} or trigger_analysis["urgency"] >= 4:
        angle = STRATEGY_URGENCY
        goal = "act before the time window closes"
    elif trigger_type in {"research", "curiosity", "education"}:
        angle = STRATEGY_CURIOSITY
        goal = "open a useful knowledge-led conversation"
    elif merchant_analysis["performance_spike"] or intent == "opportunity":
        angle = STRATEGY_OPPORTUNITY
        goal = "convert momentum into bookings, orders, or leads"
    else:
        angle = STRATEGY_CURIOSITY
        goal = "surface a specific fact worth replying to"

    if trigger_analysis["kind"] == "research_digest":
        levers = ["curiosity", "reciprocity", "source credibility"]
    elif trigger_analysis["kind"] in {"perf_dip", "seasonal_perf_dip"}:
        levers = ["loss aversion", "social proof", "effort externalization"]
    elif trigger_analysis["kind"] == "renewal_due":
        levers = ["loss aversion", "binary commitment"]
    elif trigger_analysis["type"] in {"recall", "refill"}:
        levers = ["effort externalization", "specific slot choice"]
    elif trigger_analysis["kind"] == "competitor_opened":
        levers = ["loss aversion", "curiosity", "competitive proof"]
    elif trigger_analysis["kind"] == "curious_ask_due":
        levers = ["pure curiosity", "low-stakes question"]
    elif trigger_analysis["kind"] in {"supply_alert", "regulation_change", "gbp_unverified"}:
        levers = ["urgency", "trust protection", "checklist"]
    elif trigger_analysis["kind"] == "active_planning_intent":
        levers = ["effort externalization", "ready draft"]
    else:
        levers = [angle.lower().replace("_", " "), "low-friction CTA"]

    key_facts = []
    if merchant_analysis["drop_pct"]:
        key_facts.append(f"{merchant_analysis['drop_metric']} down {int(merchant_analysis['drop_pct'] * 100)}%")
    if merchant_analysis["spike_pct"]:
        key_facts.append(f"{merchant_analysis['spike_metric']} up {int(merchant_analysis['spike_pct'] * 100)}%")
    if merchant_analysis["ctr_below_peer"]:
        key_facts.append(f"CTR {merchant_analysis['ctr']:.1%} vs peer {merchant_analysis['peer_ctr']:.1%}")
    if merchant_analysis["stale_days"]:
        key_facts.append(f"last post {merchant_analysis['stale_days']} days ago")
    payload = trigger_analysis.get("payload", {})
    for key in ("delta_pct", "days_remaining", "days_until", "occurrences_30d", "value_now", "renewal_amount"):
        if key in payload:
            key_facts.append(f"{key}={payload[key]}")

    return {
        "angle": angle,
        "goal": goal,
        "key_facts": key_facts[:5],
        "tone": category_profile["tone"],
        "severity": merchant_analysis["severity"],
        "levers": levers,
    }
