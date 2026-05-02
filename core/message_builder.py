"""Build WhatsApp bodies using HOOK -> FACT -> INSIGHT -> ACTION."""

from __future__ import annotations

from config.constants import (
    STRATEGY_CURIOSITY,
    STRATEGY_LOSS_AVERSION,
    STRATEGY_OPPORTUNITY,
    STRATEGY_REACTIVATION,
    STRATEGY_URGENCY,
)
from intelligence.category_adapter import find_digest_item, select_offer
from utils.formatter import clean_text, ctr, humanize_label, money, pct


def _merchant_name(merchant: dict) -> str:
    identity = merchant.get("identity", {})
    return identity.get("owner_first_name") or identity.get("name", "there").split()[0]


def _salutation(category_profile: dict, merchant: dict, customer_profile: dict) -> str:
    if customer_profile.get("present"):
        return f"Hi {customer_profile.get('name', 'there')}"
    name = _merchant_name(merchant)
    if category_profile["slug"] == "dentists":
        return f"Dr. {name}"
    return f"Hi {name}"


def _location(merchant: dict) -> str:
    identity = merchant.get("identity", {})
    loc = ", ".join(x for x in [identity.get("locality"), identity.get("city")] if x)
    return loc or "your area"


def _base_metrics(merchant: dict, category_profile: dict) -> str:
    perf = merchant.get("performance", {})
    peer = category_profile.get("peer_stats", {})
    return (
        f"Your 30d numbers are {perf.get('views', 0)} views, {perf.get('calls', 0)} calls, "
        f"CTR {ctr(perf.get('ctr'))}; peer CTR is {ctr(peer.get('avg_ctr'))}."
    )


def _metric_phrase(metric: str, value: object, direction: str) -> str:
    verb = {"up": "rose", "down": "dropped"}.get(direction, "changed")
    return f"{metric.replace('_', ' ')} {verb} {pct(value, signed=(direction == 'up'))}"


def _format_list(values: list[object], limit: int = 3) -> str:
    cleaned = [humanize_label(v) for v in values[:limit]]
    return ", ".join(v for v in cleaned if v)


def _ctr_gap_insight(merchant_analysis: dict) -> str:
    if merchant_analysis["ctr_gap"] > 0:
        return f"peer CTR is higher by {merchant_analysis['ctr_gap'] * 100:.1f} points"
    return f"CTR is already above peer ({ctr(merchant_analysis['ctr'])} vs {ctr(merchant_analysis['peer_ctr'])}), so the issue is demand volume"


