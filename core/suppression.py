"""Suppression key generation and in-memory dedup helpers."""

from __future__ import annotations

from config.constants import TIME_BUCKET_FALLBACK
from utils.formatter import iso_week


def make_suppression_key(merchant: dict, trigger: dict, now: str | None = None) -> str:
    if trigger.get("suppression_key"):
        return trigger["suppression_key"]
    merchant_id = merchant.get("merchant_id") or trigger.get("merchant_id") or "merchant_unknown"
    trigger_id = trigger.get("id") or trigger.get("trigger_id") or trigger.get("kind", "trigger_unknown")
    bucket = iso_week(now or trigger.get("expires_at")) or TIME_BUCKET_FALLBACK
    return f"{merchant_id}:{trigger_id}:{bucket}"

