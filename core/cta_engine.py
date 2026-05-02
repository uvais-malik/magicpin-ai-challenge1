"""CTA selection with a single primary action."""

from __future__ import annotations

from config.mappings import CTA_BY_INTENT
from utils.language import soften_hinglish


def choose_cta(trigger_analysis: dict, decision: dict, customer_profile: dict) -> str:
    intent = trigger_analysis["intent"]
    trigger_type = trigger_analysis["type"]
    choices = CTA_BY_INTENT.get(intent, CTA_BY_INTENT["info"])
    cta = choices.get(trigger_type) or choices.get("default") or "Reply"
    return soften_hinglish(cta, customer_profile.get("hinglish", False))

