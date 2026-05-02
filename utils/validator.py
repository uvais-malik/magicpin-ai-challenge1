"""Output validation for the composition contract."""

from __future__ import annotations

from config.constants import SEND_AS_MERCHANT, SEND_AS_VERA

REQUIRED_KEYS = {"body", "cta", "send_as", "suppression_key", "rationale"}


def validate_message(message: dict) -> dict:
    missing = REQUIRED_KEYS.difference(message)
    if missing:
        raise ValueError(f"compose output missing fields: {sorted(missing)}")
    if message["send_as"] not in {SEND_AS_VERA, SEND_AS_MERCHANT}:
        raise ValueError("send_as must be vera or merchant_on_behalf")
    for key in REQUIRED_KEYS:
        if message[key] is None:
            raise ValueError(f"{key} cannot be None")
    return message


def has_customer_consent(customer: dict | None) -> bool:
    if customer is None:
        return True
    consent = customer.get("consent", {})
    if not consent:
        return False
    if consent.get("revoked_at"):
        return False
    if consent.get("opted_out"):
        return False
    return bool(consent.get("opted_in_at") or consent.get("scope") or consent.get("source"))

