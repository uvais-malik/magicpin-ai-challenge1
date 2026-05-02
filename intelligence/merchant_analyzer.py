"""Merchant-specific performance and signal analysis."""

from __future__ import annotations

import re

from rules.scoring_rules import severity_score


def _extract_days(signal: str, suffix: str) -> int:
    match = re.search(rf"{re.escape(suffix)}:?(\d+)d", signal)
    return int(match.group(1)) if match else 0


def analyze_merchant(merchant: dict | None, category_profile: dict) -> dict:
    merchant = merchant or {}
    performance = merchant.get("performance", {})
    delta = performance.get("delta_7d", {})
    peer = category_profile.get("peer_stats", {})
    signals = list(merchant.get("signals", []))

    deltas = {
        "views": float(delta.get("views_pct") or 0),
        "calls": float(delta.get("calls_pct") or 0),
        "ctr": float(delta.get("ctr_pct") or 0),
    }
    worst_metric, worst_delta = min(deltas.items(), key=lambda item: item[1])
    best_metric, best_delta = max(deltas.items(), key=lambda item: item[1])

    drop_pct = abs(worst_delta) if worst_delta < 0 else 0.0
    spike_pct = best_delta if best_delta > 0 else 0.0
    ctr_value = float(performance.get("ctr") or 0)
    peer_ctr = float(peer.get("avg_ctr") or 0)
    ctr_gap = max(0.0, peer_ctr - ctr_value)

    inactivity_days = 0
    stale_days = 0
    for signal in signals:
        if signal.startswith("dormant_with_vera"):
            inactivity_days = max(inactivity_days, _extract_days(signal, "dormant_with_vera_"))
        if signal.startswith("stale_posts"):
            stale_days = max(stale_days, _extract_days(signal, "stale_posts"))

    derived = []
    if drop_pct >= 0.20:
        derived.append(f"{worst_metric}_drop_{int(drop_pct * 100)}pct")
    if spike_pct >= 0.15:
        derived.append(f"{best_metric}_spike_{int(spike_pct * 100)}pct")
    if ctr_gap > 0:
        derived.append(f"ctr_gap_{(ctr_gap * 100):.1f}pp")
    if stale_days:
        derived.append(f"stale_activity_{stale_days}d")
    if inactivity_days:
        derived.append(f"inactive_{inactivity_days}d")
    if not [o for o in merchant.get("offers", []) if o.get("status") == "active"]:
        derived.append("no_active_offer")

    severity = severity_score(drop_pct, ctr_gap, max(inactivity_days, stale_days))
    return {
        "drop_pct": drop_pct,
        "drop_metric": worst_metric,
        "spike_pct": spike_pct,
        "spike_metric": best_metric,
        "ctr": ctr_value,
        "peer_ctr": peer_ctr,
        "ctr_gap": ctr_gap,
        "inactivity_days": inactivity_days,
        "stale_days": stale_days,
        "performance_dip": drop_pct >= 0.15 or any("perf_dip" in s for s in signals),
        "performance_spike": spike_pct >= 0.15 or any("spike" in s for s in signals),
        "ctr_below_peer": ctr_gap > 0,
        "signals": signals + derived,
        "severity": severity,
    }