def build_message(category_profile: dict, merchant: dict, trigger: dict, customer_profile: dict, merchant_analysis: dict, trigger_analysis: dict, decision: dict) -> str:
    greeting = _salutation(category_profile, merchant, customer_profile)
    payload = trigger_analysis["payload"]
    offer = select_offer(category_profile, merchant, trigger)
    offer_title = clean_text(offer.get("title", "starter offer"))
    kind = trigger_analysis["kind"]
    angle = decision["angle"]

    if customer_profile.get("present"):
        return _build_customer_message(greeting, merchant, trigger_analysis, customer_profile, offer_title)

    if kind in {"research_digest", "category_research_digest_release"}:
        item = find_digest_item(category_profile, trigger)
        title = clean_text(item.get("title", "new category research"))
        source = clean_text(item.get("source", "category digest"))
        trial = item.get("trial_n") or payload.get("trial_n") or "1"
        actionable = clean_text(item.get("actionable", "turn it into one customer-facing post"))
        return (
            f"{greeting}, {source}: {title}. "
            f"Fact: sample size {trial}; your clinic has {merchant.get('customer_aggregate', {}).get('high_risk_adult_count', merchant.get('customer_aggregate', {}).get('total_unique_ytd', 0))} relevant patients and CTR {ctr(merchant_analysis['ctr'])} vs peer {ctr(merchant_analysis['peer_ctr'])}. "
            f"Insight: this is useful because your signals include {clean_text(', '.join(merchant_analysis['signals'][:2]))}. "
            f"Action: {actionable}."
        )

    if kind == "regulation_change":
        item = find_digest_item(category_profile, trigger)
        deadline = payload.get("deadline_iso", "the deadline")
        return (
            f"{greeting}, compliance window: {clean_text(item.get('title', 'new rule'))}. "
            f"Fact: deadline {deadline}; {clean_text(item.get('summary', 'audit needed'))}. "
            f"Insight: your {merchant.get('identity', {}).get('locality', 'local')} patients will trust a clinic that documents this before the date. "
            f"Action: prepare a 3-point SOP checklist today."
        )

    if kind == "supply_alert":
        molecule = clean_text(payload.get("molecule", "affected medicine"))
        batches = _format_list(payload.get("affected_batches", []))
        manufacturer = clean_text(payload.get("manufacturer", "the manufacturer"))
        return (
            f"{greeting}, stock safety alert: {molecule} batches need checking today. "
            f"Fact: affected batches are {batches or 'listed in the alert'} from {manufacturer}; urgency is {trigger_analysis['urgency']}/5. "
            f"Insight: a precise batch pull protects repeat-Rx trust without making broad medical claims. "
            f"Action: pull these batches and message affected chronic customers from your repeat list."
        )

    if kind == "category_seasonal":
        trends = payload.get("trends", [])
        trend_text = _format_list(trends, 4)
        return (
            f"{greeting}, summer shelf demand has shifted in your category. "
            f"Fact: {trend_text}; {_base_metrics(merchant, category_profile)} "
            f"Insight: shelf visibility matters more than discounts when demand is already seasonal. "
            f"Action: move ORS, sunscreen, and anti-fungal items to counter visibility this week."
        )

    if kind == "gbp_unverified":
        uplift = payload.get("estimated_uplift_pct", 0)
        path = humanize_label(payload.get("verification_path", "verification"))
        return (
            f"{greeting}, your Google profile is still unverified. "
            f"Fact: the available path is {path}; expected visibility uplift is {pct(uplift)}. "
            f"Insight: unverified profiles lose trust before customers even compare price. "
            f"Action: complete verification and add one service post after approval."
        )

    if kind == "cde_opportunity":
        item = find_digest_item(category_profile, {"payload": {"top_item_id": payload.get("digest_item_id")}})
        return (
            f"{greeting}, CDE opportunity today: {clean_text(item.get('title', 'professional update'))}. "
            f"Fact: {payload.get('credits', 0)} credits, fee {humanize_label(payload.get('fee', 'listed by organizer'))}; source {clean_text(item.get('source', 'category calendar'))}. "
            f"Insight: this is a low-friction authority signal you can also turn into a patient education post. "
            f"Action: save the event details and draft one 2-line patient-facing takeaway."
        )

    if kind == "competitor_opened":
        competitor = clean_text(payload.get("competitor_name", "a competitor"))
        their_offer = clean_text(payload.get("their_offer", "a visible offer"))
        distance = payload.get("distance_km", "?")
        opened = payload.get("opened_date", "recently")
        return (
            f"{greeting}, new competitor signal: {competitor} opened {distance} km away on {opened}. "
            f"Fact: their visible offer is {their_offer}; your CTR is {ctr(merchant_analysis['ctr'])} vs peer {ctr(merchant_analysis['peer_ctr'])}. "
            f"Insight: do not undercut blindly; answer with trust plus a comparable entry service. "
            f"Action: post {offer_title} with your review/profile strength today."
        )

    if kind == "review_theme_emerged":
        theme = humanize_label(payload.get("theme", "review issue"))
        count = payload.get("occurrences_30d", 0)
        quote = clean_text(payload.get("common_quote", ""))
        return (
            f"{greeting}, {count} reviews in 30d now mention {theme}. "
            f"Fact: one line says '{quote}' and your CTR is {ctr(merchant_analysis['ctr'])} vs peer {ctr(merchant_analysis['peer_ctr'])}. "
            f"Insight: fixing the visible complaint can recover trust before offers are needed. "
            f"Action: publish a short response and adjust the next post around the fix."
        )

    if kind == "active_planning_intent":
        topic = humanize_label(payload.get("intent_topic", "campaign plan"))
        last = clean_text(payload.get("merchant_last_message", "merchant asked to proceed"))
        return (
            f"{greeting}, picking up your plan on {topic}. "
            f"Fact: you said '{last}'; {_base_metrics(merchant, category_profile)} "
            f"Insight: the next reply should move to execution, not more questions. "
            f"Action: draft {offer_title} with price, audience, and 7-day run dates."
        )

    if kind in {"perf_dip", "seasonal_perf_dip"}:
        metric = payload.get("metric") or merchant_analysis["drop_metric"]
        delta = payload.get("delta_pct", -merchant_analysis["drop_pct"])
        baseline = payload.get("vs_baseline")
        baseline_text = f" vs baseline {baseline}" if baseline is not None else ""
        return (
            f"{greeting}, your {metric} dropped {pct(abs(float(delta)) if isinstance(delta, (int, float)) else merchant_analysis['drop_pct'])} this {payload.get('window', '7d')}{baseline_text}. "
            f"Fact: {_base_metrics(merchant, category_profile)} "
            f"Insight: {_ctr_gap_insight(merchant_analysis)}. "
            f"Action: activate {offer_title} for {_location(merchant)} and post it once."
        )

    if angle == STRATEGY_LOSS_AVERSION:
        return (
            f"{greeting}, one loss-risk signal needs action today. "
            f"Fact: {_base_metrics(merchant, category_profile)} Signals: {clean_text(', '.join(merchant_analysis['signals'][:3]))}. "
            f"Insight: the fastest fix is a concrete trust or offer update tied to the exact issue. "
            f"Action: publish {offer_title} with one proof point for {_location(merchant)}."
        )

    if kind in {"perf_spike", "milestone_reached"}:
        metric = payload.get("metric") or merchant_analysis["spike_metric"]
        delta_text = pct(payload.get("delta_pct", merchant_analysis["spike_pct"]), signed=True)
        value = payload.get("value_now")
        value_text = f"; current value {value}" if value is not None else ""
        return (
            f"{greeting}, momentum is live: {_metric_phrase(metric, payload.get('delta_pct', merchant_analysis['spike_pct']), 'up')}{value_text}. "
            f"Fact: {_base_metrics(merchant, category_profile)} "
            f"Insight: when demand is already warm, a specific price/service gets more replies than a generic discount. "
            f"Action: boost {offer_title} for the next 48 hours."
        )

    if kind == "renewal_due":
        days = payload.get("days_remaining", 0)
        amount = payload.get("renewal_amount")
        amount_text = f" at {money(amount)}" if amount else ""
        return (
            f"{greeting}, your {payload.get('plan', 'plan')} renewal is due in {days} days{amount_text}. "
            f"Fact: {_base_metrics(merchant, category_profile)} "
            f"Insight: renew only with a recovery plan attached, because your live gap is CTR {ctr(merchant_analysis['ctr'])} vs peer {ctr(merchant_analysis['peer_ctr'])}. "
            f"Action: renew and restart {offer_title} as the first 7-day campaign."
        )

    if kind in {"winback_eligible", "dormant_with_vera"} or angle == STRATEGY_REACTIVATION:
        days = payload.get("days_remaining") or payload.get("days_since_expiry") or merchant_analysis.get("inactivity_days") or 0
        amount = payload.get("renewal_amount")
        amount_text = f" at {money(amount)}" if amount else ""
        return (
            f"{greeting}, this is a reactivation moment: {days} days is the key number{amount_text}. "
            f"Fact: {_base_metrics(merchant, category_profile)} "
            f"Insight: restarting with one concrete service beats a broad profile reminder. "
            f"Action: restart {offer_title} and message the lapsed customer list once."
        )

    if kind in {"festival_upcoming", "ipl_match_today"} or angle == STRATEGY_URGENCY:
        event = payload.get("festival") or payload.get("match") or clean_text(kind.replace("_", " "))
        days = payload.get("days_until")
        when = f" in {days} days" if days is not None else ""
        venue = payload.get("venue")
        venue_text = f" near {venue}" if venue else ""
        return (
            f"{greeting}, {event}{when}{venue_text} is a timed demand window. "
            f"Fact: {_base_metrics(merchant, category_profile)} "
            f"Insight: urgency works only if the offer names the occasion and price. "
            f"Action: run {offer_title} today for {_location(merchant)}."
        )

    if angle == STRATEGY_OPPORTUNITY:
        return (
            f"{greeting}, there is an opportunity signal worth using now. "
            f"Fact: {_base_metrics(merchant, category_profile)} Trigger data: {clean_text(payload)}. "
            f"Insight: a named service and price converts better than a broad 'offer available' post. "
            f"Action: draft {offer_title} for a 7-day run in {_location(merchant)}."
        )

    if angle == STRATEGY_CURIOSITY:
        trend = (category_profile.get("trend_signals") or [{}])[0]
        query = clean_text(trend.get("query", category_profile["display_name"]))
        yoy = trend.get("delta_yoy", 0)
        return (
            f"{greeting}, quick curiosity signal: '{query}' is up {pct(yoy, signed=True)} YoY. "
            f"Fact: {_base_metrics(merchant, category_profile)} "
            f"Insight: this topic is reply-worthy because it connects demand to your current offer shelf. "
            f"Action: turn it into a 2-line post featuring {offer_title}."
        )

    return (
        f"{greeting}, one specific signal needs action today. "
        f"Fact: {_base_metrics(merchant, category_profile)} "
        f"Insight: your best next step is a concrete service-price message. "
        f"Action: publish {offer_title} for {_location(merchant)}."
    )


