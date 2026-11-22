"""Loads the 9 JSON files in data/ into a typed Catalog."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import TypeAdapter, ValidationError

from backend.catalog.models import (
    AgentPhrase,
    Area,
    Catalog,
    Doctor,
    DoctorSlotException,
    Hospital,
    Restaurant,
    RestaurantSlotException,
    SpecialityMapping,
    TestCall,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = REPO_ROOT / "data"

# file stem -> type of its top-level JSON value
FILES: dict[str, Any] = {
    "areas": list[Area],
    "restaurants": list[Restaurant],
    "restaurant_availability": list[RestaurantSlotException],
    "hospitals": list[Hospital],
    "doctors": list[Doctor],
    "doctor_availability": list[DoctorSlotException],
    "speciality_mapping": SpecialityMapping,
    "test_calls": list[TestCall],
    "agent_phrases": list[AgentPhrase],
}


class CatalogLoadError(Exception):
    """Raised with one readable line per problem (missing file, bad JSON, wrong shape)."""

    def __init__(self, problems: list[str]) -> None:
        super().__init__("\n".join(problems))
        self.problems = problems


def _format_validation_error(file: str, err: ValidationError, raw: Any) -> list[str]:
    lines = []
    for e in err.errors():
        loc = list(e["loc"])
        # Point at the record's ID when the error is inside a list item.
        where = ".".join(str(p) for p in loc)
        if isinstance(raw, list) and loc and isinstance(loc[0], int) and loc[0] < len(raw):
            item = raw[loc[0]]
            if isinstance(item, dict):
                ident = next((item[k] for k in item if k.endswith("_id") or k == "key"), None)
                if ident:
                    where = f"[{ident}]." + ".".join(str(p) for p in loc[1:])
        lines.append(f"{file}.json {where}: {e['msg']}")
    return lines


def load_raw(data_dir: Path = DATA_DIR) -> dict[str, Any]:
    raw: dict[str, Any] = {}
    problems: list[str] = []
    for stem in FILES:
        path = data_dir / f"{stem}.json"
        if not path.exists():
            problems.append(f"{stem}.json: file missing")
            continue
        try:
            raw[stem] = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            problems.append(f"{stem}.json: invalid JSON at line {e.lineno} col {e.colno}: {e.msg}")
    if problems:
        raise CatalogLoadError(problems)
    return raw


def parse_catalog(raw: dict[str, Any]) -> Catalog:
    parsed: dict[str, Any] = {}
    problems: list[str] = []
    for stem, typ in FILES.items():
        try:
            parsed[stem] = TypeAdapter(typ).validate_python(raw[stem])
        except ValidationError as e:
            problems.extend(_format_validation_error(stem, e, raw[stem]))
    if problems:
        raise CatalogLoadError(problems)
    return Catalog(**parsed)


def load_catalog(data_dir: Path = DATA_DIR) -> Catalog:
    return parse_catalog(load_raw(data_dir))
