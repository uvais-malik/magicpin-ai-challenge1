"""Customer personalization and consent controls."""

from __future__ import annotations

from utils.language import prefers_hinglish
from utils.validator import has_customer_consent


def adapt_customer(customer: dict | None, merchant: dict | None, category: dict | None) -> dict:
    if not customer:
        return {
            "present": False,
            "name": None,
            "language": None,
            "hinglish": prefers_hinglish(merchant, None, category),
            "consent": True,
            "relationship_facts": [],
        }
    relationship = customer.get("relationship", {})
    facts = []
    if relationship.get("last_visit"):
        facts.append(f"last visit {relationship['last_visit']}")
    if relationship.get("visits_total") is not None:
        facts.append(f"{relationship['visits_total']} visits")
    services = relationship.get("services_received") or []
    if services:
        facts.append(f"last service {services[-1]}")
    return {
        "present": True,
        "name": customer.get("identity", {}).get("name", "there"),
        "language": customer.get("identity", {}).get("language_pref"),
        "hinglish": prefers_hinglish(merchant, customer, category),
        "consent": has_customer_consent(customer),
        "relationship_facts": facts,
        "state": customer.get("state", "unknown"),
        "preferred_time": customer.get("preferences", {}).get("preferred_time") or customer.get("preferences", {}).get("preferred_slots"),
    }
