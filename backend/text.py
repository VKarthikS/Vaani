"""Text normalisation for matching romanised and native-script speech."""

from __future__ import annotations

import re

# ASCII punctuation + Devanagari danda + ellipsis. Unicode letters and combining vowel
# signs are kept, so Telugu/Hindi script survives (rapidfuzz's default_process strips them).
_PUNCT = re.compile(r"[!-/:-@\[-`{-~।॥…“”‘’]")
_SPACE = re.compile(r"\s+")


def norm(text: str) -> str:
    return _SPACE.sub(" ", _PUNCT.sub(" ", text.lower())).strip()


def mask_phone(phone: str | None) -> str | None:
    """'+919876543210' -> '+91••••••3210' for events, logs and API responses."""
    if not phone:
        return phone
    digits = phone.strip()
    if len(digits) <= 4:
        return "•" * len(digits)
    head = digits[:3] if digits.startswith("+") else ""
    return head + "•" * max(len(digits) - len(head) - 4, 1) + digits[-4:]
