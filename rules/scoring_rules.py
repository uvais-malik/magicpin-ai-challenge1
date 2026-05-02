"""Severity scoring for merchant intervention priority."""

from __future__ import annotations


def clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


def severity_score(drop_pct: float, ctr_gap: float, inactivity_days: int) -> int:
    drop_component = clamp(max(0.0, drop_pct) * 100.0)
    ctr_component = clamp(max(0.0, ctr_gap) * 1000.0)
    inactivity_component = clamp(inactivity_days * 3.0)
    score = 0.45 * drop_component + 0.35 * ctr_component + 0.20 * inactivity_component
    return int(round(clamp(score)))

