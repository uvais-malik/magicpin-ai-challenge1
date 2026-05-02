"""Adapts category context into messaging constraints."""

from __future__ import annotations

from config.mappings import CATEGORY_DEFAULTS


def adapt_category(category: dict | None) -> dict:
    category = category or {}
    slug = category.get("slug") or category.get("category_slug") or "generic"
    defaults = CATEGORY_DEFAULTS.get(slug, CATEGORY_DEFAULTS["generic"])
    voice = category.get("voice", {})
    return {
        "slug": slug,
        "display_name": category.get("display_name", slug.title()),
        "tone": voice.get("tone") or defaults["tone"],
        "allowed_vocabulary": voice.get("vocab_allowed") or defaults["allowed"],
        "taboo_words": voice.get("vocab_taboo") or voice.get("taboos") or defaults["taboo"],
        "salutation_template": defaults["salutation"],
        "peer_stats": category.get("peer_stats", {}),
        "offer_catalog": category.get("offer_catalog", []),
        "digest": category.get("digest", []),
        "seasonal_beats": category.get("seasonal_beats", []),
        "trend_signals": category.get("trend_signals", []),
    }


def select_offer(category_profile: dict, merchant: dict, trigger: dict) -> dict:
    active = [o for o in merchant.get("offers", []) if o.get("status") == "active"]
    if active:
        return active[0]
    catalog = category_profile.get("offer_catalog", [])
    kind = trigger.get("kind", "")
    if "restaurant" in category_profile.get("slug", "") or kind == "ipl_match_today":
        for offer in catalog:
            if "match" in offer.get("title", "").lower() or "thali" in offer.get("title", "").lower():
                return offer
    for offer in catalog:
        title = offer.get("title", "").lower()
        if "@" in offer.get("title", "") or "free" in title:
            return offer
    return catalog[0] if catalog else {"title": "starter offer", "value": "0"}


def find_digest_item(category_profile: dict, trigger: dict) -> dict:
    payload = trigger.get("payload", {})
    item_id = payload.get("top_item_id")
    if isinstance(payload.get("top_item"), dict):
        return payload["top_item"]
    for item in category_profile.get("digest", []):
        if item.get("id") == item_id:
            return item
    return (category_profile.get("digest") or [{}])[0]

