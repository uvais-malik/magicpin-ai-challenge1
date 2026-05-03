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


class ConversationHandler:
    def __init__(self, store) -> None:
        self.store = store

    def handle(self, body: dict) -> tuple[int, dict]:
        message = str(body.get("message", "")).strip()
        lowered = message.lower()
        conversation_id = str(body.get("conversation_id") or "unknown")

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

        if any(marker in lowered for marker in COMMITMENT_MARKERS):
            return 200, {
                "action": "send",
                "body": "Done - moving to execution. I will prepare the exact draft with price, audience, channel, and 7-day run dates. Reply CONFIRM and I will proceed.",
                "cta": "Confirm",
                "rationale": "Merchant committed, so switch to action mode without re-qualifying.",
            }

        if "later" in lowered or "busy" in lowered:
            return 200, {"action": "wait", "wait_seconds": 1800, "rationale": "Merchant asked for time; back off for 30 minutes."}

        return 200, {
            "action": "send",
            "body": "Got it. I will keep this to one executable step: one offer/post, one audience, one measurable 7-day target. Reply YES to proceed.",
            "cta": "Yes",
            "rationale": "Continue with a low-friction action-oriented next step.",
        }

    def _bump_auto_reply(self, conversation_id: str, message: str) -> int:
        key = f"{conversation_id}:{message[:80]}"
        current = self.store.auto_reply_counts.get(key, 0) + 1
        self.store.auto_reply_counts[key] = current
        return current
