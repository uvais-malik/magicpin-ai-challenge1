"""Sample compose call using the bundled seed data."""

from __future__ import annotations

import json
from pathlib import Path

from core.composer import compose


ROOT = Path(__file__).parent


def load_json(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


if __name__ == "__main__":
    category = load_json("dataset/categories/dentists.json")
    merchant = load_json("dataset/merchants_seed.json")["merchants"][1]
    trigger = load_json("dataset/triggers_seed.json")["triggers"][3]
    print(json.dumps(compose(category, merchant, trigger), indent=2, ensure_ascii=True))
