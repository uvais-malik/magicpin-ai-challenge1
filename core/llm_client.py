"""Optional LLM rewrite hook with deterministic fallback.

The scoring-critical engine remains rule based. When LLM_COMPOSE=1 and a
provider key is present, this module asks an OpenAI-compatible chat endpoint to
rewrite only the outward copy while preserving facts and the response contract.
"""

from __future__ import annotations

import json
import os
from urllib import request as urlrequest


OPENAI_COMPATIBLE_URLS = {
    "groq": "https://api.groq.com/openai/v1/chat/completions",
    "openai": "https://api.openai.com/v1/chat/completions",
    "deepseek": "https://api.deepseek.com/v1/chat/completions",
    "openrouter": "https://openrouter.ai/api/v1/chat/completions",
}


def rewrite_message_if_enabled(message: dict, context: dict) -> dict:
    if os.environ.get("LLM_COMPOSE", "").lower() not in {"1", "true", "yes"}:
        return message
    provider = os.environ.get("LLM_PROVIDER", "groq").lower()
    api_key = os.environ.get("LLM_API_KEY", "")
    url = OPENAI_COMPATIBLE_URLS.get(provider)
    if not api_key or not url:
        return message

    model = os.environ.get("LLM_MODEL") or ("llama-3.3-70b-versatile" if provider == "groq" else "")
    if not model:
        return message

    system = (
        "Rewrite merchant engagement copy for the magicpin Vera challenge. "
        "Use only facts present in context or draft. Do not fabricate counts, dates, names, prices, or sources. "
        "Keep category voice, one compulsion lever, one CTA, and output strict JSON with body and cta only."
    )
    prompt = json.dumps({"context": context, "draft": {"body": message["body"], "cta": message["cta"]}}, ensure_ascii=True)
    body = json.dumps(
        {
            "model": model,
            "temperature": 0.2,
            "max_tokens": 500,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": prompt}],
        }
    ).encode("utf-8")
    try:
        req = urlrequest.Request(url, data=body, headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"})
        resp = urlrequest.urlopen(req, timeout=8)
        data = json.loads(resp.read().decode("utf-8"))
        content = data["choices"][0]["message"]["content"].strip()
        if content.startswith("```"):
            content = content.strip("`").replace("json\n", "", 1).strip()
        rewrite = json.loads(content)
    except Exception:
        return message

    body_text = str(rewrite.get("body", "")).strip()
    cta_text = str(rewrite.get("cta", "")).strip()
    if len(body_text) < 40 or not cta_text:
        return message

    updated = dict(message)
    updated["body"] = body_text
    updated["cta"] = cta_text
    return updated
