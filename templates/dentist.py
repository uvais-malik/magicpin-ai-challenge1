"""Dentist-specific copy helpers."""

def opening(name: str) -> str:
    return f"Dr. {name}"


def clinical_action(offer_title: str) -> str:
    return f"Use {offer_title} as the low-friction patient action; avoid cure/guarantee claims."

