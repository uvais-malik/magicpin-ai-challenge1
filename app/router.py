"""HTTP route handlers and in-memory context store."""

from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any

from config.constants import BOT_VERSION, TEAM_NAME
from core.dispatcher import Dispatcher


class ContextStore:
    def __init__(self) -> None:
        self.started_at = time.time()
        self.categories: dict[str, dict] = {}
        self.merchants: dict[str, dict] = {}
        self.customers: dict[str, dict] = {}
        self.triggers: dict[str, dict] = {}
        self.versions: dict[tuple[str, str], int] = {}
        self.sent_suppression_keys: set[str] = set()
        self.conversations: dict[str, dict] = {}
        self._conversation_seq = 0

    def counts(self) -> dict[str, int]:
        return {
            "category": len(self.categories),
            "merchant": len(self.merchants),
            "customer": len(self.customers),
            "trigger": len(self.triggers),
        }

    def next_conversation_id(self, merchant_id: str, trigger_id: str) -> str:
        self._conversation_seq += 1
        return f"conv_{self._conversation_seq:04d}_{merchant_id}_{trigger_id}"


STORE = ContextStore()


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def handle_healthz() -> tuple[int, dict]:
    return 200, {
        "status": "ok",
        "uptime_seconds": int(time.time() - STORE.started_at),
        "contexts_loaded": STORE.counts(),
    }


def handle_metadata() -> tuple[int, dict]:
    return 200, {
        "team_name": TEAM_NAME,
        "team_members": ["Deterministic Vera Engine"],
        "model": "pure-python-rules",
        "approach": "multi-stage deterministic pipeline: analyze context, decide strategy, build HOOK-FACT-INSIGHT-ACTION copy",
        "contact_email": "team@example.com",
        "version": BOT_VERSION,
        "submitted_at": "2026-05-02T00:00:00Z",
    }


def handle_context(body: dict[str, Any]) -> tuple[int, dict]:
    scope = body.get("scope")
    context_id = body.get("context_id")
    version = body.get("version")
    payload = body.get("payload")

    if scope not in {"category", "merchant", "customer", "trigger"}:
        return 400, {"accepted": False, "reason": "invalid_scope", "details": str(scope)}
    if not context_id or not isinstance(payload, dict):
        return 400, {"accepted": False, "reason": "malformed", "details": "context_id and dict payload required"}
    try:
        version_int = int(version)
    except (TypeError, ValueError):
        return 400, {"accepted": False, "reason": "invalid_version", "details": "version must be integer"}

    current = STORE.versions.get((scope, context_id), 0)
    if version_int < current:
        return 409, {"accepted": False, "reason": "stale_version", "current_version": current}
    if version_int == current:
        return 200, {"accepted": True, "ack_id": f"ack_{scope}_{context_id}_{version_int}", "stored_at": _utc_now()}

    target = {
        "category": STORE.categories,
        "merchant": STORE.merchants,
        "customer": STORE.customers,
        "trigger": STORE.triggers,
    }[scope]
    target[context_id] = payload
    STORE.versions[(scope, context_id)] = version_int
    return 200, {"accepted": True, "ack_id": f"ack_{scope}_{context_id}_{version_int}", "stored_at": _utc_now()}


def handle_tick(body: dict[str, Any]) -> tuple[int, dict]:
    trigger_ids = body.get("available_triggers") or []
    now = body.get("now")
    actions = Dispatcher(STORE).actions_for_tick(trigger_ids, now)
    return 200, {"actions": actions}


AUTO_REPLY_MARKERS = (
    "thank you for contacting",
    "will respond shortly",
    "away from whatsapp",
    "business hours",
    "auto-reply",
    "automated",
)

HOSTILE_MARKERS = ("stop", "spam", "useless", "dont message", "don't message", "unsubscribe")
COMMITMENT_MARKERS = ("do it", "lets do", "let's do", "yes", "ok", "whats next", "what's next", "proceed", "confirm")


def handle_reply(body: dict[str, Any]) -> tuple[int, dict]:
    message = str(body.get("message", "")).strip()
    lowered = message.lower()

    if any(marker in lowered for marker in HOSTILE_MARKERS):
        return 200, {"action": "end", "rationale": "User asked to stop or called the message spam; end immediately."}

    if any(marker in lowered for marker in AUTO_REPLY_MARKERS):
        return 200, {"action": "end", "rationale": "Detected WhatsApp Business canned auto-reply; no further merchant turn should be spent."}

    if any(marker in lowered for marker in COMMITMENT_MARKERS):
        return 200, {
            "action": "send",
            "body": "Done - moving to execution. Here is the next step: I will draft the offer/post with price, audience, and 7-day run dates; reply CONFIRM and I will proceed.",
            "cta": "Confirm",
            "rationale": "Merchant committed, so switch from qualification to action mode.",
        }

    if "later" in lowered or "busy" in lowered:
        return 200, {"action": "wait", "wait_seconds": 1800, "rationale": "Merchant asked for time; back off for 30 minutes."}

    return 200, {
        "action": "send",
        "body": "Got it. I will keep this practical: one specific offer, one post, and one measurable target for the next 7 days. Reply YES to proceed.",
        "cta": "Yes",
        "rationale": "Continue with a low-friction action-oriented next step.",
    }

