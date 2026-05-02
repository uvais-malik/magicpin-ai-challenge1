# Vera by magicpin - Deterministic AI Decision Engine

This project implements the required deterministic contract:

```python
compose(category, merchant, trigger, customer=None) -> dict
```

It also exposes the challenge HTTP API:

- `POST /v1/context`
- `POST /v1/tick`
- `POST /v1/reply`
- `GET /v1/healthz`
- `GET /v1/metadata`

## Run

```bash
python bot.py
```

The server listens on `http://localhost:8080`.

Cloud hosts such as Render or Railway can provide the runtime port through
`PORT`; `bot.py` handles that automatically.

## Architecture

The code follows the requested multi-stage pipeline:

1. `intelligence/*` analyzes category, merchant, trigger, and customer context.
2. `core/decision_engine.py` selects a deterministic strategy.
3. `core/message_builder.py` builds HOOK -> FACT -> INSIGHT -> ACTION copy.
4. `core/cta_engine.py`, `core/suppression.py`, and `core/rationale_engine.py` complete the response contract.
5. `app/router.py` stores pushed context and dispatches proactive actions.

## Local Checks

```bash
python sample_run.py
python -m unittest discover -s tests
python -m compileall app core intelligence templates rules utils config bot.py
```

`scoring_simulation.py` contains a small heuristic helper. The official score should still be measured with `judge_simulator.py`.

To run `judge_simulator.py`, keep keys out of source code and set environment variables instead. See `.env.example` and `GITHUB_UPLOAD_GUIDE.md`.
