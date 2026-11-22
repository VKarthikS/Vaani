"""Language of the caller's sentence: te / hi / en (Indian English).

Native script decides at once. Romanised code-mixed speech is scored on common function
words ("lo", "kavali", "andi" vs "mein", "chahiye", "hai"). Cheap, deterministic, and good
enough to pick prompts and the TTS voice; the agent can still switch with set_language.
"""

from __future__ import annotations

import re

from backend.text import norm

TELUGU = re.compile(r"[ఀ-౿]")
DEVANAGARI = re.compile(r"[ऀ-ॿ]")

TE_WORDS = {
    "lo",
    "kavali",
    "kaavali",
    "cheppu",
    "cheppandi",
    "andi",
    "undi",
    "unda",
    "ledu",
    "repu",
    "ellundi",
    "ivala",
    "nenu",
    "naaku",
    "naa",
    "meeru",
    "mee",
    "chudandi",
    "chudu",
    "cheyyandi",
    "cheyandi",
    "peru",
    "mandi",
    "ki",
    "manchi",
    "emi",
    "enti",
    "ekkada",
    "avunu",
    "sare",
    "kaadu",
    "garu",
    "noppi",
    "pillala",
    "chesko",
    "rojula",
    "tarvata",
    "podduna",
    "saayantram",
    "raatri",
    "gantaki",
    "baaga",
    "konchem",
    "mari",
    "inka",
}
HI_WORDS = {
    "mein",
    "chahiye",
    "hai",
    "hain",
    "kal",
    "parso",
    "aaj",
    "batao",
    "bataiye",
    "kya",
    "kitne",
    "baje",
    "log",
    "logon",
    "ke",
    "liye",
    "naam",
    "haan",
    "nahi",
    "theek",
    "achha",
    "accha",
    "karo",
    "kar",
    "do",
    "dijiye",
    "mujhe",
    "hum",
    "humein",
    "aap",
    "ji",
    "raat",
    "shaam",
    "subah",
    "wala",
    "wali",
    "dard",
    "bachchon",
    "kaunsa",
    "kahan",
    "dikhana",
    "milna",
    "chalega",
    "zaroor",
    "sakte",
}
EN_WORDS = {
    "the",
    "a",
    "an",
    "i",
    "need",
    "want",
    "please",
    "table",
    "for",
    "at",
    "tomorrow",
    "today",
    "book",
    "doctor",
    "people",
    "is",
    "are",
    "can",
    "you",
    "my",
    "name",
    "yes",
    "no",
    "evening",
    "morning",
    "night",
    "appointment",
}


def detect_language(text: str) -> tuple[str, float]:
    """Returns (lang, confidence 0-1)."""
    if TELUGU.search(text):
        return "te", 1.0
    if DEVANAGARI.search(text):
        return "hi", 1.0
    words = norm(text).split()
    if not words:
        return "en", 0.0
    te = sum(w in TE_WORDS for w in words)
    hi = sum(w in HI_WORDS for w in words)
    en = sum(w in EN_WORDS for w in words) * 0.6  # English words appear in every code-mix
    best = max(("te", te), ("hi", hi), ("en", en), key=lambda x: x[1])
    total = te + hi + en
    if best[1] == 0:
        return "en", 0.3
    return best[0], round(best[1] / total, 2)
