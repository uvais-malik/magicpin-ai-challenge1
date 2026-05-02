"""Human-readable rationale for every composed message."""

from __future__ import annotations


def build_rationale(trigger_analysis: dict, merchant_analysis: dict, decision: dict) -> str:
    facts = "; ".join(decision.get("key_facts") or ["context signal present"])
    return (
        f"Sent because {trigger_analysis['kind']} maps to {trigger_analysis['intent']} "
        f"with urgency {trigger_analysis['urgency']}. Strategy {decision['angle']} uses {facts}; "
        f"expected outcome: {decision['goal']}."
    )

