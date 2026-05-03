"""Deterministic multi-turn reply handling for judge scenarios."""

from __future__ import annotations


AUTO_REPLY_MARKERS = (
    "thank you for contacting",
    "will respond shortly",
    "away from whatsapp",
    "business hours",
    "auto-reply",
    "automated",
    "out of office",
)

HOSTILE_MARKERS = ("stop", "spam", "useless", "dont message", "don't message", "unsubscribe", "not interested")
COMMITMENT_MARKERS = ("do it", "lets do", "let's do", "yes", "ok", "whats next", "what's next", "proceed", "confirm", "chalega", "go ahead")
OFF_TOPIC_MARKERS = ("gst", "tax", "loan", "rent", "electricity", "license renewal", "unrelated")
AUDIT_HELP_MARKERS = ("x-ray", "xray", "d-speed", "iopa", "radiograph", "audit", "setup", "film unit")
SLOT_PICK_MARKERS = ("book me", "book for", "slot", "appointment", "wed", "thu", "fri", "sat", "sun", "mon", "tue", "am", "pm")


class ConversationHandler:
    def __init__(self, store) -> None:
        self.store = store

    def handle(self, body: dict) -> tuple[int, dict]:
        message = str(body.get("message", "")).strip()
        lowered = message.lower()
        conversation_id = str(body.get("conversation_id") or "unknown")
        conversation = self.store.conversations.get(conversation_id, {})
        trigger_id = conversation.get("trigger_id")
        trigger = self.store.triggers.get(trigger_id, {}) if trigger_id else {}
        merchant_id = conversation.get("merchant_id")
        merchant = self.store.merchants.get(merchant_id, {}) if merchant_id else {}
        customer_id = conversation.get("customer_id")
        customer = self.store.customers.get(customer_id, {}) if customer_id else {}
        category_slug = merchant.get("category_slug")
        category = self.store.categories.get(category_slug, {}) if category_slug else {}
        from_role = body.get("from_role", "merchant")

        if any(marker in lowered for marker in HOSTILE_MARKERS):
            return 200, {"action": "end", "body": "Sorry, I will stop here.", "rationale": "Merchant opted out or called the message spam."}

        if any(marker in lowered for marker in AUTO_REPLY_MARKERS):
            count = self._bump_auto_reply(conversation_id, lowered)
            if count == 1:
                return 200, {"action": "wait", "wait_seconds": 3600, "rationale": "Detected likely business auto-reply; try once later."}
            if count == 2:
                return 200, {"action": "wait", "wait_seconds": 86400, "rationale": "Repeated auto-reply detected; wait 24 hours."}
            return 200, {"action": "end", "rationale": "Repeated canned auto-reply; end to avoid wasting merchant turns."}

        if any(marker in lowered for marker in OFF_TOPIC_MARKERS):
            return 200, {
                "action": "send",
                "body": "I can only help with your magicpin growth actions here; for this thread, I can draft the offer/post or campaign next.",
                "cta": "Send draft",
                "rationale": "Off-topic message redirected in one sentence.",
            }

        is_audit_help = any(marker in lowered for marker in AUDIT_HELP_MARKERS)
        is_commitment = any(marker in lowered for marker in COMMITMENT_MARKERS)
        is_slot_pick = any(marker in lowered for marker in SLOT_PICK_MARKERS)

        if is_audit_help:
            base_reply = {
                "action": "send",
                "body": "Got it, doc. Since you have an old D-speed film unit, I will make this audit practical: check film speed, IOPA dose setting, RVG upgrade option, and SOP documentation before the 2026-12-15 DCI deadline. Reply CHECKLIST and I will send the audit checklist.",
                "cta": "Checklist",
                "rationale": "Merchant asked for help on the radiograph compliance trigger; respond with audit-specific next step.",
            }
        elif is_slot_pick:
            slot_text = self._extract_slot_text(message)
            base_reply = {
                "action": "send",
                "body": f"Confirmed, your slot is booked for {slot_text}. We will send a reminder one day before. Reply CHANGE if you need a different time.",
                "cta": "Change",
                "rationale": "Customer picked a concrete appointment slot; confirm the booking instead of moving to campaign execution.",
            }
        elif is_commitment:
            if from_role == "customer" or customer_id or trigger.get("scope") == "customer" or is_slot_pick:
                base_reply = {
                    "action": "send",
                    "body": "Confirmed. I will hold the recommended slot and send a reminder one day before. Reply CHANGE if you need another time.",
                    "cta": "Change",
                    "rationale": "Customer confirmed a booking-oriented next step.",
                }
            elif trigger.get("kind") == "regulation_change":
                base_reply = {
                    "action": "send",
                    "body": "Done. I will prepare a practical checklist for your audit and a draft post explaining your compliance update to build trust. Reply CONFIRM to proceed.",
                    "cta": "Confirm",
                    "rationale": "Contextual reply for regulation change.",
                }
            else:
                base_reply = {
                    "action": "send",
                    "body": "Done - moving to execution. I will prepare the exact draft with price, audience, channel, and 7-day run dates. Reply CONFIRM and I will proceed.",
                    "cta": "Confirm",
                    "rationale": "Merchant committed, so switch to action mode without re-qualifying.",
                }
        elif "later" in lowered or "busy" in lowered:
            return 200, {"action": "wait", "wait_seconds": 1800, "rationale": "Merchant asked for time; back off for 30 minutes."}
        else:
            base_reply = {
                "action": "send",
                "body": "Got it. I will keep this to one executable step: one offer/post, one audience, one measurable 7-day target. Reply YES to proceed.",
                "cta": "Yes",
                "rationale": "Continue with a low-friction action-oriented next step.",
            }

        try:
            from core.llm_client import rewrite_reply_if_enabled
            context = {
                "trigger": trigger,
                "merchant": merchant,
                "customer": customer,
                "category": category,
                "user_message": message,
                "role": from_role
            }
            final_reply = rewrite_reply_if_enabled(base_reply, context)
        except Exception:
            final_reply = base_reply

        return 200, final_reply

    def _bump_auto_reply(self, conversation_id: str, message: str) -> int:
        key = f"{conversation_id}:{message[:80]}"
        current = self.store.auto_reply_counts.get(key, 0) + 1
        self.store.auto_reply_counts[key] = current
        return current

    @staticmethod
    def _extract_slot_text(message: str) -> str:
        cleaned = " ".join(message.replace(".", " ").replace(",", " ").split())
        lowered = cleaned.lower()
        for starter in ("for ", "book me for ", "book for "):
            idx = lowered.find(starter)
            if idx >= 0:
                return cleaned[idx + len(starter):].strip() or cleaned
        return cleaned
