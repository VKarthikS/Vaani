"""Regenerate supabase/seed.sql from data/*.json.

    uv run python scripts/make_seed_sql.py           # write supabase/seed.sql
    uv run python scripts/make_seed_sql.py --check   # exit 1 if seed.sql is out of date

The file uses dates relative to public.vaani_today(), so it stays valid on any day;
only re-run this when data/ changes. Validation runs first and blocks bad data.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.catalog.loader import DATA_DIR, CatalogLoadError, load_catalog  # noqa: E402
from backend.catalog.seeding import build_seed_sql  # noqa: E402
from backend.catalog.validate import validate_catalog  # noqa: E402
from backend.db import SUPABASE_DIR  # noqa: E402

SEED_SQL = SUPABASE_DIR / "seed.sql"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data-dir", type=Path, default=DATA_DIR)
    ap.add_argument("--out", type=Path, default=SEED_SQL)
    ap.add_argument("--check", action="store_true", help="only check that the file is up to date")
    args = ap.parse_args(argv)

    try:
        cat = load_catalog(args.data_dir)
    except CatalogLoadError as e:
        print("✗ cannot load data — run scripts/validate_data.py\n  " + "\n  ".join(e.problems))
        return 1
    report = validate_catalog(cat)
    if not report.ok:
        print(f"✗ data has {len(report.errors)} error(s) — run scripts/validate_data.py")
        return 1

    sql = build_seed_sql(cat)
    if args.check:
        current = args.out.read_text(encoding="utf-8") if args.out.exists() else ""
        if current != sql:
            print(f"✗ {args.out} is out of date — run scripts/make_seed_sql.py")
            return 1
        print(f"✓ {args.out} is up to date")
        return 0

    args.out.write_text(sql, encoding="utf-8")
    print(f"✓ wrote {args.out} ({len(sql.splitlines())} lines)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
