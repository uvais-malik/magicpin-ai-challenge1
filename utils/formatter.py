"""Formatting helpers that keep copy deterministic and concise."""

from __future__ import annotations

from datetime import datetime
from typing import Any


def as_number(value: Any, default: str = "0") -> str:
    if value is None:
        return default
    if isinstance(value, float):
        if abs(value) < 1:
            return f"{value:.1%}"
        if value.is_integer():
            return str(int(value))
        return f"{value:.1f}"
    return str(value)


def pct(value: Any, signed: bool = False) -> str:
    if value is None:
        return "0%"
    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value)
    sign = "+" if signed and number > 0 else ""
    return f"{sign}{number * 100:.0f}%"


def ctr(value: Any) -> str:
    if value is None:
        return "0.0%"
    try:
        return f"{float(value) * 100:.1f}%"
    except (TypeError, ValueError):
        return str(value)


def money(value: Any) -> str:
    if value is None:
        return "Rs 0"
    text = str(value).replace("\u20b9", "Rs ").replace("\u00e2\u201a\u00b9", "Rs ")
    if text.lower().startswith("rs"):
        return text
    return f"Rs {text}"


def clean_text(value: Any) -> str:
    text = "" if value is None else str(value)
    return (
        text.replace("\u2014", "-")
        .replace("\u2013", "-")
        .replace("\u20b9", "Rs ")
        .replace("\u00e2\u201a\u00b9", "Rs ")
        .replace("\u2192", "->")
        .replace("\n", " ")
        .strip()
    )


def humanize_label(value: Any) -> str:
    return clean_text(value).replace("_", " ").strip()


def first_name(identity: dict) -> str:
    return identity.get("owner_first_name") or identity.get("name", "there").split()[0].strip(",")


def iso_week(value: str | None) -> str:
    if not value:
        return "current"
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        week = parsed.isocalendar()
        return f"{week.year}-W{week.week:02d}"
    except ValueError:
        return value[:10] if len(value) >= 10 else "current"


def compact_sentence(parts: list[str]) -> str:
    return " ".join(clean_text(p) for p in parts if p and clean_text(p))