def _build_customer_message(greeting: str, merchant: dict, trigger_analysis: dict, customer_profile: dict, offer_title: str) -> str:
    merchant_name = clean_text(merchant.get("identity", {}).get("name", "your clinic"))
    payload = trigger_analysis["payload"]
    facts = ", ".join(customer_profile.get("relationship_facts") or ["your previous visit is on record"])
    if not customer_profile.get("consent"):
        return (
            f"{greeting}, {merchant_name} has your previous visit noted but no active outreach consent. "
            f"Fact: {facts}. Insight: no promotional message will be sent without opt-in. Action: reply START only if you want reminders."
        )
    if trigger_analysis["type"] == "recall":
        service = clean_text(payload.get("service_due", "follow-up visit").replace("_", " "))
        due = payload.get("due_date") or payload.get("last_service_date") or "this month"
        slots = payload.get("available_slots") or payload.get("next_session_options") or []
        slot = clean_text(slots[0].get("label")) if slots else "this week"
        return (
            f"{greeting}, reminder from {merchant_name}: {service} is due around {due}. "
            f"Fact: {facts}; first open slot is {slot}. "
            f"Insight: booking before the due window keeps the visit short and predictable. "
            f"Action: reserve {slot}."
        )
    return (
        f"{greeting}, {merchant_name} is following up from your last interaction. "
        f"Fact: {facts}. Insight: {offer_title} is the simplest next step. "
        f"Action: reply with a preferred evening/weekend slot."
    )
