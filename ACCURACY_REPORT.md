# Accuracy Report And Optimization Notes

## Why The Previous Score Looked Low

The `30/50` local Gemini run mostly matched the simulator fallback pattern:

- specificity was `10/10`
- category fit, merchant fit, decision quality, and engagement were all fixed at `5/10`

That is the fallback scorer shape in `judge_simulator.py`, not a nuanced LLM judgment. The simulator fell back when it could not parse or receive valid scoring output, and later Gemini also returned `HTTP 429` rate-limit errors. So the reported score was useful as a smoke test, but not a reliable accuracy read.

## Real Bot Accuracy Problems Found

1. Missing trigger taxonomy

   Several trigger kinds were not classified: `supply_alert`, `category_seasonal`, `gbp_unverified`, `cde_opportunity`, and `chronic_refill_due`. These fell into generic messages, reducing trigger relevance and category fit.

2. Wrong strategy priority

   `perf_dip` with high urgency was being labelled as `URGENCY` instead of `LOSS_AVERSION`. The message body was still decent, but the rationale and strategy were less accurate.

3. Planning intent branch was unreachable

   `active_planning_intent` was classified as opportunity, then consumed by the broad opportunity branch before the dedicated planning message could run.

4. Generic wording hurt category fit

   Pharmacy alerts could become "timed demand window" copy, which is wrong for medical inventory and batch recall scenarios.

5. Machine labels leaked into merchant copy

   Examples: `delivery_late`, `corporate_bulk_thali_package`, `postcard_or_phone_call`, `free_for_members`.

6. CTR insight was sometimes inaccurate

   For seasonal gym dips with CTR above peer, the engine still said the peer CTR gap was the problem. This is now corrected to identify demand volume as the issue.

## Optimizations Made

- Added missing trigger classifications and CTA mappings.
- Reordered strategy selection so performance loss and planning intent win over generic urgency/opportunity.
- Added dedicated message branches for:
  - stock/batch supply alerts
  - seasonal pharmacy demand shifts
  - Google profile verification
  - CDE opportunities
  - competitor openings
  - review themes
  - active planning intent
- Humanized payload labels before inserting them into merchant copy.
- Added CTR-aware insight text so the engine does not claim a CTR gap when CTR is above peer.
- Improved trigger-specific action recommendations for pharmacy, dentist, restaurant, gym, and salon scenarios.

## Remaining Risk

The bundled simulator is useful but brittle with Gemini: it can hit model availability issues, console encoding issues, parsing fallback, and rate limits. The bot output should be evaluated after Gemini quota cools down, ideally with `PYTHONIOENCODING=utf-8` and an available Gemini model such as `gemini-2.5-flash`.

