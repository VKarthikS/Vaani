"""Validate the 9 data files in data/ (or another folder).

    uv run python scripts/validate_data.py            # data/
    uv run python scripts/validate_data.py path/to/dir

Exit code 0 = valid (warnings allowed), 1 = errors. Rules: backend/catalog/validate.py.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.catalog.loader import DATA_DIR, CatalogLoadError, load_catalog  # noqa: E402
from backend.catalog.validate import validate_catalog  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("data_dir", nargs="?", type=Path, default=DATA_DIR)
    ap.add_argument("--strict", action="store_true", help="treat warnings as errors")
    args = ap.parse_args(argv)

    try:
        cat = load_catalog(args.data_dir)
    except CatalogLoadError as e:
        print(f"✗ {len(e.problems)} problem(s) loading {args.data_dir}:")
        for p in e.problems:
            print(f"  - {p}")
        return 1

    report = validate_catalog(cat)
    for w in report.warnings:
        print(f"  ! {w}")
    for err in report.errors:
        print(f"  ✗ {err}")

    summary = (
        f"{len(cat.areas)} areas, {len(cat.restaurants)} restaurants, {len(cat.hospitals)} hospitals, "
        f"{len(cat.doctors)} doctors, {len(cat.restaurant_availability)} + {len(cat.doctor_availability)} "
        f"availability rows, {len(cat.speciality_mapping.phrases)} phrases, "
        f"{len(cat.speciality_mapping.emergency_phrases)} emergency phrases, {len(cat.test_calls)} test calls, "
        f"{len(cat.agent_phrases)} agent phrase keys"
    )
    failed = bool(report.errors) or (args.strict and bool(report.warnings))
    if failed:
        print(f"✗ INVALID — {len(report.errors)} error(s), {len(report.warnings)} warning(s)\n  {summary}")
        return 1
    print(f"✓ data OK — {len(report.warnings)} warning(s)\n  {summary}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
