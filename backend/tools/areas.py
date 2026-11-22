"""resolve_area: caller's words → a supported area_id, or a polite 'unsupported'."""

from __future__ import annotations

from rapidfuzz import fuzz, process

from backend.text import norm
from backend.tools.base import Args, Result, ToolContext, tool

# Words callers wrap around area names ("Jubilee Hills lo", "Gachibowli mein", "near …").
FILLERS = {
    "lo",
    "loni",
    "daggara",
    "pakkana",
    "mein",
    "me",
    "mai",
    "ke",
    "paas",
    "in",
    "at",
    "near",
    "area",
    "side",
    "the",
    "around",
    "hyderabad",
    "ki",
    "ka",
    "ko",
    "chudu",
    "chudandi",
    "dekho",
    "check",
}
MATCH_CUTOFF = 85


class ResolveAreaArgs(Args):
    text: str


def _clean(text: str) -> str:
    return " ".join(w for w in norm(text).split() if w not in FILLERS)


@tool("resolve_area", ResolveAreaArgs, "Map what the caller said to a supported demo area.")
async def resolve_area(ctx: ToolContext, args: ResolveAreaArgs) -> tuple[Result, str]:
    heard = _clean(args.text)
    supported = [a for a in ctx.catalog.areas if a.area_id in ctx.settings.demo_areas]

    # Exact alias inside the utterance first ("jubilee hills lo restaurant" → jubilee_hills).
    choices: dict[str, str] = {}
    for a in supported:
        for alias in [a.name_en, a.name_te, a.name_hi, *a.aliases]:
            key = norm(alias)
            choices[key] = a.area_id
            if key and (f" {key} " in f" {heard} "):
                return {"area_id": a.area_id, "name": a.name_en}, f"Area → {a.name_en}"

    # Known neighbouring areas are answered politely, never fuzzy-matched into a demo area.
    nearby = {norm(n): n for a in supported for n in a.nearby_unsupported_areas}
    for key, name in nearby.items():
        if f" {key} " in f" {heard} ":
            return _unsupported(ctx, name)

    # Fuzzy only on longer aliases: "jh" / "gb" would partially match too many words.
    fuzzy_keys = [k for k in choices if len(k) >= 4]
    best = process.extractOne(heard, fuzzy_keys, scorer=fuzz.WRatio, score_cutoff=MATCH_CUTOFF) if heard else None
    if best:
        area_id = choices[best[0]]
        name = next(a.name_en for a in supported if a.area_id == area_id)
        return {"area_id": area_id, "name": name}, f"Area → {name} (heard “{args.text}”)"
    return _unsupported(ctx, args.text.strip() or "that area")


def _unsupported(ctx: ToolContext, heard: str) -> tuple[Result, str]:
    supported = [a for a in ctx.catalog.areas if a.area_id in ctx.settings.demo_areas]
    reply = supported[0].unsupported_area_reply.model_dump() if supported else {}
    return (
        {"unsupported": True, "heard": heard, "supported": [a.area_id for a in supported], "reply": reply},
        f"Area “{heard}” not covered → offered {' / '.join(a.name_en for a in supported)}",
    )
