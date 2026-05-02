"""Dispatch tick triggers into scored, deduplicated actions."""

from __future__ import annotations

from config.constants import MAX_ACTIONS_PER_TICK
from core.composer import compose
from core.suppression import make_suppression_key
from intelligence.category_adapter import adapt_category
from intelligence.merchant_analyzer import analyze_merchant
from rules.priority_rules import trigger_priority


class Dispatcher:
    def __init__(self, store):
        self.store = store

    def actions_for_tick(self, available_trigger_ids: list[str], now: str | None = None) -> list[dict]:
        candidates = []
        for trigger_id in available_trigger_ids:
            trigger = self.store.triggers.get(trigger_id)
            if not trigger:
                continue
            merchant_id = trigger.get("merchant_id")
            merchant = self.store.merchants.get(merchant_id)
            if not merchant:
                continue
            if trigger.get("customer_id") and trigger.get("scope") == "customer" and trigger.get("customer_id") not in self.store.customers:
                continue
            category = self.store.categories.get(merchant.get("category_slug")) or {}
            category_profile = adapt_category(category)
            merchant_analysis = analyze_merchant(merchant, category_profile)
            candidates.append((trigger_priority(trigger, merchant_analysis), trigger_id, trigger, merchant, category))

        candidates.sort(key=lambda item: (-item[0], item[1]))
        actions = []
        for _, trigger_id, trigger, merchant, category in candidates:
            customer = self.store.customers.get(trigger.get("customer_id")) if trigger.get("customer_id") else None
            suppression_key = make_suppression_key(merchant, trigger, now)
            if suppression_key in self.store.sent_suppression_keys:
                continue

            message = compose(category, merchant, trigger, customer)
            self.store.sent_suppression_keys.add(message["suppression_key"])
            conversation_id = self.store.next_conversation_id(merchant.get("merchant_id"), trigger_id)
            self.store.conversations[conversation_id] = {
                "merchant_id": merchant.get("merchant_id"),
                "customer_id": trigger.get("customer_id"),
                "trigger_id": trigger_id,
                "last_body": message["body"],
            }
            actions.append(
                {
                    "conversation_id": conversation_id,
                    "merchant_id": merchant.get("merchant_id"),
                    "customer_id": trigger.get("customer_id"),
                    "send_as": message["send_as"],
                    "trigger_id": trigger_id,
                    "template_name": self._template_name(trigger),
                    "template_params": self._template_params(merchant, trigger),
                    **message,
                }
            )
            if len(actions) >= MAX_ACTIONS_PER_TICK:
                break
        return actions

    @staticmethod
    def _template_name(trigger: dict) -> str:
        kind = trigger.get("kind", "general")
        return f"vera_{kind}_v1"

    @staticmethod
    def _template_params(merchant: dict, trigger: dict) -> list[str]:
        identity = merchant.get("identity", {})
        payload = trigger.get("payload", {})
        return [
            identity.get("name", "merchant"),
            trigger.get("kind", "trigger"),
            str(payload.get("metric") or payload.get("festival") or payload.get("top_item_id") or ""),
        ]
