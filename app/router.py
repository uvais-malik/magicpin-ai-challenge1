"""HTTP route handlers and in-memory context store."""

from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any

from config.constants import BOT_VERSION, TEAM_NAME
from core.conversation_handlers import ConversationHandler
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
        self.auto_reply_counts: dict[str, int] = {}
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
        short_merchant = str(merchant_id).replace("m_", "")[:24]
        short_trigger = str(trigger_id).replace("trg_", "")[:32]
        return f"conv_{short_merchant}_{short_trigger}_{self._conversation_seq:04d}"

    def clear_trigger_suppression(self, context_id: str, payload: dict) -> None:
        explicit = payload.get("suppression_key")
        if explicit:
            self.sent_suppression_keys.discard(explicit)
        merchant_id = payload.get("merchant_id", "")
        possible = [
            key
            for key in self.sent_suppression_keys
            if context_id in key or (merchant_id and key.startswith(f"{merchant_id}:"))
        ]
        for key in possible:
            self.sent_suppression_keys.discard(key)


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
    target = {
        "category": STORE.categories,
        "merchant": STORE.merchants,
        "customer": STORE.customers,
        "trigger": STORE.triggers,
    }[scope]

    if version_int == current:
        target[context_id] = payload
        if scope == "trigger":
            STORE.clear_trigger_suppression(context_id, payload)
        return 200, {"accepted": True, "ack_id": f"ack_{scope}_{context_id}_{version_int}", "stored_at": _utc_now()}

    target[context_id] = payload
    STORE.versions[(scope, context_id)] = version_int
    if scope == "trigger":
        STORE.clear_trigger_suppression(context_id, payload)
    return 200, {"accepted": True, "ack_id": f"ack_{scope}_{context_id}_{version_int}", "stored_at": _utc_now()}


def handle_tick(body: dict[str, Any]) -> tuple[int, dict]:
    trigger_ids = body.get("available_triggers") or []
    now = body.get("now")
    actions = Dispatcher(STORE).actions_for_tick(trigger_ids, now)
    return 200, {"actions": actions}


def handle_reply(body: dict[str, Any]) -> tuple[int, dict]:
    return ConversationHandler(STORE).handle(body)
