"""Public deterministic compose function."""

from __future__ import annotations

from config.constants import SEND_AS_MERCHANT, SEND_AS_VERA
from core.cta_engine import choose_cta
from core.decision_engine import decide_strategy
from core.message_builder import build_message
from core.rationale_engine import build_rationale
from core.suppression import make_suppression_key
from intelligence.category_adapter import adapt_category
from intelligence.customer_adapter import adapt_customer
from intelligence.merchant_analyzer import analyze_merchant
from intelligence.trigger_analyzer import analyze_trigger
from utils.validator import validate_message


def compose(category: dict, merchant: dict, trigger: dict, customer: dict | None = None) -> dict:
    """Compose one production-shaped Vera message.

    The function is deterministic: all choices are rule based and derived from
    the supplied dictionaries. It never calls an external model or API.
    """
    category_profile = adapt_category(category)
    merchant_analysis = analyze_merchant(merchant, category_profile)
    trigger_analysis = analyze_trigger(trigger)
    customer_profile = adapt_customer(customer, merchant, category)
    decision = decide_strategy(category_profile, merchant_analysis, trigger_analysis, customer_profile)

    body = build_message(
        category_profile=category_profile,
        merchant=merchant or {},
        trigger=trigger or {},
        customer_profile=customer_profile,
        merchant_analysis=merchant_analysis,
        trigger_analysis=trigger_analysis,
        decision=decision,
    )
    cta = choose_cta(trigger_analysis, decision, customer_profile)
    message = {
        "body": body,
        "cta": cta,
        "send_as": SEND_AS_MERCHANT if customer_profile.get("present") else SEND_AS_VERA,
        "suppression_key": make_suppression_key(merchant or {}, trigger or {}),
        "rationale": build_rationale(trigger_analysis, merchant_analysis, decision),
    }
    return validate_message(message)

