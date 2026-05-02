"""Language and Hinglish controls."""

from __future__ import annotations


HINGLISH_MARKERS = {"hi", "hindi", "hi-en", "hi-en mix", "hindi_english_natural"}


def prefers_hinglish(merchant: dict | None = None, customer: dict | None = None, category: dict | None = None) -> bool:
    if customer:
        pref = customer.get("identity", {}).get("language_pref") or customer.get("preferences", {}).get("language")
        if pref and any(marker in str(pref).lower() for marker in HINGLISH_MARKERS):
            return True
    languages = (merchant or {}).get("identity", {}).get("languages", [])
    code_mix = (category or {}).get("voice", {}).get("code_mix", "")
    return "hi" in languages or "hindi" in str(code_mix).lower()


def soften_hinglish(text: str, enabled: bool) -> str:
    if not enabled:
        return text
    replacements = {
        "Want summary?": "Summary bheju?",
        "Create offer": "Offer banayein?",
        "Boost campaign": "Boost karein?",
        "Book slot": "Slot book karein?",
        "Show checklist": "Checklist bheju?",
        "Send draft": "Draft bheju?",
        "Want numbers?": "Numbers bheju?",
    }
    return replacements.get(text, text)

