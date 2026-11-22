"""Load data/*.json into the database (wipes and reloads catalogue, slots, bookings, calls).

    uv run python scripts/seed.py            # validate, then seed SUPABASE_DB_URL
    uv run python scripts/seed.py --dry-run  # validate + show what would be created today

day_offset 0-6 becomes real dates relative to today in IST, so re-run it on the demo
morning to get fresh slots. Uses the same SQL as supabase/seed.sql.
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from psycopg import sql

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.catalog.loader import DATA_DIR, CatalogLoadError, load_catalog  # noqa: E402
from backend.catalog.seeding import build_seed_sql, preview  # noqa: E402
from backend.catalog.validate import validate_catalog  # noqa: E402
from backend.db import connect, run_sql  # noqa: E402

IST = ZoneInfo("Asia/Kolkata")
COUNT_TABLES = (
    "areas",
    "restaurants",
    "restaurant_tables",
    "restaurant_slots",
    "hospitals",
    "doctors",
    "doctor_slots",
    "speciality_map",
    "bookings",
)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data-dir", type=Path, default=DATA_DIR)
    ap.add_argument("--db-url", help="Postgres URL (default: SUPABASE_DB_URL from .env)")
    ap.add_argument("--dry-run", action="store_true")
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

    today = datetime.now(IST).date()
    pv = preview(cat, today)
    print(
        f"Seeding for {today.isoformat()} (IST) → {pv.restaurant_slots} restaurant slots, "
        f"{pv.doctor_slots} doctor slots over 7 days"
    )
    for s in pv.skipped:
        print(f"  ! skipped exception: {s}")
    if args.dry_run:
        print("✓ dry run — nothing written")
        return 0

    with connect(args.db_url) as conn:
        run_sql(conn, build_seed_sql(cat))
        counts = {}
        for t in COUNT_TABLES:
            row = conn.execute(sql.SQL("select count(*) from {}").format(sql.Identifier("public", t))).fetchone()
            counts[t] = row[0] if row else 0
    print("✓ seeded: " + ", ".join(f"{t}={n}" for t, n in counts.items()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
